from ninja import NinjaAPI, Schema
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
from typing import Optional
from ninja.security import django_auth

api = NinjaAPI()

class SignupSchema(Schema):
    email: str
    password: str

class LoginSchema(Schema):
    email: str
    password: str

class ChangePasswordSchema(Schema):
    user_email: str
    new_password: str

@api.post("/auth/register")
def register(request, data: SignupSchema):
    if User.objects.filter(email=data.email).exists():
        return {"success": False, "message": "Email already registered"}
    
    user = User.objects.create(
        username=data.email,
        email=data.email,
        password=make_password(data.password)
    )
    
    return {"success": True, "message": "User registered successfully"}

@api.post("/auth/login")
def login(request, data: LoginSchema):
    user = authenticate(username=data.email, password=data.password)
    if user is None:
        return {"success": False, "message": "Invalid credentials"}
    
    return {
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email,
        }
    }

@api.post("/auth/change-password")
@django_auth
def change_password(request, data: ChangePasswordSchema):
    if not request.user.is_staff:
        return {"success": False, "message": "Only admins can change passwords"}
    
    try:
        user = User.objects.get(email=data.user_email)
        user.password = make_password(data.new_password)
        user.save()
        return {"success": True, "message": "Password changed successfully"}
    except User.DoesNotExist:
        return {"success": False, "message": "User not found"}

@api.get("/hello")
def hello(request):
    return {"message": "Hello from SalesWise!"} 