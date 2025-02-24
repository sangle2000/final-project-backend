import graphene
from flask_jwt_extended import jwt_required, get_jwt_identity

class Query(graphene.ObjectType):
    protected_data = graphene.String()
    
    @jwt_required()
    def resolve_protected_data(self, info):
        user = get_jwt_identity()
        return f"Hello {user['email']}, this is protected data"
