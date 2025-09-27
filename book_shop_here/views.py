from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group
from django.contrib import messages
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from .models import Book, Author, Order, Employee
from .forms import BookForm, CustomerForm, AuthorForm, OrderForm, GroupForm, EmployeeForm
import logging

logger = logging.getLogger(__name__)

def home(request):
    if request.user.is_authenticated:
        return redirect('book_list')
    return render(request, 'book_shop_here/home.html')

@login_required
def book_list(request):
    query = request.GET.get('q')
    books = Book.objects.filter(book_status='available').prefetch_related('authors')
    if query:
        books = books.filter(title__icontains=query) | books.filter(book_id__icontains=query)
    return render(request, 'book_shop_here/book_list.html', {'books': books, 'query': query})

@login_required
@permission_required('book_shop_here.add_book', raise_exception=True)
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        try:
            if form.is_valid():
                book = form.save(commit=False)
                book.save(form.cleaned_data['authors'])
                form.save_m2m()
                messages.success(request, 'Book added.')
                return redirect('book_list')
        except Exception as e:
            logger.error(f"Error adding book: {e}")
            messages.error(request, 'Failed to add book.')
    else:
        form = BookForm()
    return render(request, 'book_shop_here/book_form.html', {'form': form, 'title': 'Add Book'})

@login_required
@permission_required('book_shop_here.delete_book')
def delete_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    
    if request.method == 'POST':
        try:
            book.delete()
            messages.success(request, 'Book removed.')
            return redirect('book_list')
        except Exception as e:
            logger.error(f"Error deleting book: {e}")
            messages.error(request, 'Failed to delete book.')
        
    return render(request, 'book_shop_here/book_delete_confirm.html', {'book': book})

@login_required
def author_list(request):
    authors = Author.objects.all()
    return render(request, 'book_shop_here/author_list.html', {'authors': authors})

@login_required
@permission_required('book_shop_here.add_author')
def add_author(request):
    if request.method == 'POST':
        form = AuthorForm(request.POST)
        try:
            if form.is_valid():
                form.save()
                messages.success(request, 'Author added successfully.')
                return redirect('author_list')
        except Exception as e:
            logger.error(f"Error adding author: {e}")
            messages.error(request, 'Failed to add author.')
    else:
        form = AuthorForm()
    return render(request, 'book_shop_here/author_form.html', {'form': form})

@login_required
def order_list(request):
    orders = Order.objects.all()
    return render(request, 'book_shop_here/order_list.html', {'orders': orders})

@login_required
@permission_required('book_shop_here.add_order')
def add_order(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        try:
            if form.is_valid():
                form.save()
                messages.success(request, 'Order added successfully.')
                return redirect('order_list')
        except Exception as e:
            logger.error(f"Error adding order: {e}")
            messages.error(request, 'Failed to add order.')
    else:
        form = OrderForm()
    return render(request, 'book_shop_here/order_form.html', {'form': form})

@login_required
def group_list(request):
    groups = Group.objects.all().select_related('profile').order_by('name')
    return render(request, 'book_shop_here/group_list.html', {'groups': groups})

@login_required
@permission_required('book_shop_here.add_group')
def add_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        try:
            if form.is_valid():
                form.save()
                messages.success(request, 'Group added successfully.')
                return redirect('group_list')
        except Exception as e:
            logger.error(f"Error adding group: {e}")
            messages.error(request, 'Failed to add group.')
    else:
        form = GroupForm()
        
    return render(request, 'book_shop_here/group_form.html', {'form': form})

class EmployeeListView(ListView):
    model = Employee
    template_name = 'book_shop_here/employee_list.html'
    context_object_name = 'employees'

@login_required
@permission_required('book_shop_here.add_employee', raise_exception=True)
class EmployeeCreateView(CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'book_shop_here/employee_form.html'
    success_url = reverse_lazy('employee_list')

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Employee added successfully.')
            return response
        except Exception as e:
            logger.error(f"Error adding employee: {e}")
            messages.error(self.request, 'Failed to add employee.')
            return self.form_invalid(form)