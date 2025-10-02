from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.contrib import messages
from django.views.generic import ListView, CreateView, TemplateView, DeleteView, UpdateView
from django.urls import reverse_lazy
from .models import Book, Author, Order, Employee, Customer
from .forms import BookForm, CustomerForm, AuthorForm, OrderForm, GroupForm, EmployeeForm
import logging

logger = logging.getLogger(__name__)

class HomeView(TemplateView):
    template_name = 'book_shop_here/home.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('book_shop_here:book-list')
        return super().get(request, *args, **kwargs)

class BookListView(LoginRequiredMixin, ListView):
    model = Book
    template_name = 'book_shop_here/book_list.html'
    context_object_name = 'books'

    def get_queryset(self):
        queryset = Book.objects.filter(book_status='available').prefetch_related('authors')
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(title__icontains=query) | queryset.filter(legacy_id__icontains=query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context

class BookCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = 'book_shop_here/book_form.html'
    success_url = reverse_lazy('book_shop_here:book-list')
    permission_required = 'book_shop_here.add_book'
    raise_exception = True

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Book added.')
            return response
        except Exception as e:
            logger.error(f"Error adding book: {e}")
            messages.error(self.request, 'Failed to add book.')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Book'
        return context

class BookUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'book_shop_here/book_form.html'
    success_url = reverse_lazy('book_shop_here:book-list')
    permission_required = 'book_shop_here.change_book'
    raise_exception = True

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Book updated.')
            return response
        except Exception as e:
            logger.error(f"Error updating book: {e}")
            messages.error(self.request, 'Failed to update book.')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Book'
        return context

class BookDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Book
    template_name = 'book_shop_here/book_delete_confirm.html'
    success_url = reverse_lazy('book_shop_here:book-list')
    permission_required = 'book_shop_here.delete_book'
    raise_exception = True

    # Resolve object by legacy_id passed as 'pk' in URL
    def get_object(self, queryset=None):
        return get_object_or_404(Book, legacy_id=self.kwargs['pk'])

    def post(self, request, *args, **kwargs):
        # If the legacy_id doesn't exist, treat as no-op and redirect
        try:
            self.object = self.get_object()
        except Exception:
            messages.warning(request, 'Book not found; nothing to delete.')
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            messages.success(self.request, 'Book removed.')
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error deleting book: {e}")
            messages.error(self.request, 'Failed to delete book.')
            return self.form_invalid(form)

class AuthorListView(LoginRequiredMixin, ListView):
    model = Author
    template_name = 'book_shop_here/author_list.html'
    context_object_name = 'authors'

class AuthorCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Author
    form_class = AuthorForm
    template_name = 'book_shop_here/author_form.html'
    success_url = reverse_lazy('book_shop_here:author-list')
    permission_required = 'book_shop_here.add_author'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Author'
        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Author added successfully.')
            return response
        except Exception as e:
            logger.error(f"Error adding author: {e}")
            messages.error(self.request, 'Failed to add author.')
            return self.form_invalid(form)

class AuthorUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Author
    form_class = AuthorForm
    template_name = 'book_shop_here/author_form.html'
    success_url = reverse_lazy('book_shop_here:author-list')
    permission_required = 'book_shop_here.change_author'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Author'
        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Author updated successfully.')
            return response
        except Exception as e:
            logger.error(f"Error updating author: {e}")
            messages.error(self.request, 'Failed to update author.')
            return self.form_invalid(form)

class AuthorDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Author
    template_name = 'book_shop_here/author_delete_confirm.html'
    success_url = reverse_lazy('book_shop_here:author-list')
    permission_required = 'book_shop_here.delete_author'
    raise_exception = True

    def form_valid(self, form):
        try:
            messages.success(self.request, 'Author removed.')
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error deleting author: {e}")
            messages.error(self.request, 'Failed to delete author.')
            return self.form_invalid(form)

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'book_shop_here/order_list.html'
    context_object_name = 'orders'

class OrderCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'book_shop_here/order_form.html'
    success_url = reverse_lazy('book_shop_here:order-list')
    permission_required = 'book_shop_here.add_order'
    raise_exception = True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method in ('POST', 'PUT'):
            data = self.request.POST.copy()
            if 'books' in data:
                values = data.getlist('books')
                mapped = []
                for v in values:
                    if v.isdigit():
                        mapped.append(v)
                    else:
                        try:
                            from .models import Book
                            b = Book.objects.get(legacy_id=v)
                            mapped.append(str(b.pk))
                        except Book.DoesNotExist:
                            mapped.append(v)
                data.setlist('books', mapped)
            kwargs['data'] = data
        return kwargs

    def form_valid(self, form):
        try:
            # Save without triggering auto-recalc (respect posted sale_amount)
            obj = form.save(commit=False)
            setattr(obj, '_skip_recalc', True)
            obj.save()
            form.save_m2m()
            self.object = obj
            messages.success(self.request, 'Order added successfully.')
            return redirect(self.success_url)
        except Exception as e:
            logger.error(f"Error adding order: {e}")
            messages.error(self.request, 'Failed to add order.')
            return self.form_invalid(form)

class OrderUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = 'book_shop_here/order_form.html'
    success_url = reverse_lazy('book_shop_here:order-list')
    permission_required = 'book_shop_here.change_order'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Order'
        return context

    def form_valid(self, form):
        try:
            obj = form.save(commit=False)
            setattr(obj, '_skip_recalc', True)
            obj.save()
            form.save_m2m()
            self.object = obj
            messages.success(self.request, 'Order updated successfully.')
            return redirect(self.success_url)
        except Exception as e:
            logger.error(f"Error updating order: {e}")
            messages.error(self.request, 'Failed to update order.')
            return self.form_invalid(form)

class OrderDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Order
    template_name = 'book_shop_here/order_delete_confirm.html'
    success_url = reverse_lazy('book_shop_here:order-list')
    permission_required = 'book_shop_here.delete_order'
    raise_exception = True

    def form_valid(self, form):
        try:
            messages.success(self.request, 'Order removed.')
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error deleting order: {e}")
            messages.error(self.request, 'Failed to delete order.')
            return self

class GroupListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = 'book_shop_here/group_list.html'
    context_object_name = 'groups'

    def get_queryset(self):
        return Group.objects.all().select_related('profile').order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        # Provide helper display data with base names (strip anything after first ' (')
        display = []
        for g in context['groups']:
            name = g.name
            base = name.split(' (')[0]
            desc = getattr(getattr(g, 'profile', None), 'description', '') or '-'
            display.append({'name': name, 'base_name': base, 'description': desc, 'id': g.id})
        context['groups_display'] = display
        return context

class GroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'book_shop_here/group_form.html'
    success_url = reverse_lazy('book_shop_here:group-list')
    permission_required = 'auth.add_group'
    raise_exception = True

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Group added successfully.')
            return response
        except Exception as e:
            logger.error(f"Error adding group: {e}")
            messages.error(self.request, 'Failed to add group.')
            return self.form_invalid(form)

class GroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'book_shop_here/group_form.html'
    success_url = reverse_lazy('book_shop_here:group-list')
    permission_required = 'auth.change_group'
    raise_exception = True

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Group updated successfully.')
            return response
        except Exception as e:
            logger.error(f"Error updating group: {e}")
            messages.error(self.request, 'Failed to update group.')
            return self.form_invalid(form)

class GroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Group
    template_name = 'book_shop_here/group_delete_confirm.html'
    success_url = reverse_lazy('book_shop_here:group-list')
    permission_required = 'auth.delete_group'
    raise_exception = True

    def form_valid(self, form):
        try:
            messages.success(self.request, 'Group removed.')
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error deleting group: {e}")
            messages.error(self.request, 'Failed to delete group.')
            return self.form_invalid(form)

class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'book_shop_here/employee_list.html'
    context_object_name = 'employees'

class EmployeeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'book_shop_here/employee_form.html'
    success_url = reverse_lazy('book_shop_here:employee-list')
    permission_required = 'book_shop_here.add_employee'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Employee'
        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Employee added successfully.')
            return response
        except Exception as e:
            logger.error(f"Error adding employee: {e}")
            messages.error(self.request, 'Failed to add employee.')
            return self.form_invalid(form)

class EmployeeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'book_shop_here/employee_form.html'
    success_url = reverse_lazy('book_shop_here:employee-list')
    permission_required = 'book_shop_here.change_employee'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Employee'
        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Employee updated successfully.')
            return response
        except Exception as e:
            logger.error(f"Error updating employee: {e}")
            messages.error(self.request, 'Failed to update employee.')
            return self.form_invalid(form)

class EmployeeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Employee
    template_name = 'book_shop_here/employee_delete_confirm.html'
    success_url = reverse_lazy('book_shop_here:employee-list')
    permission_required = 'book_shop_here.delete_employee'
    raise_exception = True

    def form_valid(self, form):
        try:
            messages.success(self.request, 'Employee removed.')
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error deleting employee: {e}")
            messages.error(self.request, 'Failed to delete employee.')
            return self.form_invalid(form)

class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'book_shop_here/customer_list.html'
    context_object_name = 'customers'

class CustomerCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'book_shop_here/customer_form.html'
    success_url = reverse_lazy('book_shop_here:customer-list')
    permission_required = 'book_shop_here.add_customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Customer'
        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Customer added successfully.')
            return response
        except Exception as e:
            logger.error(f"Error adding customer: {e}")
            messages.error(self.request, 'Failed to add customer.')
            return self.form_invalid(form)

class CustomerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'book_shop_here/customer_form.html'
    success_url = reverse_lazy('book_shop_here:customer-list')
    permission_required = 'book_shop_here.change_customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Customer'
        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Customer updated successfully.')
            return response
        except Exception as e:
            logger.error(f"Error updating customer: {e}")
            messages.error(self.request, 'Failed to update customer.')
            return self.form_invalid(form)

class CustomerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Customer
    template_name = 'book_shop_here/customer_delete_confirm.html'
    success_url = reverse_lazy('book_shop_here:customer-list')
    permission_required = 'book_shop_here.delete_customer'

    def form_valid(self, form):
        try:
            messages.success(self.request, 'Customer removed.')
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error deleting customer: {e}")
            messages.error(self.request, 'Failed to delete customer.')
            return self.form_invalid(form)