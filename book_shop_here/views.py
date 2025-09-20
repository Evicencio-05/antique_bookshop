from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from .models import Book, Author, Order, Role
from .forms import BookForm, CustomerForm, RoleForm

@login_required
def book_list(request):
    query = request.GET.get('q')
    books = Book.objects.filter(book_status='available')
    if query:
        books = books.filter(title__icontains=query) | books.filter(book_id__icontains=query)
    return render(request, 'book_shop_here/book_list.html', {'books': books, 'query': query})
    
@login_required
@permission_required('book_shop_here.add_book')
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book added.')
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'book_shop_here/book_form.html', {'form': form, 'title': 'Add Book'})

@login_required
def role_list(request):
    roles = Role.objects.all()
    return render(request, 'book_shop_here/role_list.html', {'roles': roles})

@login_required
@permission_required('book_shop_here.add_role')
def add_role(request):
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Role added successfully.')
            return redirect('role_list')
    else:
        form = RoleForm()
    return render(request, 'book_shop_here/role_form.html', {'form': form})