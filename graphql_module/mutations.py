import graphene
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from database.db import conn

bcrypt = Bcrypt()

class SignUp(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        
    status = graphene.String()
    token = graphene.String()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, email, password):
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            user_email = cursor.fetchone()
            
            if user_email:
                return SignUp(status="error", token=None, errors=["User already exists"])

            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            
            cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s) RETURNING id", (email, hashed_password))
            user_id = cursor.fetchone()[0]
            conn.commit()

            token = create_access_token(identity=str(user_id), expires_delta=False)

            return SignUp(status="success", token=token, errors=[])
            
        except Exception as e:
            conn.rollback()
            return SignUp(status="error", token=None, errors=[f"Error: {str(e)}"])
        
        
# Login Mutation
class Login(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    status = graphene.String()
    token = graphene.String()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, email, password):
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, password FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if not user:
                return Login(status="error", token=None, errors=["Email or password is incorrect"])
            
            user_id, hashed_password = user
            
            if not bcrypt.check_password_hash(hashed_password, password):
                return Login(status="error", token=None, errors=["Email or password is incorrect"])

            token = create_access_token(identity=str(user_id), expires_delta=False)
    
            return Login(status="success", token=token, errors=[])
        
        except Exception as e:
            return Login(status="error", token=None, errors=[f"Error: {str(e)}"])
            

class UpdateProfile(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        phone = graphene.String(required=True)
        address = graphene.String(required=True)

    status = graphene.String()
    token = graphene.String()
    errors = graphene.List(graphene.String)
        
    @jwt_required()
    def mutate(self, info, name, phone, address):
        try:
            cursor = conn.cursor()
            
            current_user = get_jwt_identity()
            user_id = current_user

            # Fetch user from DB
            cursor.execute("SELECT id, email FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return UpdateProfile(status="error", token=None, errors=["User does not exist"])
            
            # Update fields if provided
            if name and phone and address:
                print("Update user profile")
                cursor.execute("UPDATE users SET name = %s, phone = %s, address = %s WHERE id = %s", (name, phone, address, user_id))
            
            conn.commit()
            
            # Fetch updated user
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            updated_user_id = cursor.fetchone()
            
            new_token = create_access_token(
                identity=str(updated_user_id), expires_delta=False
            )
            
            return UpdateProfile(status="success", token=new_token, errors=[])
        
        except Exception as e:
            return UpdateProfile(status="error", token=None, errors=[f"Error: {str(e)}"])
    

class AddProduction(graphene.Mutation):
    class Arguments:
        product_code = graphene.String(required=True)
        name = graphene.String(required=True)
        description = graphene.String(required=True)
        price = graphene.Int(required=True)
        sale_percent = graphene.Float(required=False)
        stock = graphene.Int(required=True)
        category_id = graphene.Int(required=True)
        product_type = graphene.Int(required=True)
        image_url = graphene.String(required=True)

    status = graphene.String()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, product_code, name, description, price, stock, category_id, image_url, product_type, sale_percent):
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM products WHERE product_code = %s", (product_code,))
            product = cursor.fetchone()
            
            if product:
                return AddProduction(status="error", errors=["Product have been existed"])
    
            cursor.execute("INSERT INTO products (product_code, name, description, price, stock, category_id, image_url, product_type, sale_percent) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id", (product_code, name, description, price, stock, category_id, image_url, product_type, sale_percent))
            conn.commit()
    
            return AddProduction(status="success", errors=[])

        except Exception as e:
            conn.rollback()
            return AddProduction(status="error", errors=[f"Error: {str(e)}"])


class AddItemToCart(graphene.Mutation):
    class Arguments:
        product_id = graphene.Int(required=True)
        quantity = graphene.Int(required=True)

    status = graphene.String()
    errors = graphene.List(graphene.String)

    @jwt_required()
    def mutate(self, info, product_id, quantity):
        try:
            cursor = conn.cursor()
            
            current_user = get_jwt_identity()
            user_id = current_user
            
            cursor.execute("SELECT id FROM carts WHERE user_id = %s", (user_id,))
            cart_id = cursor.fetchone()
            
            cursor.execute("""
                INSERT INTO cart_items (cart_id, product_id, quantity) VALUES (%s, %s, %s)
                ON CONFLICT (cart_id, product_id)
                DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity
            """, (cart_id, product_id, quantity))
            conn.commit()

            return AddItemToCart(status="success", errors=[])
        
        except Exception as e:
            return AddItemToCart(status="error", errors=[f"Error: {str(e)}"])

class DeleteItemInCart(graphene.Mutation):
    class Arguments:
        product_id = graphene.Int(required=True)
        
    status = graphene.String()
    errors = graphene.List(graphene.String)
    
    @jwt_required()
    def mutate(self, info, product_id):
        try:
            cursor = conn.cursor()
            
            current_user = get_jwt_identity()
            
            cursor.execute("""
                DELETE FROM cart_items WHERE product_id = %s AND cart_id = (SELECT id FROM carts WHERE user_id = %s)
            """, (product_id, current_user))
            conn.commit()
            
            return DeleteItemInCart(status="success", errors=[])
        
        except Exception as e:
            return DeleteItemInCart(status="error", errors=[f"Error: {str(e)}"])
        
