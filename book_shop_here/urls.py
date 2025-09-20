from django.urls import path
from . import views

urlpatterns = [
    path('', views.book_list, name='book_list'),  # Root within /bookshop/
    path('add_book/', views.add_book, name='add_book'),
    path('roles/', views.role_list, name='role_list'),
    path('roles/add/', views.add_role, name='add_role'),
]