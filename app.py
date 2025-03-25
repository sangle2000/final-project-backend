from flask import Flask
from flask_graphql import GraphQLView
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import graphene
from flask import request, jsonify
import hashlib
import os

from dotenv import load_dotenv

from payment.vnpay import vnpay

from graphql_module.mutations import SignUp, Login, UpdateProfile, AddProduction, UpdateUserCartItem, Payment
from graphql_module.queries import UserDataQuery, CategoryDataQuery, ProductTypeDataQuery, ProductDataQuery, \
    UserCartDataQuery

load_dotenv()

VNPAY_HASH_SECRET_KEY = os.getenv("VNPAY_HASH_SECRET_KEY")

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
    updateUserCartItem = UpdateUserCartItem.Field()
    payment = Payment.Field()
    
class Query(UserDataQuery, ProductDataQuery, CategoryDataQuery, ProductTypeDataQuery, UserCartDataQuery, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)

@app.route("/payment_return", methods=["GET"])
def vnpay_return():
    vnp = vnpay()

    vnp.responseData = request.args.to_dict()

    order_id = request.args.get("vnp_TxnRef")
    amount = int(request.args.get("vnp_Amount")) / 100
    order_desc = request.args.get('vnp_OrderInfo')
    vnp_TransactionNo = request.args.get("vnp_TransactionNo")
    vnp_ResponseCode = request.args.get("vnp_ResponseCode")
    
    if vnp.validate_response(VNPAY_HASH_SECRET_KEY):
        if vnp_ResponseCode == "00":
            return {"title": "Kết quả thanh toán",
                    "result": "Thành công", "order_id": order_id,
                    "amount": amount,
                    "order_desc": order_desc,
                    "vnp_TransactionNo": vnp_TransactionNo,
                    "vnp_ResponseCode": vnp_ResponseCode}
        else:
            return {"title": "Kết quả thanh toán",
                    "result": "Lỗi", "order_id": order_id,
                    "amount": amount,
                    "order_desc": order_desc,
                    "vnp_TransactionNo": vnp_TransactionNo,
                    "vnp_ResponseCode": vnp_ResponseCode}
    else:
        return {"title": "Kết quả thanh toán", 
                "result": "Lỗi", 
                "order_id": order_id, 
                "amount": amount,
                "order_desc": order_desc, 
                "vnp_TransactionNo": vnp_TransactionNo,
                "vnp_ResponseCode": vnp_ResponseCode, 
                "msg": "Sai checksum"}

# Add GraphQL Route
app.add_url_rule('/api/graphql', view_func=GraphQLView.as_view("graphql_module", schema=schema, graphiql=True))

if __name__ == '__main__':
    app.run(debug=True)
