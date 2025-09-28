from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from . import views

app_name = 'book_shop_here'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    path('books/', views.BookListView.as_view(), name='book-list'),
    path('books/add/', views.BookCreateView.as_view(), name='book-create'),
    path('books/edit/<int:pk>/', views.BookUpdateView.as_view(), name='book-update'),
    path('books/delete/<int:pk>/', views.BookDeleteView.as_view(), name='book-delete'),
    
    path('groups/', views.GroupListView.as_view(), name='group-list'),
    path('groups/add/', views.GroupCreateView.as_view(), name='group-create'),
    path('groups/edit/<int:pk>/', views.GroupUpdateView.as_view(), name='group-update'),
    path('groups/delete/<int:pk>/', views.GroupDeleteView.as_view(), name='group-delete'),
    
    path('authors/', views.AuthorListView.as_view(), name='author-list'),
    path('authors/add/', views.AuthorCreateView.as_view(), name='author-create'),
    path('authors/edit/<int:pk>/', views.AuthorUpdateView.as_view(), name='author-update'),
    path('authors/delete/<int:pk>/', views.AuthorDeleteView.as_view(), name='author-delete'),
    
    path('orders/', views.OrderListView.as_view(), name='order-list'),
    path('orders/add/', views.OrderCreateView.as_view(), name='order-create'),
    path('orders/edit/<int:pk>/', views.OrderUpdateView.as_view(), name='order-update'),
    path('orders/delete/<int:pk>/', views.OrderDeleteView.as_view(), name='order-delete'),
    
    path('employees/', views.EmployeeListView.as_view(), name='employee-list'),
    path('employees/add/', views.EmployeeCreateView.as_view(), name='employee-create'),
    path('employees/edit/<int:pk>/', views.EmployeeUpdateView.as_view(), name='employee-update'),
    path('employees/delete/<int:pk>/', views.EmployeeDeleteView.as_view(), name='employee-delete'),
    
    path('customers/', views.CustomerListView.as_view(), name='customer-list'),
    path('customers/add/', views.CustomerCreateView.as_view(), name='customer-create'),
    path('customers/edit/<int:pk>/', views.CustomerUpdateView.as_view(), name='customer-update'),
    path('customers/delete/<int:pk>/', views.CustomerDeleteView.as_view(), name='customer-delete'),
]