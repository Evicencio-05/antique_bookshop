from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from datetime import date

class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Roles"
    
class Employee(models.Model):
    employee_id = models.AutoField(primary_key=True)
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    address = models.CharField()
    zip_code = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    hire_date = models.DateField(auto_now_add=True, editable=True)
    phone_number = models.CharField(max_length=50)
    position_id = models.ForeignKey(Role, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Author(models.Model):
    author_id = models.AutoField(primary_key=True)
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100, blank=True)
    birth_year = models.DateField(blank=True)
    death_year = models.DateField(blank=True)
    description = models.TextField(max_length=1000, blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()

class Book(models.Model):
    class Rating(models.TextChoices):
        SUPERB = 'superb', _('Superb')
        EXCELLENT = 'excellent', _('Excellent')
        GOOD = 'good', _('Good')
        FAIR = 'fair', _('Fair')
        POOR = 'poor', _('Poor')
        DAMAGED = 'damaged', _('Damaged')
        UNRATED = 'unrated', _('Unrated')
        
    class Status(models.TextChoices):
        SOLD = 'sold', _('Sold')
        RESERVED = 'reserved', _('Reserved')
        AVAILABLE = 'available', _('Available')
        PROCESSING = 'processing', _('Processing')
        
    book_id = models.CharField(max_length=8, Validators=[MinValueValidator(8)], primary_key=True)
    title = models.CharField(max_length=500)
    cost = models.DecimalField(max_digits=11, decimal_places=2)
    retail_price = models.DecimalField(max_digits=11, decimal_places=2)
    publication_date = models.DateField()
    edition = models.CharField(max_length=50, blank=True)
    rating = models.CharField(max_length=10, choices=Rating.choices, default=Rating.UNRATED)
    authors = models.ManyToManyField(Author, related_name='books')
    book_status = models.CharField(max_length=10, choices=Status.choices, default=Status.PROCESSING)
    
    def __str__(self):
        return f"{self.book_id}: {self.title}"

class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    last_name = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=25, blank=True)
    mailing_address = models.CharField(blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(first_name__isnull=False) | models.Q(first_name__isnull=True), 
                                    name='name_required')
        ]
        
class Order(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = 'cash', _('Cash')
        CHECK = 'check', _('Check')
        CREDIT = 'credit', _('Credit Card')
        OTHER = 'other', _('Other')
        
    class OrderStatus(models.TextChoices):
        TO_SHIP = 'to_ship', _('To Be Shipped')
        PICKUP = 'pickup', _('Customer Will Pick Up')
        SHIPPED = 'shipped', _('Shipped')
        PICKED_UP = 'picked_up', _('Picked Up')
    
    order_id = models.AutoField(primary_key=True)
    customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE)
    employee_id = models.ForeignKey(Employee, on_delete=models.CASCADE)
    order_date = models.DateField(auto_now_add=True, editable=True)
    delivery_pickup_date = models.DateField(null=True, blank=True)
    sale_amount = models.DecimalField(max_digits=11, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices)
    status = models.CharField(max_length=30, choices=OrderStatus.choices, default='pickup')
    books = models.ManyToManyField(Book, related_name='orders')
    
    def completed_order(self):
        for book in self.books.all():
            book.book_stats = 'sold'
            book.save()
        self.delivery_pickup_date = date.today()
        if self.status == 'to_be_shipped':
            self.status = 'shipped'
        else:
            self.status = 'picked_up'
        self.save()
    
    def __str__(self):
        return f"Order {self.order_id} -> {self.customer_id}"
    
from django.db.models.signals import post_save
from django.contrib.auth.models import Group
from django.dispatch import receiver

@receiver(post_save, sender=Employee)
def assign_group_to_employee(sender, instance, created, **kwargs):
    if created:
        group_name = 'ClerkGroup'
        if instance.position_id.title == 'Owner':
            group_name = 'OwnerGroup'
        elif instance.position_id.title == 'Assistant Manager':
            group_name = 'ManagerGroup'
        group, _ = Group.objects.get_or_create(name=group_name)
        instance.employee_id.groups.add(group)