import graphene
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from database.db import cursor


class UserData(graphene.ObjectType):
    id = graphene.String()
    email = graphene.String()
    name = graphene.String()
    phone = graphene.String()
    address = graphene.String()
    role = graphene.String()
    created_at = graphene.String()
    wallet = graphene.Int()
    
class CategoryData(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()

class ProtectedDataResponse(graphene.ObjectType):
    status = graphene.String()
    message = graphene.String()
    data = graphene.Field(UserData)
    
class CategoryDataResponse(graphene.ObjectType):
    status = graphene.String()
    message = graphene.String()
    data = graphene.List(CategoryData)

class UserDataQuery(graphene.ObjectType):
    protected_data = graphene.Field(ProtectedDataResponse)
    
    @jwt_required()
    def resolve_protected_data(self, info):
        try:
            user_id = get_jwt_identity()
            claims = get_jwt()
            
            print("Query user data")
            
            data = UserData(
                id=user_id,
                email=claims["email"],
                name=claims["name"],
                phone=claims["phone"],
                address=claims["address"],
                role=claims["role"],
                created_at=claims["created_at"],
                wallet=int(claims["wallet"]),
            )
            
            return ProtectedDataResponse(
                status="success",
                message="Access granted",
                data=data
            )
        
        except Exception as e:
            return ProtectedDataResponse(
                status="error",
                message=f"Error: {str(e)}",
                data=None
            )

class CategoryDataQuery(graphene.ObjectType):
    category_data = graphene.Field(CategoryDataResponse)
    
    def resolve_category_data(self, info):
        try:
            print("Start query category")

            cursor.execute("SELECT * FROM categories")
            categories = cursor.fetchall()
            
            print(categories)

            # Convert SQLAlchemy objects to GraphQL objects
            category_data_list = [
                CategoryData(id=category[0], name=category[1]) for category in categories
            ]
            
            return CategoryDataResponse(
                status="success",
                message="Categories retrieved",
                data=category_data_list
            )
            
        except Exception as e:
            return CategoryDataResponse(
                status="error",
                message=f"Error: {str(e)}",
                data=None
            )
