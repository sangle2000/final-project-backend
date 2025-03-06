from flask import Flask
from flask_graphql import GraphQLView
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import graphene

from graphql_module.mutations import SignUp, Login, UpdateProfile, AddProduction
from graphql_module.queries import UserDataQuery, CategoryDataQuery

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "419c2d3376b522f9253ed82e4ffd36c86c34a3c2af4a7268c2ce2264a56db70f"
jwt = JWTManager(app)
CORS(app)

# Define GraphQL Schema
class Mutation(graphene.ObjectType):
    sign_up = SignUp.Field()
    login = Login.Field()
    updateProfile = UpdateProfile.Field()
    addProduction = AddProduction.Field()
    
class Query(UserDataQuery, CategoryDataQuery, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)

# Add GraphQL Route
app.add_url_rule('/api/graphql', view_func=GraphQLView.as_view("graphql_module", schema=schema, graphiql=True))

if __name__ == '__main__':
    app.run(debug=True)
