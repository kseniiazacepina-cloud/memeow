from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    pass

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