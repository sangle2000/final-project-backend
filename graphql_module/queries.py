import graphene
from flask_jwt_extended import jwt_required, get_jwt_identity

from database.db import conn


class UserData(graphene.ObjectType):
    id = graphene.String()
    email = graphene.String()
    name = graphene.String()
    phone = graphene.String()
    address = graphene.String()
    role = graphene.String()
    created_at = graphene.String()
    wallet = graphene.Int()
    item_in_cart = graphene.Int()
    
class ProductData(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()
    description = graphene.String()
    price = graphene.Int()
    sale_percent = graphene.Float()
    stock = graphene.Int()
    category_id = graphene.String()
    product_type = graphene.String()
    image_url = graphene.String()
    created_at = graphene.String()
    product_code = graphene.String()
    
class CategoryData(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()

class ProductTypeData(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()
    
class UserCartData(graphene.ObjectType):
    id = graphene.Int()
    product_code = graphene.String()
    name = graphene.String()
    price = graphene.Int()
    salePercent = graphene.Float()
    quantity = graphene.Int()
    imageUrl = graphene.String()

class ProtectedDataResponse(graphene.ObjectType):
    status = graphene.String()
    message = graphene.String()
    data = graphene.Field(UserData)
    
class ProductDataResponse(graphene.ObjectType):
    status = graphene.String()
    message = graphene.String()
    data = graphene.List(ProductData)
    
class CategoryDataResponse(graphene.ObjectType):
    status = graphene.String()
    message = graphene.String()
    data = graphene.List(CategoryData)

class ProductTypeDataResponse(graphene.ObjectType):
    status = graphene.String()
    message = graphene.String()
    data = graphene.List(ProductTypeData)
    
class UserCartDataResponse(graphene.ObjectType):
    status = graphene.String()
    message = graphene.String()
    data = graphene.List(UserCartData)

class UserDataQuery(graphene.ObjectType):
    protected_data = graphene.Field(ProtectedDataResponse)
    
    @jwt_required()
    def resolve_protected_data(self, info):
        try:
            user_id = get_jwt_identity()

            cursor = conn.cursor()

            cursor.execute("SELECT id, email, name, phone, address, role, created_at, wallet FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            cursor.execute("SELECT id FROM carts WHERE user_id = %s", (user_id,))
            user_cart_id = cursor.fetchone()
            
            if user is None:
                return ProtectedDataResponse(status=404, message="User not found", data={})
            
            _, email, name, phone, address, role, created_at, wallet = user
            
            if user_cart_id is None:
                print("Create new user cart!!!")
                cursor.execute("INSERT INTO carts (user_id) VALUES (%s)", (user_id,))
                conn.commit()

                data = UserData(
                    id=user_id,
                    email=email,
                    name=name,
                    phone=phone,
                    address=address,
                    role=role,
                    created_at=created_at,
                    wallet=wallet,
                    item_in_cart=0,
                )

                return ProtectedDataResponse(
                    status="success",
                    message="Access granted",
                    data=data
                )

            cursor.execute("""
                SELECT COUNT(*) 
                FROM cart_items 
                WHERE cart_id = (SELECT id FROM carts WHERE user_id = %s);
            """, (user_id,))
            item_in_cart = cursor.fetchone()[0]
            
            data = UserData(
                id=user_id,
                email=email,
                name=name,
                phone=phone,
                address=address,
                role=role,
                created_at=created_at,
                wallet=wallet,
                item_in_cart=item_in_cart,
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

            cursor = conn.cursor()

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

class ProductTypeDataQuery(graphene.ObjectType):
    product_type_data = graphene.Field(ProductTypeDataResponse)

    def resolve_product_type_data(self, info):
        try:
            print("Start query product type")

            cursor = conn.cursor()

            cursor.execute("SELECT * FROM product_type")
            product_types = cursor.fetchall()

            # Convert SQLAlchemy objects to GraphQL objects
            product_type_data_list = [
                ProductTypeData(id=product_type_item[0], name=product_type_item[1]) for product_type_item in product_types
            ]

            return ProductTypeDataResponse(
                status="success",
                message="Product Type retrieved",
                data=product_type_data_list
            )

        except Exception as e:
            print("Error", str(e))
            
            return ProductTypeDataResponse(
                status="error",
                message=f"Error: {str(e)}",
                data=None
            )

class ProductDataQuery(graphene.ObjectType):
    product_data = graphene.Field(ProductDataResponse)
    
    def resolve_product_data(self, info):
        try:
            print("Start query product")

            cursor = conn.cursor()

            cursor.execute("""
                    SELECT p.id, p.name, p.description, p.price, p.stock, pt.name AS type, c.name AS category, p.created_at, p.image_url, p.product_code, p.sale_percent
                    FROM products p
                    JOIN product_type pt ON p.product_type = pt.id
                    JOIN categories c ON p.category_id = c.id
                    ORDER BY id ASC
                """)
            products = cursor.fetchall()
            
            print("Products:", products)

            # Convert SQLAlchemy objects to GraphQL objects
            product_data_list = [
                ProductData(
                    id=product_item[0], 
                    name=product_item[1],
                    description=product_item[2],
                    price=product_item[3],
                    stock=product_item[4],
                    product_type=product_item[5],
                    category_id=product_item[6],
                    created_at=product_item[7],
                    image_url=product_item[8],
                    product_code=product_item[9],
                    sale_percent=product_item[10]
                ) for product_item in products
            ]
        
            return ProductDataResponse(
                status="success",
                message="Product Type retrieved",
                data=product_data_list
            )

        except Exception as e:
            print("Error: ", str(e))

            return ProductDataResponse(
                status="error",
                message=f"Error: {str(e)}",
                data=None
            )

class UserCartDataQuery(graphene.ObjectType):
    user_cart_data = graphene.Field(UserCartDataResponse)
    
    @jwt_required()
    def resolve_user_cart_data(self, info):
        try:
            print("Update User Cart Data!!!")
            
            cursor = conn.cursor()
            
            current_user = get_jwt_identity()

            cursor.execute("""
                SELECT p.id, p.product_code, p.name, p.price, p.sale_percent, ci.quantity, p.image_url 
                FROM cart_items ci
                JOIN products p ON ci.product_id = p.id
                JOIN carts c ON ci.cart_id = c.id
                WHERE c.user_id = %s
            """, (current_user,))
            
            cart_items = cursor.fetchall()
            
            user_cart_item_list = [
                UserCartData(
                    id=item[0],
                    product_code=item[1],
                    name=item[2],
                    price=item[3],
                    salePercent=item[4],
                    quantity=item[5],
                    imageUrl=item[6]
                ) for item in cart_items
            ]
            
            return UserCartDataResponse(
                status="success",
                message="User cart retrieved",
                data=user_cart_item_list
            )
        
        except Exception as e:
            return UserCartDataResponse(
                status="error",
                message=f"Error: {str(e)}",
                data=None
            )
