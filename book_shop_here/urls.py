from django.urls import path
from . import views

app_name = 'book_shop_here'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('books/', views.BookListView.as_view(), name='book-list'),
    path('books/add/', views.BookCreateView.as_view(), name='book-create'),
    path('books/delete/<str:pk>/', views.BookDeleteView.as_view(), name='book-delete'),
    path('groups/', views.GroupListView.as_view(), name='group-list'),
    path('groups/add/', views.GroupCreateView.as_view(), name='group-create'),
    path('authors/', views.AuthorListView.as_view(), name='author-list'),
    path('authors/add/', views.AuthorCreateView.as_view(), name='author-create'),
    path('orders/', views.OrderListView.as_view(), name='order-list'),
    path('orders/add/', views.OrderCreateView.as_view(), name='order-create'),
    path('employees/', views.EmployeeListView.as_view(), name='employee-list'),
    path('employees/add/', views.EmployeeCreateView.as_view(), name='employee-create'),
    path('employees/edit/<int:pk>/', views.EmployeeUpdateView.as_view(), name='employee-update'),
    path('employees/delete/<int:pk>/', views.EmployeeDeleteView.as_view(), name='employee-delete'),
]