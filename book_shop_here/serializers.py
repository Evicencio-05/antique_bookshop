import logging
from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib.auth.models import Group
from django.db import models
from rest_framework import serializers

from .models import Author, Book, Customer, Employee, Order


class FlexibleIntegerField(serializers.Field):
    """Integer field that accepts empty string/None as None."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("allow_null", True)
        kwargs.setdefault("required", False)
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        if data in (None, ""):
            return None
        try:
            return int(str(data))
        except (ValueError, TypeError):
            raise serializers.ValidationError("A valid integer is required.") from None

    def to_representation(self, value):
        return value


logger = logging.getLogger(__name__)


class BaseImportSerializer(serializers.ModelSerializer):
    """Base serializer with common null value handling"""

    def handle_null_or_empty(self, value, field_name, default=None):
        """Helper method to handle null/empty values consistently"""
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return default
        return value


class AuthorImportSerializer(BaseImportSerializer):
    # Allow flexible inputs for numeric and string fields
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    birth_year = FlexibleIntegerField(required=False)
    death_year = FlexibleIntegerField(required=False)

    class Meta:
        model = Author
        fields = ["last_name", "first_name", "birth_year", "death_year", "description"]
        nullable_fields = ["first_name", "birth_year", "death_year", "description"]

    def validate_last_name(self, value):
        """Ensure last_name is not empty"""
        if not value or (isinstance(value, str) and not value.strip()):
            raise serializers.ValidationError("Author last name is required")
        return value.strip() if isinstance(value, str) else value

    def validate_birth_year(self, value):
        """Handle birth year validation with proper null handling"""
        if value is None or value == "":
            return None
        if value is None:
            return None
        year = int(value)
        if year < 1 or year > date.today().year:
            raise serializers.ValidationError(f"Invalid birth year: {year}")
        return year

    def validate_death_year(self, value):
        """Handle death year validation with proper null handling"""
        if value is None or value == "":
            return None
        if value is None:
            return None
        year = int(value)
        if year < 1 or year > date.today().year + 1:
            raise serializers.ValidationError(f"Invalid death year: {year}")
        return year

    def validate(self, attrs):
        """Cross-field validation and normalization for names"""
        # Normalize first_name to empty string rather than None
        first_name = attrs.get("first_name")
        if first_name is None:
            attrs["first_name"] = ""

        birth_year = attrs.get("birth_year")
        death_year = attrs.get("death_year")

        if birth_year and death_year and death_year < birth_year:
            raise serializers.ValidationError("Death year cannot be before birth year")

        return super().validate(attrs)


class BookImportSerializer(BaseImportSerializer):
    # Override fields to bypass strict choice validation and accept human inputs
    condition = serializers.CharField(required=False, allow_blank=True)
    book_status = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    # Accept author names as strings and handle them
    author_names = serializers.CharField(write_only=True, required=False, allow_blank=True)
    publication_date = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = Book
        fields = [
            "legacy_id",
            "title",
            "cost",
            "suggested_retail_price",
            "condition",
            "condition_notes",
            "publication_date",
            "publisher",
            "edition",
            "book_status",
            "author_names",
        ]
        nullable_fields = [
            "legacy_id",
            "condition_notes",
            "publication_date",
            "publisher",
            "edition",
        ]

    def validate_publication_date(self, value):
        "Ensure proper date format and null handling"
        if value is not None or value != "":
            try:
                pub_date = date.fromisoformat(value)
            except (ValueError, TypeError):
                try:
                    pub_year = int(value)
                    pub_date = date(pub_year, 1, 1)
                except (ValueError, TypeError):
                    raise serializers.ValidationError(
                        f"Publication date must be in YYYY-MM-DD or YYYY format, got: {value}"
                    ) from None
            return pub_date
        return value

    def validate_title(self, value):
        """Ensure title is not empty"""
        if not value or (isinstance(value, str) and not value.strip()):
            raise serializers.ValidationError("Book title is required")
        return value.strip() if isinstance(value, str) else value

    def validate_cost(self, value):
        """Handle cost validation with proper type conversion"""
        if value is None or value == "":
            raise serializers.ValidationError("Cost is required")
        try:
            cost = Decimal(str(value))
            if cost < 0:
                raise serializers.ValidationError("Cost cannot be negative")
            return cost
        except (InvalidOperation, ValueError, TypeError):
            raise serializers.ValidationError(
                f"Cost must be a valid number, got: {value}"
            ) from None

    def validate_suggested_retail_price(self, value):
        """Handle price validation with proper type conversion"""
        if value is None or value == "":
            raise serializers.ValidationError("Suggested retail price is required")
        try:
            price = Decimal(str(value))
            if price < 0:
                raise serializers.ValidationError("Price cannot be negative")
            return price
        except (InvalidOperation, ValueError, TypeError):
            raise serializers.ValidationError(
                f"Suggested retail price must be a valid number, got: {value}"
            ) from None

    def validate_condition(self, value):
        """Validate book condition"""
        if not value:
            return Book.Condition.UNRATED

        # Handle both display names and values
        condition_map = {choice[1].lower(): choice[0] for choice in Book.Condition.choices}
        condition_map.update({choice[0].lower(): choice[0] for choice in Book.Condition.choices})

        value_lower = str(value).lower().strip()
        if value_lower in condition_map:
            return condition_map[value_lower]

        raise serializers.ValidationError(
            f"Invalid condition: {value}. Valid options: {list(condition_map.keys())}"
        )

    def validate_book_status(self, value):
        """Validate book status"""
        if not value:
            return Book.BookStatus.AVAILABLE

        # Handle both display names and values
        status_map = {choice[1].lower(): choice[0] for choice in Book.BookStatus.choices}
        status_map.update({choice[0].lower(): choice[0] for choice in Book.BookStatus.choices})

        value_lower = str(value).lower().strip()
        if value_lower in status_map:
            return status_map[value_lower]

        raise serializers.ValidationError(
            f"Invalid book status: {value}. Valid options: {list(status_map.keys())}"
        )

    def create(self, validated_data):
        """Handle author creation/linking during book creation"""
        author_names = validated_data.pop("author_names", "")
        book = super().create(validated_data)

        if author_names:
            self._handle_authors(book, author_names)

        return book

    def _handle_authors(self, book, author_names):
        """Parse author names and create/link authors"""
        if not author_names.strip():
            return

        # Split by common separators
        separators = [";", ",", "&", " and ", "\n"]
        authors = [author_names.strip()]

        for sep in separators:
            new_authors = []
            for author in authors:
                new_authors.extend([a.strip() for a in author.split(sep) if a.strip()])
            authors = new_authors

        for author_name in authors:
            if not author_name:
                continue

            # Parse "Last, First" or "First Last" format
            parts = [p.strip() for p in author_name.split(",")]
            if len(parts) == 2:
                last_name, first_name = parts[0], parts[1]
            else:
                name_parts = author_name.split()
                if len(name_parts) >= 2:
                    first_name = " ".join(name_parts[:-1])
                    last_name = name_parts[-1]
                else:
                    last_name = author_name
                    first_name = ""

            # Get or create author
            author, created = Author.objects.get_or_create(
                last_name=last_name,
                first_name=first_name or "",
                defaults={"first_name": first_name or ""},
            )
            book.authors.add(author)


class CustomerImportSerializer(BaseImportSerializer):
    class Meta:
        model = Customer
        fields = [
            "last_name",
            "first_name",
            "phone_number",
            "mailing_address",
            "secondary_mailing_address",
            "city",
            "state",
            "zip_code",
        ]
        nullable_fields = [
            "last_name",
            "first_name",
            "phone_number",
            "mailing_address",
            "city",
            "state",
            "zip_code",
        ]

    def validate(self, attrs):
        """Ensure at least first or last name is provided"""
        first_name = self.handle_null_or_empty(attrs.get("first_name"), "first_name")
        last_name = self.handle_null_or_empty(attrs.get("last_name"), "last_name")

        if not first_name and not last_name:
            raise serializers.ValidationError("Either first name or last name must be provided")

        attrs["first_name"] = first_name
        attrs["last_name"] = last_name
        return super().validate(attrs)


class EmployeeImportSerializer(BaseImportSerializer):
    group_name = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Employee
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "address",
            "secondary_address",
            "birth_date",
            "hire_date",
            "city",
            "zip_code",
            "state",
            "email",
            "group_name",
        ]
        nullable_fields = ["secondary_address", "email"]

    def validate_first_name(self, value):
        """Ensure first_name is not empty"""
        if not value or (isinstance(value, str) and not value.strip()):
            raise serializers.ValidationError("Employee first name is required")
        return value.strip()

    def validate_last_name(self, value):
        """Ensure last_name is not empty"""
        if not value or (isinstance(value, str) and not value.strip()):
            raise serializers.ValidationError("Employee last name is required")
        return value.strip()

    def validate_email(self, value):
        """Handle email validation with null handling"""
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return value

    def validate_group_name(self, value):
        """Validate that group exists"""
        if not value or not value.strip():
            raise serializers.ValidationError("Group name is required")

        try:
            group = Group.objects.get(name=value.strip())
            return group
        except Group.DoesNotExist:
            raise serializers.ValidationError(f"Group '{value}' does not exist") from None

    def create(self, validated_data):
        """Create Employee with linked User and group assignment.
        - Creates a Django User with an unusable password.
        - Ensures secondary_address has a non-null default string.
        """
        from django.contrib.auth.models import User

        group = validated_data.pop("group_name")
        validated_data["group"] = group

        # Generate a username from first/last name
        first = validated_data.get("first_name", "").strip().lower() or "user"
        last = validated_data.get("last_name", "").strip().lower() or "import"
        base_username = f"{first}.{last}".strip(".") or "import.user"
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Create user with unusable password
        user = User(
            username=username,
            first_name=validated_data.get("first_name", "") or "",
            last_name=validated_data.get("last_name", "") or "",
            email=validated_data.get("email") or "",
        )
        user.set_unusable_password()
        user.save()
        user.groups.add(group)

        # Ensure non-null secondary_address for legacy NOT NULL schema
        if not validated_data.get("secondary_address"):
            validated_data["secondary_address"] = "N/A"

        validated_data["user"] = user
        return super().create(validated_data)


class OrderImportSerializer(BaseImportSerializer):
    customer_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    employee_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    book_titles = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Order
        fields = [
            "customer_name",
            "employee_name",
            "order_date",
            "delivery_pickup_date",
            "sale_amount",
            "discount_amount",
            "payment_method",
            "order_status",
            "book_titles",
        ]
        nullable_fields = ["delivery_pickup_date"]

    def validate_payment_method(self, value):
        """Validate payment method"""
        if not value:
            raise serializers.ValidationError("Payment method is required")

        # Handle both display names and values
        method_map = {choice[1].lower(): choice[0] for choice in Order.PaymentMethod.choices}
        method_map.update({choice[0].lower(): choice[0] for choice in Order.PaymentMethod.choices})

        value_lower = str(value).lower().strip()
        if value_lower in method_map:
            return method_map[value_lower]

        raise serializers.ValidationError(f"Invalid payment method: {value}")

    def validate_order_status(self, value):
        """Validate order status"""
        if not value:
            return Order.OrderStatus.PICKUP

        # Handle both display names and values
        status_map = {choice[1].lower(): choice[0] for choice in Order.OrderStatus.choices}
        status_map.update({choice[0].lower(): choice[0] for choice in Order.OrderStatus.choices})

        value_lower = str(value).lower().strip()
        if value_lower in status_map:
            return status_map[value_lower]

        raise serializers.ValidationError(f"Invalid order status: {value}")

    def create(self, validated_data):
        """Handle foreign key lookups and many-to-many relationships"""
        customer_name = validated_data.pop("customer_name", "")
        employee_name = validated_data.pop("employee_name", "")
        book_titles = validated_data.pop("book_titles", "")

        # Find customer
        customer = self._find_customer(customer_name)
        if not customer:
            raise serializers.ValidationError(f"Customer not found: {customer_name}")
        validated_data["customer_id"] = customer

        # Find employee
        employee = self._find_employee(employee_name)
        if not employee:
            raise serializers.ValidationError(f"Employee not found: {employee_name}")
        validated_data["employee_id"] = employee

        order = super().create(validated_data)

        # Handle books
        if book_titles:
            self._handle_books(order, book_titles)

        return order

    def _find_customer(self, name_str):
        """Find customer by name"""
        if not name_str.strip():
            return None

        # Try exact match first
        customers = Customer.objects.filter(
            models.Q(first_name__icontains=name_str) | models.Q(last_name__icontains=name_str)
        )

        if customers.count() == 1:
            return customers.first()
        elif customers.count() > 1:
            # Try more specific matching
            for customer in customers:
                full_name = f"{customer.first_name or ''} {customer.last_name or ''}".strip()
                if full_name.lower() == name_str.lower():
                    return customer

        return customers.first() if customers.exists() else None

    def _find_employee(self, name_str):
        """Find employee by name"""
        if not name_str.strip():
            return None

        employees = Employee.objects.filter(
            models.Q(first_name__icontains=name_str) | models.Q(last_name__icontains=name_str)
        )

        if employees.count() == 1:
            return employees.first()
        elif employees.count() > 1:
            # Try more specific matching
            for employee in employees:
                full_name = f"{employee.first_name} {employee.last_name}".strip()
                if full_name.lower() == name_str.lower():
                    return employee

        return employees.first() if employees.exists() else None

    def _handle_books(self, order, book_titles):
        """Find and link books to order"""
        if not book_titles.strip():
            return

        # Split by common separators
        separators = [";", ",", "\n"]
        titles = [book_titles.strip()]

        for sep in separators:
            new_titles = []
            for title in titles:
                new_titles.extend([t.strip() for t in title.split(sep) if t.strip()])
            titles = new_titles

        for title in titles:
            if not title:
                continue

            # Find book by title or legacy_id
            books = Book.objects.filter(
                models.Q(title__icontains=title) | models.Q(legacy_id=title)
            )

            if books.exists():
                order.books.add(books.first())
            else:
                logger.warning(f"Book not found for order {order.order_id}: {title}")
