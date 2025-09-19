from django.contrib import admin
from models import Role, Author, Book, Employee, Customer, Order

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['title', 'description']

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'birth_year', 'death_year']

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['book_id', 'title', 'retail_price', 'rating', 'book_status']
    list_filter = ['rating', 'book_status']
    filter_horizontal = ['authors']

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'position_id', 'hire_date']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'phone_number']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'customer_id', 'employee_id', 'sale_amount', 'status', 'order_date']
    list_filter = ['status', 'payment_method', 'order_date']
    filter_horizontal = ['books']
    actions = ['complete_order']

    def complete_order(self, request, queryset):
        for order in queryset:
            order.complete_order()
        self.message_user(request, "Selected orders completed.")
    complete_order.short_description = "Complete selected orders"