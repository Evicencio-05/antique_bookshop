from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator
from django.db import models, transaction, DatabaseError
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.contrib.auth.models import User, Group
from django.utils.translation import gettext_lazy as _
from datetime import date
import logging
import string
import random
import re

logger = logging.getLogger(__name__)

class GroupProfile(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, primary_key=True, related_name='group')
    description = models.TextField(verbose_name= _('description'), max_length=500, blank=True, null=True, help_text= _('Role description'))
    
    def __str__(self):
        return f"Profile: {self.group.name}"

class Employee(models.Model):
    employee_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50, editable=True, verbose_name= _('Employee first name'))
    last_name = models.CharField(max_length=50, editable=True, verbose_name= _('Employee last name'))
    phone_number = models.CharField(max_length=50, editable=True, verbose_name= _('Employee phone number'))
    address = models.CharField(max_length=200, editable=True, verbose_name= _('Employee address'))
    birth_date = models.DateField(auto_now_add=False, editable=True, verbose_name= _('Employee date of birth'), default=date(1600,1,1))
    hire_date = models.DateField(auto_now_add=True, editable=True, verbose_name= _('Employee hire date'))
    group = models.ForeignKey(Group, on_delete=models.CASCADE, editable=True, verbose_name= _('Employee role'))
    zip_code = models.CharField(max_length=50, editable=True, verbose_name= _('Employee zip code'))
    state = models.CharField(max_length=50, editable=True, verbose_name= _('Employee state'))
    user = models.OneToOneField(User, on_delete=models.CASCADE, editable=True, null=True, verbose_name= _('Employee user'))
    email = models.EmailField(max_length=254, editable=True, verbose_name=_('Employee email'), unique=True, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if self.user:
            user = self.user
            
        elif not self.user and self.pk is None:
            try:
                base_username = f"{self.first_name.lower()}{self.last_name.lower()}".replace(' ', '')
                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                user = User.objects.create(
                    username=username,
                    email=self.email or f"{username}@placeholder.com", 
                    first_name=self.first_name,
                    last_name=self.last_name,
                    is_active=True # Set to False if you want to set password later
                )

                self.user = user
                super().save(update_fields=['user'])

            except Exception as e:
                logger.error(f"Failed to create user for employee {self.pk}: {e}")
                # Consider raising an error or handling this more gracefully
                return # Exit save if user creation failed

        if self.user:
            update_fields = []
            if self.user.first_name != self.first_name:
                self.user.first_name = self.first_name
                update_fields.append('first_name')
            if self.user.last_name != self.last_name:
                self.user.last_name = self.last_name
                update_fields.append('last_name')
            if self.user.email != self.email:
                self.user.email = self.email
                update_fields.append('email')
                
            if update_fields:
                self.user.save(update_fields=update_fields)
                
            current_groups = set(self.user.groups.all())
            employee_group = self.group

            if employee_group not in current_groups or len(current_groups) > 1:
                with transaction.atomic():
                    self.user.groups.set([employee_group])
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Author(models.Model):
    author_id = models.AutoField(primary_key=True)
    last_name = models.CharField(max_length=100, verbose_name= _('Author last name'))
    first_name = models.CharField(max_length=100, blank=True, null=True, default='', verbose_name= _('Author first name'))
    birth_year = models.SmallIntegerField(blank=True, null=True, verbose_name= _('Author birth year'))
    death_year = models.SmallIntegerField(blank=True, null=True, verbose_name= _('Author death year'))
    description = models.TextField(max_length=1000, blank=True, null=True, verbose_name= _('Author description'))

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()

def validate_book_id(value):
    if not value:
        raise ValidationError('Book ID cannot be empty.')
    pattern = r"[a-z]{4}[0-9]{4}"
    if not re.search(pattern, value):
        raise ValidationError('Book ID must match pattern: four lowercase letters followed by four digits.')


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

    book_id = models.CharField(max_length=8, validators=[MinLengthValidator(8), validate_book_id], primary_key=True, editable=False)
    title = models.CharField(max_length=500, verbose_name= _('Book title'))
    cost = models.DecimalField(max_digits=11, decimal_places=2, verbose_name= _('Book cost'))
    authors = models.ManyToManyField(Author, related_name='books', verbose_name= _('Book author(s)'), editable=True)
    retail_price = models.DecimalField(max_digits=11, decimal_places=2, verbose_name= _('Suggested retail price'))
    rating = models.CharField(max_length=10, choices=Rating.choices, default=Rating.UNRATED, verbose_name= _('Visible book condition'))
    publication_date = models.DateField(blank=True, null=True, validators=[MinValueValidator(date(1600,1,1)), MaxValueValidator(date(2099,12,31))], verbose_name= _('Publication Date'))
    publisher = models.CharField(max_length=100, blank=True, null=True, verbose_name= _('Book publisher'))
    edition = models.CharField(max_length=50, blank=True, null=True, default='N/A', verbose_name= _('Book edition'))
    book_status = models.CharField(max_length=10, choices=BookStatus.choices, default=BookStatus.PROCESSING)
    
    def generate_pk(self, authors=None):
        try:
            if authors is None:
                first_author = self.authors.all().order_by('last_name').first()
            elif isinstance(authors, QuerySet) or (hasattr(authors, '__iter__') and not isinstance(authors, (str, bytes))):
                first_author = authors.order_by('last_name').first()
            else:
                first_author = authors
                
            base_name = first_author.last_name if first_author and hasattr(first_author, 'last_name') else 'unknown'
        except (AttributeError, DatabaseError):
            base_name = 'unknown'

        base_name = ''.join(c for c in base_name if c.isalpha())[:4].lower()
        base = (base_name[:4].lower() + 'xxxx')[:4]

        attempts = 0
        max_attempts = 1000
        
        with transaction.atomic():
            while True:
                digits = ''.join(random.choices(string.digits, k=4))
                candidate = f'{base}{digits}'
                if not self.__class__.objects.filter(book_id=candidate).exists():
                    return candidate
                attempts += 1
                if attempts >= max_attempts:
                    raise ValueError('Unable to generate a unique book_id after {} attempts.'.format(max_attempts))

    def save(self, authors=None, *args, **kwargs,):
        with transaction.atomic():
            pattern = r"[a-z]{4}[0-9]{4}"
            if not re.search(pattern, self.book_id):
                self.book_id = self.generate_pk(authors)
            super().save(*args, **kwargs)
                
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
    