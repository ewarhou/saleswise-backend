from ninja import NinjaAPI, Schema
from api.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
from typing import Optional
from ninja.security import HttpBearer
from django.conf import settings
import secrets
from datetime import datetime, timedelta

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            user = User.objects.get(auth_token=token)
            request.user = user
            return user
        except User.DoesNotExist:
            return None

api = NinjaAPI(csrf=False, auth=AuthBearer())

class SignupSchema(Schema):
    email: str
    password: str

class LoginSchema(Schema):
    email: str
    password: str

class ChangePasswordSchema(Schema):
    user_email: str
    new_password: str

class TokenSchema(Schema):
    access_token: str
    token_type: str

@api.post("/auth/register", auth=None)
def register(request, data: SignupSchema):
    if User.objects.filter(email=data.email).exists():
        return {"success": False, "message": "Email already registered"}
    
    token = secrets.token_urlsafe(32)
    user = User.objects.create(
        username=data.email,
        email=data.email,
        password=make_password(data.password),
        auth_token=token
    )
    
    return {
        "success": True,
        "message": "User registered successfully",
        "token": token
    }

@api.post("/auth/login", auth=None)
def login(request, data: LoginSchema):
    user = authenticate(username=data.email, password=data.password)
    if user is None:
        return {"success": False, "message": "Invalid credentials"}
    
    token = secrets.token_urlsafe(32)
    user.auth_token = token
    user.save()
    
    return {
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email,
        },
        "token": token
    }

@api.post("/auth/change-password")
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

@api.get("/hello", auth=None)
def hello(request):
    return {"message": "Hello from SalesWise!"} 