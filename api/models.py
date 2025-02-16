from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
    auth_token = models.CharField(max_length=255, null=True, blank=True, unique=True)

class Employee(models.Model):
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Sale(models.Model):
    SHIFT_CHOICES = [
        ('matin', 'Matin'),
        ('après-midi', 'Après-midi'),
        ('nuit', 'Nuit'),
    ]

    date = models.DateField()
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES)
    sales_amount = models.DecimalField(max_digits=10, decimal_places=2)
    employees = models.ManyToManyField(Employee, through='SaleEmployee')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['shift']),
        ]

    def __str__(self):
        return f"{self.date} - {self.shift}"

class SaleEmployee(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['sale', 'employee']),
        ]

    def __str__(self):
        return f"{self.sale} - {self.employee.name}"
