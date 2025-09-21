from django import forms
from .models import Book, Customer, Role, Author, Order

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = '__all__'
        widgets = {
            'authors': forms.SelectMultiple(attrs={'placeholder': 'Select Options'})
        }

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('first_name') and not cleaned_data.get('last_name'):
            raise forms.ValidationError("At least one name is required.")
        return cleaned_data

class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['title', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Brief job duties (optional)...'}),
        }

class AuthorForm(forms.ModelForm):
    
    class Meta:
        model = Author
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Brief author description (optional)...'}),
        }

class OrderForm(forms.ModelForm):
    
    class Meta:
        model = Order
        fields = '__all__'