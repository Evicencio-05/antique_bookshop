import logging
from datetime import date

from django.contrib.auth.models import Group, User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class GroupProfile(models.Model):
    group = models.OneToOneField(
        Group, on_delete=models.CASCADE, primary_key=True, related_name="profile"
    )
    description = models.TextField(
        verbose_name=_("description"),
        max_length=500,
        blank=True,
        null=True,
        help_text=_("Role description"),
    )

    def __str__(self):
        return f"Profile: {self.group.name}"


class Employee(models.Model):
    employee_id = models.AutoField(primary_key=True)
    first_name = models.CharField(
        max_length=50, editable=True, verbose_name=_("Employee first name")
    )
    last_name = models.CharField(max_length=50, editable=True, verbose_name=_("Employee last name"))
    phone_number = models.CharField(
        max_length=50, editable=True, verbose_name=_("Employee phone number")
    )
    address = models.CharField(max_length=200, editable=True, verbose_name=_("Employee address"))
    secondary_address = models.CharField(
        max_length=200,
        blank=True,
        editable=True,
        null=True,
        default="N/A",
        verbose_name=_("Employee secondary address"),
    )
    birth_date = models.DateField(
        auto_now_add=False,
        editable=True,
        verbose_name=_("Employee date of birth"),
        default=date(1600, 1, 1),
    )
    hire_date = models.DateField(
        default=timezone.now, editable=True, verbose_name=_("Employee hire date")
    )
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, editable=True, verbose_name=_("Employee role")
    )
    zip_code = models.CharField(max_length=50, editable=True, verbose_name=_("Employee zip code"))
    state = models.CharField(max_length=50, editable=True, verbose_name=_("Employee state"))
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, editable=True, blank=True, verbose_name=_("Employee user")
    )
    email = models.EmailField(
        max_length=254,
        editable=True,
        verbose_name=_("Employee email"),
        unique=True,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        # Ensure legacy NOT NULL columns have safe defaults
        if not self.secondary_address:
            self.secondary_address = "N/A"
        super().save(*args, **kwargs)
        if self.user:  # Auto-sync on save if User exists (e.g., for updates)
            self.sync_user()

    def _generate_username(self):
        """Generate a unique username based on first and last name."""
        base_username = f"{self.first_name.lower()}.{self.last_name.lower()}"
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        return username

    def sync_user(self, commit=True):
        """Sync non-password fields from Employee to linked User.
        Username policy:
        - Preserve custom usernames that don't contain a dot (e.g., "testuser").
        - If the current username contains a dot (pattern-like), update it to the new base pattern (first.last) while ensuring uniqueness, excluding the current user from collision checks.
        """
        if not self.user:
            raise ValueError("No linked User to sync.")
        self.user.first_name = self.first_name
        self.user.last_name = self.last_name
        self.user.email = self.email or ""

        base_username = f"{self.first_name.lower()}.{self.last_name.lower()}"
        current_username = self.user.username or ""
        if "." in current_username:
            # Recompute expected unique username, excluding current user
            expected = base_username
            counter = 1
            while User.objects.filter(username=expected).exclude(pk=self.user.pk).exists():
                expected = f"{base_username}{counter}"
                counter += 1
            if current_username != expected:
                self.user.username = expected
        # else: keep custom username without dot

        self.user.groups.clear()
        self.user.groups.add(self.group)

        if commit:
            self.user.save()

    def set_password(self, password):
        """Set password on linked User (for updates)."""
        if not self.user:
            raise ValueError("No linked User to set password.")
        self.user.set_password(password)
        self.user.save()

    @classmethod
    def create_with_user(cls, password, **kwargs):
        """
        Classmethod for creating Employee with a new User (non-form use).
        Usage: Employee.create_with_user(password='secret', first_name='John', last_name='Doe', ...)
        Note: This is for scripts/shell; forms are preferred for web apps due to validation.
        """
        if not password:
            raise ValueError("Password is required for creation.")
        first_name = kwargs.get("first_name")
        last_name = kwargs.get("last_name")
        email = kwargs.get("email")
        group = kwargs.get("group")

        if not (first_name and last_name):
            raise ValueError("First and last name are required.")
        if not group:
            raise ValueError("Group is required for employee creation.")

        # Ensure secondary_address is non-null for legacy schema
        if not kwargs.get("secondary_address"):
            kwargs["secondary_address"] = "N/A"

        temp_employee = cls(first_name=first_name, last_name=last_name)
        username = temp_employee._generate_username()

        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email or "",
            password=password,
        )
        if group:
            user.groups.add(group)

        # Drop form-only fields if present
        for k in ("password1", "password2"):
            if k in kwargs:
                kwargs.pop(k)

        employee = cls.objects.create(user=user, **kwargs)
        return employee


class Author(models.Model):
    author_id = models.AutoField(primary_key=True)
    last_name = models.CharField(max_length=100, verbose_name=_("Author last name"))
    first_name = models.CharField(
        max_length=100, blank=True, null=True, default="", verbose_name=_("Author first name")
    )
    birth_year = models.SmallIntegerField(
        blank=True, null=True, verbose_name=_("Author birth year")
    )
    death_year = models.SmallIntegerField(
        blank=True, null=True, verbose_name=_("Author death year")
    )
    description = models.TextField(
        max_length=1000, blank=True, null=True, verbose_name=_("Author description")
    )

    def __str__(self):
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts).strip()


class Book(models.Model):
    class Condition(models.TextChoices):
        SUPERB = "superb", _("Superb")
        EXCELLENT = "excellent", _("Excellent")
        GOOD = "good", _("Good")
        FAIR = "fair", _("Fair")
        POOR = "poor", _("Poor")
        DAMAGED = "damaged", _("Damaged")
        UNRATED = "unrated", _("Unrated")

    class BookStatus(models.TextChoices):
        SOLD = "sold", _("Sold")
        RESERVED = "reserved", _("Reserved")
        AVAILABLE = "available", _("Available")
        PROCESSING = "processing", _("Processing")

    book_id = models.AutoField(primary_key=True)
    legacy_id = models.CharField(
        max_length=8, blank=True, null=True, verbose_name=_("Legacy book ID")
    )
    title = models.CharField(max_length=500, verbose_name=_("Book title"), db_index=True)
    cost = models.DecimalField(max_digits=11, decimal_places=2, verbose_name=_("Book cost"))
    authors = models.ManyToManyField(
        Author, related_name="books", verbose_name=_("Book author(s)"), editable=True
    )
    suggested_retail_price = models.DecimalField(
        max_digits=11, decimal_places=2, verbose_name=_("Suggested retail price")
    )
    condition = models.CharField(
        max_length=10,
        choices=Condition.choices,
        default=Condition.UNRATED,
        verbose_name=_("Visible book condition"),
    )
    condition_notes = models.TextField(
        max_length=1000, blank=True, null=True, verbose_name=_("Condition notes")
    )
    publication_date = models.DateField(
        blank=True,
        null=True,
        validators=[MinValueValidator(date(1600, 1, 1)), MaxValueValidator(date(2099, 12, 31))],
        verbose_name=_("Publication Date"),
    )
    publisher = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_("Book publisher")
    )
    edition = models.CharField(
        max_length=50, blank=True, null=True, default="N/A", verbose_name=_("Book edition")
    )
    book_status = models.CharField(
        max_length=10, choices=BookStatus.choices, default=BookStatus.PROCESSING
    )

    def __str__(self):
        return f"{self.legacy_id or self.book_id}: {self.title}"


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    last_name = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_("Customer last name")
    )
    first_name = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_("Customer first name")
    )
    phone_number = models.CharField(
        max_length=25, blank=True, null=True, verbose_name=_("Customer phone number")
    )
    mailing_address = models.CharField(
        max_length=50, blank=True, null=True, verbose_name=_("Customer mailing address")
    )
    secondary_mailing_address = models.CharField(
        max_length=200,
        blank=True,
        editable=True,
        default="N/A",
        verbose_name=_("Customer secondary address"),
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(first_name__isnull=False) | models.Q(last_name__isnull=False),
                name="name_required",
            )
        ]

    def __str__(self):
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts).strip()


class Order(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = "cash", _("Cash")
        CHECK = "check", _("Check")
        CREDIT = "credit", _("Credit Card")
        OTHER = "other", _("Other")

    class OrderStatus(models.TextChoices):
        TO_SHIP = "to_ship", _("To Be Shipped")
        PICKUP = "pickup", _("Customer Will Pick Up")
        SHIPPED = "shipped", _("Shipped")
        PICKED_UP = "picked_up", _("Picked Up")

    order_id = models.AutoField(primary_key=True)
    customer_id = models.ForeignKey(
        Customer, on_delete=models.CASCADE, verbose_name=_("Customer id for order")
    )
    employee_id = models.ForeignKey(
        Employee, on_delete=models.CASCADE, verbose_name=_("Employee id for order")
    )
    order_date = models.DateField(
        auto_now_add=True, editable=True, verbose_name=_("Date when order was placed")
    )
    delivery_pickup_date = models.DateField(null=True, blank=True)
    sale_amount = models.DecimalField(max_digits=11, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=11, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices)
    order_status = models.CharField(
        max_length=30, choices=OrderStatus.choices, default=OrderStatus.PICKUP
    )
    books = models.ManyToManyField(Book, related_name="orders")

    class Meta:
        permissions = [
            ("view_sales_reports", "Can view sales reports"),
            ("view_employee_sales", "Can view employee sales"),
        ]

    def __str__(self):
        return f"Order {self.order_id}: {self.order_status}"

    def save(self, *args, **kwargs):
        from decimal import Decimal

        # Auto-calculate sale_amount from sum of suggested_retail_price minus discount unless explicitly skipped
        if not getattr(self, "_skip_recalc", False):
            try:
                if self.pk and self.books.exists():
                    total = sum(
                        (book.suggested_retail_price for book in self.books.all()), Decimal("0.00")
                    )
                    discount = getattr(self, "discount_amount", Decimal("0.00")) or Decimal("0.00")
                    amount = total - discount
                    if amount < 0:
                        amount = Decimal("0.00")
                    self.sale_amount = amount
            except Exception as e:  # Log unexpected issues rather than swallowing
                logger.exception("Auto-calc sale_amount failed: %s", e)
        super().save(*args, **kwargs)

    def completed_order(self):
        for book in self.books.all():
            book.book_status = "sold"
            book.save()
        self.delivery_pickup_date = date.today()
        if self.order_status == Order.OrderStatus.TO_SHIP:
            self.order_status = Order.OrderStatus.SHIPPED
        else:
            self.order_status = Order.OrderStatus.PICKED_UP
        self.save()
