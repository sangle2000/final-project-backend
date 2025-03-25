import graphene
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from database.db import conn

from payment.vnpay import vnpay

import os

from dotenv import load_dotenv

from datetime import datetime

load_dotenv()

VNPAY_TMN_CODE = os.getenv("VNPAY_TMN_CODE")
VNPAY_RETURN_URL = os.getenv("VNPAY_RETURN_URL")
VNPAY_PAYMENT_URL = os.getenv("VNPAY_PAYMENT_URL")
VNPAY_HASH_SECRET_KEY = os.getenv("VNPAY_HASH_SECRET_KEY")

bcrypt = Bcrypt()

class UpdateUserCartItemInput(graphene.InputObjectType):
    product_id = graphene.Int(required=True)
    user_action = graphene.String(required=True)
    quantity = graphene.Int()

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

class UpdateUserCartItem(graphene.Mutation):
    class Arguments:
        payload = graphene.List(UpdateUserCartItemInput, required=True)
        
    status = graphene.String()
    errors = graphene.List(graphene.String)
    
    @jwt_required()
    def mutate(self, info, payload):
        try:
            current_user = get_jwt_identity()
            
            cursor = conn.cursor()
            
            print(current_user)
            
            for item in payload:
                print(item)
                if item.user_action == "add":
                    cursor.execute("SELECT id FROM carts WHERE user_id = %s", (current_user,))
                    cart_id = cursor.fetchone()

                    cursor.execute("""
                        INSERT INTO cart_items (cart_id, product_id, quantity) VALUES (%s, %s, %s)
                        ON CONFLICT (cart_id, product_id)
                        DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity
                    """, (cart_id, item.product_id, item.quantity))
                    conn.commit()
                    
                    print("Add item to cart successfully!!!")
                
                elif item.user_action == "update":
                    cursor.execute("""
                        UPDATE cart_items AS ci
                        SET quantity = %s
                        FROM carts AS c
                        WHERE ci.cart_id = c.id
                        AND c.user_id = %s 
                        AND ci.product_id = %s
                    """, (item.quantity, current_user, item.product_id))
                    
                    conn.commit()
                    
                    print("Update successfully!!!")
                    
                elif item.user_action == "delete":
                    cursor.execute("""
                        DELETE FROM cart_items AS ci
                        WHERE ci.product_id = %s
                        AND ci.cart_id = (SELECT id FROM carts WHERE user_id = %s)
                    """, (item.product_id, current_user))
                    
                    conn.commit()
                    
                    print("Delete successfully!!!")
                    
            return UpdateUserCartItem(status="success", errors=[])

        except Exception as e:
            return UpdateUserCartItem(status="error", errors=[f"Error: {str(e)}"])

class Payment(graphene.Mutation):
    class Arguments:
        order_type = graphene.String(required=True)
        order_id = graphene.String(required=True)
        amount = graphene.Int(required=True)
        order_desc = graphene.String(required=True)
        bank_code = graphene.String(required=False)
        language = graphene.String(required=False)
        
    status = graphene.String()
    redirect_url = graphene.String()
    errors = graphene.List(graphene.String)
    
    @jwt_required()
    def mutate(self, info, order_type, order_id, amount, order_desc, bank_code, language):
        try:
            ipaddr = "localhost:5000"
            # Build URL Payment
            vnp = vnpay()
            vnp.requestData['vnp_Version'] = '2.1.0'
            vnp.requestData['vnp_Command'] = 'pay'
            vnp.requestData['vnp_TmnCode'] = VNPAY_TMN_CODE
            vnp.requestData['vnp_Amount'] = amount * 100
            vnp.requestData['vnp_CurrCode'] = 'VND'
            vnp.requestData['vnp_TxnRef'] = order_id
            vnp.requestData['vnp_OrderInfo'] = order_desc
            vnp.requestData['vnp_OrderType'] = order_type
            # Check language, default: vn
            if language and language != '':
                vnp.requestData['vnp_Locale'] = language
            else:
                vnp.requestData['vnp_Locale'] = 'vn'
                # Check bank_code, if bank_code is empty, customer will be selected bank on VNPAY
            if bank_code and bank_code != "":
                vnp.requestData['vnp_BankCode'] = bank_code
    
            vnp.requestData['vnp_CreateDate'] = datetime.now().strftime('%Y%m%d%H%M%S')  # 20150410063022
            vnp.requestData['vnp_IpAddr'] = ipaddr
            vnp.requestData['vnp_ReturnUrl'] = VNPAY_RETURN_URL
            vnpay_payment_url = vnp.get_payment_url(VNPAY_PAYMENT_URL, VNPAY_HASH_SECRET_KEY)
            print(vnpay_payment_url)
    
            return Payment(status="success", redirect_url=vnpay_payment_url, errors=[])
        
        except Exception as e:
            return Payment(status="error", redirect_url="", errors=[f"Error: {str(e)}"])
