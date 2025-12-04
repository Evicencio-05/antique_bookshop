from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .unified_import import unified_import_process, unified_import_upload
from .views import authors as views_authors
from .views import base as views_base
from .views import books as views_books
from .views import customers as views_customers
from .views import employees as views_employees
from .views import groups as views_groups
from .views import orders as views_orders
from .views import reports as views_reports
from .views import setup as views_setup
from .views import setup_simple as views_setup_simple
from .views import test as views_test

app_name = "book_shop_here"

urlpatterns = [
    path("", views_base.HomeView.as_view(), name="home"),
    path("login/", LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("docs/", views_base.DocsView.as_view(), name="docs"),
    path("reports/sales/", views_reports.SalesDashboardView.as_view(), name="sales-dashboard"),
    path("books/", views_books.BookListView.as_view(), name="book-list"),
    path("books/add/", views_books.BookCreateView.as_view(), name="book-create"),
    path("books/<int:pk>/", views_books.BookDetailView.as_view(), name="book-detail"),
    path("books/edit/<int:pk>/", views_books.BookUpdateView.as_view(), name="book-update"),
    path("books/delete/<int:pk>/", views_books.BookDeleteView.as_view(), name="book-delete"),
    path("groups/", views_groups.GroupListView.as_view(), name="group-list"),
    path("groups/add/", views_groups.GroupCreateView.as_view(), name="group-create"),
    path("groups/<int:pk>/", views_groups.GroupDetailView.as_view(), name="group-detail"),
    path("groups/edit/<int:pk>/", views_groups.GroupUpdateView.as_view(), name="group-update"),
    path("groups/delete/<int:pk>/", views_groups.GroupDeleteView.as_view(), name="group-delete"),
    path("authors/", views_authors.AuthorListView.as_view(), name="author-list"),
    path("authors/add/", views_authors.AuthorCreateView.as_view(), name="author-create"),
    path("authors/<int:pk>/", views_authors.AuthorDetailView.as_view(), name="author-detail"),
    path("authors/edit/<int:pk>/", views_authors.AuthorUpdateView.as_view(), name="author-update"),
    path(
        "authors/delete/<int:pk>/", views_authors.AuthorDeleteView.as_view(), name="author-delete"
    ),
    path("orders/", views_orders.OrderListView.as_view(), name="order-list"),
    path("orders/add/", views_orders.OrderCreateView.as_view(), name="order-create"),
    path("orders/<int:pk>/", views_orders.OrderDetailView.as_view(), name="order-detail"),
    path("orders/edit/<int:pk>/", views_orders.OrderUpdateView.as_view(), name="order-update"),
    path("orders/delete/<int:pk>/", views_orders.OrderDeleteView.as_view(), name="order-delete"),
    path("orders/close/<int:pk>/", views_orders.OrderCloseView.as_view(), name="order-close"),
    path("employees/", views_employees.EmployeeListView.as_view(), name="employee-list"),
    path("employees/add/", views_employees.EmployeeCreateView.as_view(), name="employee-create"),
    path(
        "employees/<int:pk>/", views_employees.EmployeeDetailView.as_view(), name="employee-detail"
    ),
    path(
        "employees/<int:pk>/sales/",
        views_reports.EmployeeSalesView.as_view(),
        name="employee-sales",
    ),
    path(
        "employees/edit/<int:pk>/",
        views_employees.EmployeeUpdateView.as_view(),
        name="employee-update",
    ),
    path(
        "employees/delete/<int:pk>/",
        views_employees.EmployeeDeleteView.as_view(),
        name="employee-delete",
    ),
    path("customers/", views_customers.CustomerListView.as_view(), name="customer-list"),
    path("customers/add/", views_customers.CustomerCreateView.as_view(), name="customer-create"),
    path(
        "customers/<int:pk>/", views_customers.CustomerDetailView.as_view(), name="customer-detail"
    ),
    path(
        "customers/edit/<int:pk>/",
        views_customers.CustomerUpdateView.as_view(),
        name="customer-update",
    ),
    path(
        "customers/delete/<int:pk>/",
        views_customers.CustomerDeleteView.as_view(),
        name="customer-delete",
    ),
    # Unified import endpoints (XLSX, CSV, XML) - handles all file formats
    path("import/upload/", unified_import_upload, name="import-upload"),
    path("import/process/", unified_import_process, name="import-process"),
    # Temporary setup endpoints - remove after initial deployment
    path("setup/superuser/", views_setup.create_initial_superuser, name="create-superuser"),
    path("setup/", views_setup_simple.create_super_user_get, name="setup-simple"),
    path("test/", views_test.simple_test, name="test"),
]
