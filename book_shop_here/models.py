from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User

class Rating(models.TextChoices):
    SUPERB = 'superb', 'Superb'
    EXCELLENT = 'excellent', 'Excellent'
    GOOD = 'good', 'Good'
    FAIR = 'fair', 'Fair'
    POOR = 'poor', 'Poor'
    DAMAGED = 'damaged', 'Damaged'

    
class PaymentMethod(models.TextChoices):
    CASH = 'cash', 'Cash'
    CHECK = 'check', 'Check'
    CREDIT = 'credit', 'Credit Card'
    
class OrderStatus(models.TextChoices):
    TO_SHIP = 'to_ship', 'To Be Shipped'
    PICKUP = 'pickup', 'Customer Will Pick Up'
    SHIPPED = 'shipped', 'Shipped'
    PICKED_UP = 'picked_up', 'Picked Up'

class Position(models.Model):
    from django.utils.translation import gettext_lazy as _
    
    class Position(models.TextChoices):
        OWNER = 'owner', _('Owner')
        ASSISTANT_MANAGER = 'assistant_manager', 'Assistant Manager'
        FULL_TIME = 'full_time', 'Full Time Sales Clerk'
        PART_TIME = 'part_time', 'Part Time Sales Clerk'
        
    position_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50, choices=[
        ('owner', 'Owner'),
        ('assistant_manager', 'Assistant Manager'),
        ('full_time', 'Full Time Sales Clerk'),
        ('part_time', 'Part Time Sales Clerk')
    ])
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title

class Author(models.Model):
    author_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    birth_year = models.DateField(blank=True)
    death_year = models.DateField(blank=True)
    description = models.TextField(max_length=1000, blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()
    
class Book(models.Model):
    book_id = models.CharField(max_length=8, Validators=[MinValueValidator(8)], primary_key=True)
    title = models.CharField(max_length=500)
    cost = models.DecimalField(max_digits=11, decimal_places=2)
    retail_price = models.DecimalField(max_digits=11, decimal_places=2)
    publication_date = models.DateField()
    edition = models.CharField(max_length=50, blank=True)
    rating = models.CharField(max_length=10, choices=[])