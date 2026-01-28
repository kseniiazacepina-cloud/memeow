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
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, 
                              null=True, blank=True, related_name='children')
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name

class Manufacturer(models.Model):
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='manufacturers/', blank=True, null=True)

    class Meta:
        verbose_name = "Производитель"
        verbose_name_plural = "Производители"

    def __str__(self):
        return f"{self.name} ({self.country})"

class Product(models.Model):
    name = models.CharField(max_length=300)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, related_name='products')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True)
    images = models.JSONField(default=list)
    specifications = models.JSONField(default=dict)
    rating = models.FloatField(default=0)
    review_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['-created_at']

    def __str__(self):
        return self.name
    
    @property
    def final_price(self):
        if self.discount:
            return self.price * (1 - self.discount / 100)
        return self.price

class Cart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'product']
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.quantity})"
    
    @property
    def total_price(self):
        return self.product.final_price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('paid', 'Оплачен'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]

class OrderItem(models.Model):
    pass

class Payment(models.Model):
    pass

class Review(models.Model):
    pass