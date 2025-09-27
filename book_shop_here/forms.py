from django import forms
from django.contrib.auth.models import Group, Permission, User
from .models import Book, Customer, Author, Order, GroupProfile, Employee
from django.core.exceptions import ValidationError

class BookForm(forms.ModelForm):
    authors = forms.ModelMultipleChoiceField(
        queryset=Author.objects.order_by('last_name'),
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Book
        fields = ['title', 'cost', 'retail_price', 'publication_date', 'publisher', 'edition', 'rating', 'authors', 'book_status']

    def clean_authors(self):
        authors = self.cleaned_data['authors']
        if not authors:
            raise forms.ValidationError('Must select at least one author.')
        for author in authors:
            if not author.pk:
                raise forms.ValidationError(f'Author "{author}" is not saved to the database.')
        return authors

import re

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
        
    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('first_name') and not cleaned_data.get('last_name'):
            raise forms.ValidationError("At least one name is required.")
        return cleaned_data
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number and not re.match(r'^\+?1?\d{10,15}$', phone_number):
            raise forms.ValidationError("Enter a valid phone number (10-15 digits, optional +).")
        return phone_number

class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Brief author description (optional)...'}),
        }

class OrderForm(forms.ModelForm):
    books = forms.ModelMultipleChoiceField(
        queryset=Book.objects.filter(book_status__in=['available', 'reserved']),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = Order
        fields = ['customer_id', 'employee_id', 'sale_amount', 'payment_method', 'order_status', 'books', 'delivery_pickup_date']
        

class GroupForm(forms.ModelForm):
    description = forms.CharField(label='Description', widget=forms.Textarea(attrs={'rows': 3}), required=False)
    permissions = forms.ModelMultipleChoiceField(queryset=Permission.objects.filter(content_type__app_label__in=['book_shop_here', 'auth'])
                                                , required=False, widget=forms.CheckboxSelectMultiple, label='Permissions')
    class Meta:
        model = Group
        fields = ('name',) 

    def save(self, commit=True):
        group = super().save(commit=commit)
        
        description = self.cleaned_data.get('description', '')
        
        # Create and save the associated GroupProfile
        if group.pk:
            GroupProfile.objects.update_or_create(
                group=group,
                defaults={'description': description}
            )
        
        selected_permissions = self.cleaned_data.get('permissions', [])
        if selected_permissions:
            group.permissions.set(selected_permissions)
        else:
            group.permissions.clear()
        
        return group
    
class EmployeeForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        required=False,
        help_text="Required for new employees. Leave blank to keep current on updates."
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput,
        required=False,
    )

    class Meta:
        model = Employee
        fields = [
            'first_name', 'last_name', 'phone_number', 'address',
            'birth_date', 'hire_date', 'group', 'zip_code',
            'state', 'email'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        is_creation = self.instance.pk is None

        if is_creation:
            if not password1 or not password2:
                raise ValidationError("Password and confirmation are required for new employees.")

        if password1 or password2:
            if password1 != password2:
                raise ValidationError("Passwords don't match.")

        return cleaned_data
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number and not re.match(r'^\+?1?\d{10,15}$', phone_number):
            raise forms.ValidationError("Enter a valid phone number (10-15 digits, optional +).")
        return phone_number

    def save(self, commit=True):
        employee = super().save(commit=False)
        password1 = self.cleaned_data.get('password1')
        is_creation = employee.pk is None

        if is_creation:
            # Creation: Use model's classmethod for consistency
            # Extract kwargs from cleaned_data (plus instance fields)
            kwargs = self.cleaned_data.copy()
            kwargs['first_name'] = employee.first_name
            kwargs['last_name'] = employee.last_name
            kwargs['email'] = employee.email
            kwargs['group'] = employee.group
            employee = Employee.create_with_user(password=password1, **kwargs)
        else:
            # Update: Save employee (which auto-syncs via model save), then handle password if provided
            if commit:
                employee.save()
            if password1:
                employee.set_password(password1)

        return employee