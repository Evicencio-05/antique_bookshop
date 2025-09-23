from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from datetime import date

class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50, verbose_name='Role title')
    description = models.TextField(blank=True, null=True, verbose_name= _('Role description'))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Roles"
    
class Employee(models.Model):
    employee_id = models.AutoField(primary_key=True)
    last_name = models.CharField(max_length=50, verbose_name= _('Employee last name'))
    first_name = models.CharField(max_length=50, verbose_name= _('Employee first name'))
    address = models.CharField(max_length=200, verbose_name= _('Employee address'))
    zip_code = models.CharField(max_length=50, verbose_name= _('Employee zip code'))
    state = models.CharField(max_length=50, verbose_name= _('Employee state'))
    hire_date = models.DateField(auto_now_add=True, verbose_name= _('Employee hire date'))
    birth_date = models.DateField(auto_now_add=False, verbose_name= _('Employee date of birth'), default=date(1600,1,1))
    phone_number = models.CharField(max_length=50, verbose_name= _('Employee phone number'))
    position_id = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name= _('Employee role ID'))
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, verbose_name= _('Employee user'))

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Author(models.Model):
    author_id = models.AutoField(primary_key=True, editable=False)
    last_name = models.CharField(max_length=100, verbose_name= _('Author last name'))
    first_name = models.CharField(max_length=100, blank=True, default='', verbose_name= _('Author first name'))
    birth_year = models.SmallIntegerField(blank=True, null=True, verbose_name= _('Author birth year'))
    death_year = models.SmallIntegerField(blank=True, null=True, verbose_name= _('Author death year'))
    description = models.TextField(max_length=1000, blank=True, null=True, verbose_name= _('Author description'))

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()

import string
import random
from django.db import transaction

class Book(models.Model):
    class Rating(models.TextChoices):
        SUPERB = 'superb', _('Superb')
        EXCELLENT = 'excellent', _('Excellent')
        GOOD = 'good', _('Good')
        FAIR = 'fair', _('Fair')
        POOR = 'poor', _('Poor')
        DAMAGED = 'damaged', _('Damaged')
        UNRATED = 'unrated', _('Unrated')

    class BookStatus(models.TextChoices):
        SOLD = 'sold', _('Sold')
        RESERVED = 'reserved', _('Reserved')
        AVAILABLE = 'available', _('Available')
        PROCESSING = 'processing', _('Processing')

    book_id = models.CharField(max_length=8, validators=[MinLengthValidator(8)], primary_key=True, editable=False)
    title = models.CharField(max_length=500, verbose_name= _('Book title'))
    cost = models.DecimalField(max_digits=11, decimal_places=2, verbose_name= _('Book cost'))
    retail_price = models.DecimalField(max_digits=11, decimal_places=2, verbose_name= _('Suggested retail price'))
    publication_date = models.DateField(validators=[MinValueValidator(date(1500,1,1)), MaxValueValidator(date(2099,12,31))], verbose_name= _('Publication Date'))
    edition = models.CharField(max_length=50, blank=True, null=True, default='N/A', verbose_name= _('Book edition'))
    rating = models.CharField(max_length=10, choices=Rating.choices, default=Rating.UNRATED, verbose_name= _('Visible book condition'))
    authors = models.ManyToManyField(Author, related_name='books', verbose_name= _('Book author(s)'), editable=True)
    book_status = models.CharField(max_length=10, choices=BookStatus.choices, default=BookStatus.PROCESSING)
    
    def generate_pk(self):
        try:
            first_author = self.authors.order_by('last_name').first()
            base_name = first_author.last_name if first_author else 'unknown'
        except AttributeError:
            base_name = 'unkown'

        base = (base_name[:4].lower() + 'xxxx')[:4]
        digits = ''.join(random.choices(string.digits, k=4))
        candidate = f'{base}{digits}'

        attempts = 0
        max_attempts = 100
        
        while Book.objects.filter(book_id=candidate).exists():
            if attempts >= max_attempts:
                raise ValueError('Unable to generate a unique primary key.')
            digits = ''.join(random.choices(string.digits, k=4))
            candidate = f'{base}{digits}'
            attempts += 1
        
        return candidate

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if not self.book_id:
                if not self.pk and not self.authors.exists():
                    super().save(*args, **kwargs)
                self.book_id = self.generate_pk()
                super().save(*args, **kwargs)
            else:
                super().save()(*args, **kwargs)
                 
    def __str__(self):
        return f"{self.book_id}: {self.title}"

class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    last_name = models.CharField(max_length=100, blank=True, null=True, verbose_name= _('Customer last name'))
    first_name = models.CharField(max_length=100, blank=True, null=True, verbose_name= _('Customer first name'))
    phone_number = models.CharField(max_length=25, blank=True, null=True, verbose_name= _('Customer phone number'))
    mailing_address = models.CharField(max_length=50, blank=True, null=True, verbose_name= _('Customer mailing address'))
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(first_name__isnull=False) | models.Q(last_name__isnull=False), name='name_required')
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
    customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name= _('Customer id for order'))
    employee_id = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name= _('Employee id for order'))
    order_date = models.DateField(auto_now_add=True, editable=True, verbose_name= _('Date when order was placed'))
    delivery_pickup_date = models.DateField(null=True, blank=True)
    sale_amount = models.DecimalField(max_digits=11, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices)
    order_status = models.CharField(max_length=30, choices=OrderStatus.choices, default=OrderStatus.PICKUP)
    books = models.ManyToManyField(Book, related_name='orders')
    
    def completed_order(self):
        for book in self.books.all():
            book.book_status = 'sold'
            book.save()
        self.delivery_pickup_date = date.today()
        if self.order_status == Order.OrderStatus.TO_SHIP:
            self.order_status = Order.OrderStatus.SHIPPED
        else:
            self.order_status = Order.OrderStatus.PICKED_UP
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
        if instance.role_id.title == 'Owner':
            group_name = 'OwnerGroup'
        elif instance.role_id.title == 'Assistant Manager':
            group_name = 'ManagerGroup'
        group, _ = Group.objects.get_or_create(name=group_name)
        instance.user.groups.add(group)