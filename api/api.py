from ninja import NinjaAPI, Schema
from api.models import User, Employee, Sale, SaleEmployee
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
from typing import Optional, List
from ninja.security import HttpBearer
from django.conf import settings
import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Avg
from django.shortcuts import get_object_or_404

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

class EmployeeSchema(Schema):
    name: str

class EmployeeOutSchema(Schema):
    id: int
    name: str
    active: bool

class SaleSchema(Schema):
    date: str
    shift: str
    sales_amount: Decimal
    employee_ids: List[int]

class SaleOutSchema(Schema):
    id: int
    date: str
    shift: str
    sales_amount: Decimal
    employees: List[EmployeeOutSchema]

class EmployeeStatsSchema(Schema):
    name: str
    total_sales: Decimal
    days_worked: int
    average_sales: Decimal

class DailyReportSchema(Schema):
    total_sales: Decimal
    shift_totals: dict
    top_employee: str
    best_shift: str

class MonthlyEmployeeStatsSchema(Schema):
    name: str
    total: Decimal
    days_worked: int
    average: Decimal

class DailyBreakdownSchema(Schema):
    date: str
    total: Decimal

class MonthlyReportSchema(Schema):
    total_sales: Decimal
    top_employees: List[MonthlyEmployeeStatsSchema]
    daily_breakdown: List[DailyBreakdownSchema]

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

@api.get("/employees", response=List[EmployeeOutSchema])
def list_employees(request):
    employees = Employee.objects.filter(active=True)
    return [{"id": e.id, "name": e.name, "active": e.active} for e in employees]

@api.post("/employees", response=EmployeeOutSchema)
def create_employee(request, data: EmployeeSchema):
    employee = Employee.objects.create(name=data.name)
    return {"id": employee.id, "name": employee.name, "active": employee.active}

@api.get("/employees/stats", response=List[EmployeeStatsSchema])
def employee_stats(request, start_date: str, end_date: str):
    stats = []
    employees = Employee.objects.filter(active=True)
    
    for employee in employees:
        sales = Sale.objects.filter(
            employees=employee,
            date__range=[start_date, end_date]
        )
        total_sales = sales.aggregate(total=Sum('sales_amount'))['total'] or 0
        days_worked = sales.dates('date', 'day').count()
        average_sales = total_sales / days_worked if days_worked > 0 else 0
        
        stats.append({
            "name": employee.name,
            "total_sales": total_sales,
            "days_worked": days_worked,
            "average_sales": average_sales
        })
    
    return stats

@api.get("/sales", response=List[SaleOutSchema])
def list_sales(request, date: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None):
    sales = Sale.objects.all()
    
    if date:
        sales = sales.filter(date=date)
    elif start_date and end_date:
        sales = sales.filter(date__range=[start_date, end_date])
    
    return [{
        "id": sale.id,
        "date": str(sale.date),
        "shift": sale.shift,
        "sales_amount": sale.sales_amount,
        "employees": [{
            "id": e.id,
            "name": e.name,
            "active": e.active
        } for e in sale.employees.all()]
    } for sale in sales]

@api.post("/sales", response=SaleOutSchema)
def create_sale(request, data: SaleSchema):
    sale = Sale.objects.create(
        date=data.date,
        shift=data.shift,
        sales_amount=data.sales_amount
    )
    
    for employee_id in data.employee_ids:
        employee = get_object_or_404(Employee, id=employee_id)
        SaleEmployee.objects.create(sale=sale, employee=employee)
    
    return {
        "id": sale.id,
        "date": str(sale.date),
        "shift": sale.shift,
        "sales_amount": sale.sales_amount,
        "employees": [{
            "id": e.id,
            "name": e.name,
            "active": e.active
        } for e in sale.employees.all()]
    }

@api.put("/sales/{sale_id}", response=SaleOutSchema)
def update_sale(request, sale_id: int, data: SaleSchema):
    sale = get_object_or_404(Sale, id=sale_id)
    
    sale.date = data.date
    sale.shift = data.shift
    sale.sales_amount = data.sales_amount
    sale.save()
    
    # Update employees
    SaleEmployee.objects.filter(sale=sale).delete()
    for employee_id in data.employee_ids:
        employee = get_object_or_404(Employee, id=employee_id)
        SaleEmployee.objects.create(sale=sale, employee=employee)
    
    return {
        "id": sale.id,
        "date": str(sale.date),
        "shift": sale.shift,
        "sales_amount": sale.sales_amount,
        "employees": [{
            "id": e.id,
            "name": e.name,
            "active": e.active
        } for e in sale.employees.all()]
    }

@api.delete("/sales/{sale_id}")
def delete_sale(request, sale_id: int):
    sale = get_object_or_404(Sale, id=sale_id)
    sale.delete()
    return {"success": True, "message": "Sale deleted successfully"}

@api.get("/reports/daily", response=DailyReportSchema)
def daily_report(request, date: str):
    sales = Sale.objects.filter(date=date)
    total_sales = sales.aggregate(total=Sum('sales_amount'))['total'] or 0
    
    shift_totals = {
        'matin': 0,
        'après-midi': 0,
        'nuit': 0
    }
    
    for sale in sales:
        shift_totals[sale.shift] = float(sale.sales_amount)
    
    best_shift = max(shift_totals.items(), key=lambda x: x[1])[0] if total_sales > 0 else None
    
    # Find top employee
    employee_sales = {}
    for sale in sales:
        for employee in sale.employees.all():
            if employee.name not in employee_sales:
                employee_sales[employee.name] = 0
            employee_sales[employee.name] += float(sale.sales_amount)
    
    top_employee = max(employee_sales.items(), key=lambda x: x[1])[0] if employee_sales else None
    
    return {
        "total_sales": total_sales,
        "shift_totals": shift_totals,
        "top_employee": top_employee,
        "best_shift": best_shift
    }

@api.get("/reports/monthly", response=MonthlyReportSchema)
def monthly_report(request, month: int, year: int):
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    
    sales = Sale.objects.filter(date__range=[start_date, end_date])
    total_sales = sales.aggregate(total=Sum('sales_amount'))['total'] or 0
    
    # Calculate employee stats
    employee_stats = []
    for employee in Employee.objects.filter(active=True):
        employee_sales = sales.filter(employees=employee)
        total = employee_sales.aggregate(total=Sum('sales_amount'))['total'] or 0
        days_worked = employee_sales.dates('date', 'day').count()
        average = total / days_worked if days_worked > 0 else 0
        
        if total > 0:
            employee_stats.append({
                "name": employee.name,
                "total": total,
                "days_worked": days_worked,
                "average": average
            })
    
    # Sort employee stats by total sales
    employee_stats.sort(key=lambda x: x['total'], reverse=True)
    
    # Daily breakdown
    daily_breakdown = []
    current_date = start_date
    while current_date <= end_date:
        day_sales = sales.filter(date=current_date)
        total = day_sales.aggregate(total=Sum('sales_amount'))['total'] or 0
        if total > 0:
            daily_breakdown.append({
                "date": str(current_date.date()),
                "total": total
            })
        current_date += timedelta(days=1)
    
    return {
        "total_sales": total_sales,
        "top_employees": employee_stats,
        "daily_breakdown": daily_breakdown
    } 