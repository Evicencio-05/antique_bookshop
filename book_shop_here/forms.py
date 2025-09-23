from django import forms
from .models import Book, Customer, Role, Author, Order

class BookForm(forms.ModelForm):
    authors = forms.ModelMultipleChoiceField(
        queryset=Author.objects.order_by('last_name'),
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Book
        fields = '__all__'

    def clean_authors(self):
        authors = self.cleaned_data['authors']
        if not authors:
            raise forms.ValidationError('Must select at least one author.')
        return authors        

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