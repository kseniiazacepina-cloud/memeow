from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'Покупатель'),
        ('manager', 'Менеджер'),
        ('admin', 'Администратор'),
    ]
    
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    registration_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class Category(models.Model):
    pass

class Manufacturer(models.Model):
    pass

class Product(models.Model):
    pass

class Cart(models.Model):
    pass

class Order(models.Model):
    pass

class OrderItem(models.Model):
    pass

class Payment(models.Model):
    pass

class Review(models.Model):
    pass