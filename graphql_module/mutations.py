import graphene
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from database.db import cursor, conn

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
            cursor.execute("SELECT id, email, password, name, wallet, phone, address, role, created_at FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if not user:
                return Login(status="error", token=None, errors=["Email or password is incorrect"])
            
            user_id, user_email, hashed_password, user_name, user_wallet, user_phone, user_address, user_role, user_created_at = user
            
            if not bcrypt.check_password_hash(hashed_password, password):
                return Login(status="error", token=None, errors=["Email or password is incorrect"])

            token = create_access_token(
                identity=str(user_id),
                additional_claims={
                    "email": str(user_email),
                    "name": str(user_name),
                    "phone": str(user_phone),
                    "address": str(user_address),
                    "role": str(user_role),
                    "created_at": str(user_created_at),
                    "wallet": str(user_wallet)
                },
                expires_delta=False
            )
    
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
            print("Get Request")
            current_user = get_jwt_identity()
            user_id = current_user
            
            print(name)
            print(phone)
            print(address)
            
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
            cursor.execute("SELECT id, email, name, wallet, phone, address, role, created_at FROM users WHERE id = %s", (user_id,))
            updated_user = cursor.fetchone()
            updated_id, updated_email, updated_name, updated_wallet, updated_phone, updated_address, updated_role, updated_time = updated_user
            
            new_token = create_access_token(
                identity=str(updated_id),
                additional_claims={
                    "email": str(updated_email),
                    "name": str(updated_name),
                    "phone": str(updated_phone),
                    "address": str(updated_address),
                    "role": str(updated_role),
                    "created_at": str(updated_time),
                    "wallet": str(updated_wallet)
                },
                expires_delta=False
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
        stock = graphene.Int(required=True)
        category_id = graphene.Int(required=True)
        image_url = graphene.String(required=True)

    status = graphene.String()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, product_code, name, description, price, stock, category_id, image_url):
        try:
            cursor.execute("SELECT id FROM products WHERE product_code = %s", (product_code,))
            product = cursor.fetchone()
            
            if product:
                return UpdateProfile(status="error", errors=["Product have been existed"])
    
            cursor.execute("INSERT INTO products (product_code, name, description, price, stock, category_id, image_url) VALUES (%s, %s) RETURNING id", (product_code, name, description, price, stock, category_id, image_url))
            conn.commit()
    
            return SignUp(status="success", errors=[])

        except Exception as e:
            conn.rollback()
            return SignUp(status="error", token=None, errors=[f"Error: {str(e)}"])
