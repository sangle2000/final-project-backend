from tkinter.font import names

import graphene
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from database.db import cursor, conn
from .types import UserType
from graphql import GraphQLError

bcrypt = Bcrypt()

class SignUp(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        
    user = graphene.Field(UserType)
    
    def mutate(self, info, email, password):
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user_email = cursor.fetchone()
        
        if user_email:
            raise GraphQLError("User has been exists")

        try:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s) RETURNING id", (email, hashed_password))
            user_id = cursor.fetchone()[0]
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise GraphQLError(f"Database error: {str(e)}")
        
        token = create_access_token(identity={"id": user_id, "email": email})
        
        return SignUp(user=UserType(id=user_id, email=email, token=token, wallet=0, name="Unknown"))
        
        
# Login Mutation
class Login(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
    
    user = graphene.Field(UserType)
    
    def mutate(self, info, email, password):
        cursor.execute("SELECT id, email, password, name, wallet FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            raise GraphQLError("User not found")
        
        user_id, user_email, hashed_password, user_name, user_wallet = user
        
        if not bcrypt.check_password_hash(hashed_password, password):
            raise GraphQLError("Invalid password")
        
        token = create_access_token(identity={"id": user_id, "email": email})

        return Login(user=UserType(id=user_id, email=user_email, token=token, wallet=user_wallet, name=user_name))
