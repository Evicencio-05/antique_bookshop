from django import forms
from django.contrib.auth.models import Group, Permission
from .models import Book, Customer, Author, Order, GroupProfile

class BookForm(forms.ModelForm):
    authors = forms.ModelMultipleChoiceField(
        queryset=Author.objects.order_by('last_name'),
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Book
        fields = ['title', 'cost', 'retail_price', 'publication_date', 'edition', 'rating', 'authors', 'book_status']

    def clean_authors(self):
        authors = self.cleaned_data['authors']
        if not authors:
            raise forms.ValidationError('Must select at least one author.')
        for author in authors:
            if not author.pk:
                raise forms.ValidationError(f'Author "{author}" is not saved to the database.')
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