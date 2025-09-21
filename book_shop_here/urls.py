from django.urls import path
from . import views

urlpatterns = [
    path('', views.book_list, name='book_list'),
    path('add_book/', views.add_book, name='add_book'),
    path('roles/', views.role_list, name='role_list'),
    path('roles/add/', views.add_role, name='add_role'),
    path('authors/', views.author_list, name='author_list'),
    path('authors/add', views.add_author, name='add_author'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/add', views.add_order, name='add_order'),
]