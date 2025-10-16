import data_wizard
from django.contrib import admin

from .forms import EmployeeForm
from .models import Author, Book, Customer, Employee, GroupProfile, Order
from .serializers import (
    AuthorImportSerializer,
    BookImportSerializer,
    CustomerImportSerializer,
    EmployeeImportSerializer,
    OrderImportSerializer,
)

# Register models with custom serializers for better null value handling
data_wizard.register(Book, serializer=BookImportSerializer)
data_wizard.register(Author, serializer=AuthorImportSerializer)
data_wizard.register(Customer, serializer=CustomerImportSerializer)
data_wizard.register(Employee, serializer=EmployeeImportSerializer)
data_wizard.register(Order, serializer=OrderImportSerializer)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ["author_id", "last_name", "first_name", "birth_year", "death_year"]
    search_fields = ["first_name", "last_name"]
    list_filter = ["birth_year"]


@admin.register(GroupProfile)
class GroupProfileAdmin(admin.ModelAdmin):
    list_display = ["group", "description"]
    search_fields = ["group_name", "description"]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = [
        "book_id",
        "legacy_id",
        "title",
        "suggested_retail_price",
        "condition",
        "book_status",
    ]
    search_fields = ["title", "legacy_id"]
    list_filter = ["condition", "book_status", "publication_date"]
    filter_horizontal = ["authors"]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["employee_id", "last_name", "first_name", "email", "group", "hire_date"]
    search_fields = ["first_name", "last_name", "email", "address", "secondary_address"]
    list_filter = ["group", "hire_date"]
    form = EmployeeForm


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["customer_id", "last_name", "first_name", "phone_number", "mailing_address"]
    search_fields = [
        "first_name",
        "last_name",
        "phone_number",
        "mailing_address",
        "secondary_mailing_address",
        "city",
        "state",
        "zip_code",
    ]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_id",
        "customer_id",
        "employee_id",
        "sale_amount",
        "order_status",
        "order_date",
    ]
    search_fields = [
        "order_id",
        "customer_id__first_name",
        "customer_id__last_name",
        "employee_id__first_name",
        "employee_id__last_name",
    ]
    list_filter = ["order_status", "payment_method", "order_date"]
    filter_horizontal = ["books"]
    actions = ["completed_order"]

    def completed_order(self, request, queryset):
        for order in queryset:
            order.completed_order()
        self.message_user(request, "Selected orders have been completed.")
