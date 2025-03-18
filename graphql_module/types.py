import graphene

class UserType(graphene.ObjectType):
    id = graphene.Int()
    email = graphene.String()
    name = graphene.String()
    token = graphene.String()
    wallet = graphene.Int()
    phone = graphene.String()
    address = graphene.String()
    time = graphene.String()
    