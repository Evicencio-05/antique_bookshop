from django.test import TestCase
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from book_shop_here.models import Book, Author, Customer, Employee, GroupProfile
from book_shop_here.forms import BookForm, CustomerForm, AuthorForm, OrderForm, GroupForm, EmployeeForm
from datetime import date
import html
import logging

logging = logging.getLogger(__name__)

class BookFormTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(first_name="John", last_name="Doe")

    def test_book_form_valid(self):
        form_data = {
            "title": "Test Book",
            "cost": 10.00,
            "retail_price": 15.00,
            "publication_date": date(2020, 1, 1),
            "publisher": "Test Publisher",
            "edition": "1st",
            "rating": "excellent",
            "book_status": "available",
            "legacy_id": "doej1234",
            "authors": [self.author.author_id]
        }
        form = BookForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_book_form_no_authors(self):
        form_data = {
            "title": "Test Book",
            "cost": 10.00,
            "retail_price": 15.00,
            "publication_date": date(2020, 1, 1),
            "publisher": "Test Publisher",
            "edition": "1st",
            "rating": "excellent",
            "book_status": "available",
            "legacy_id": "doej1234",
            "authors": []
        }
        form = BookForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("authors", form.errors)

class CustomerFormTests(TestCase):
    def test_customer_form_no_names(self):
        form_data = {"phone_number": "1234567890"}
        form = CustomerForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("At least one name is required.", str(form.errors))

    def test_customer_form_valid(self):
        form_data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "phone_number": "1234567890",
            "mailing_address": "123 St"
        }
        form = CustomerForm(data=form_data)
        self.assertTrue(form.is_valid())

class GroupFormTests(TestCase):
    def setUp(self):
        ct = ContentType.objects.get_for_model(Book)
        self.perm = Permission.objects.create(codename='can_sell_book', name='Can Sell Book', content_type=ct)

    def test_group_creation_form_valid(self):
        form_data = {
            "name": "Manager (GroupForm)",
            "description": "Manages store operations",
            "permissions": [self.perm.pk]
        }
        form = GroupForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        group = form.save()
        self.assertEqual(group.name, "Manager (GroupForm)")
        self.assertTrue(group.permissions.filter(pk=self.perm.pk).exists())
        self.assertTrue(GroupProfile.objects.filter(group=group, description="Manages store operations").exists())

    def test_group_creation_form_no_description_or_permissions(self):
        form_data = {"name": "Clerk (GroupFormNoDescOrPerm)"}
        form = GroupForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        group = form.save()
        self.assertEqual(group.name, "Clerk (GroupFormNoDescOrPerm)")
        self.assertEqual(group.permissions.count(), 0)

class AuthorFormTests(TestCase):
    def test_author_form_valid(self):
        form_data = {
            "first_name": "Jane",
            "last_name": "Austen",
            "birth_year": 1775,
            "description": "Famous novelist"
        }
        form = AuthorForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_author_form_no_first_name(self):
        form_data = {"last_name": "Smith"}
        form = AuthorForm(data=form_data)
        self.assertTrue(form.is_valid())

class OrderFormTests(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Full Time Sales Clerk (OrderForm)")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.employee = Employee.objects.create(
            first_name="Test",
            last_name="Employee",
            address="123 St",
            zip_code="12345",
            state="CA",
            birth_date=date(1990, 1, 1),
            phone_number="1234567890",
            group=self.group,
            user=self.user
        )
        self.customer = Customer.objects.create(first_name="Bob", last_name="Jones")
        self.book = Book.objects.create(
            legacy_id="test1234",
            title="Test Book",
            cost=10.00,
            retail_price=15.00,
            publication_date=date(2020, 1, 1),
            book_status="available"
        )

    def test_order_form_valid(self):
        form_data = {
            "customer_id": self.customer.customer_id,
            "employee_id": self.employee.employee_id,
            "sale_amount": 10.00,
            "payment_method": "cash",
            "order_status": "to_ship",
            "books": [self.book.book_id]
        }
        form = OrderForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_order_form_no_books(self):
        form_data = {
            "customer_id": self.customer.customer_id,
            "employee_id": self.employee.employee_id,
            "sale_amount": 10.00,
            "payment_method": "cash",
            "order_status": "to_ship",
            "books": []
        }
        form = OrderForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("books", form.errors)

class EmployeeFormTests(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Test Group")
        self.form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '1234567890',
            'address': '123 Main St',
            'birth_date': date(1990, 1, 1),
            'hire_date': date.today(),
            'group': self.group.id,
            'zip_code': '12345',
            'state': 'CA',
            'email': 'john.doe@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }

    def test_form_creation_valid(self):
        form = EmployeeForm(data=self.form_data)
        self.assertTrue(form.is_valid())
        employee = form.save()
        self.assertIsNotNone(employee.user)
        self.assertEqual(employee.user.username, 'john.doe')
        self.assertTrue(employee.user.check_password('testpass123'))

    def test_form_creation_no_password(self):
        data = self.form_data.copy()
        form = EmployeeForm(data=data)
        del data['password2']
        del data['password1']
        self.assertFalse(form.is_valid())
        self.assertIn("Password and confirmation are required for new employees.", str(form.errors))

    def test_form_creation_password_mismatch(self):
        data = self.form_data.copy()
        data['password2'] = 'wrongpass'
        form = EmployeeForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn(html.escape("Passwords don't match."), str(form.errors))

    def test_form_update(self):
        employee = Employee.create_with_user(password='oldpass', first_name='John', last_name='Doe', group=self.group, email='john@example.com')
        data = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'phone_number': '1234567890',
            'address': '123 Main St',
            'birth_date': date(1990, 1, 1),
            'hire_date': date.today(),
            'group': self.group.id,
            'zip_code': '12345',
            'state': 'CA',
            'email': 'jane.doe@example.com',
            'password1': '',
            'password2': ''
        }
        form = EmployeeForm(data=data, instance=employee)
        self.assertTrue(form.is_valid())
        updated_employee = form.save()
        updated_employee.user.refresh_from_db()
        self.assertEqual(updated_employee.user.first_name, 'Jane')
        self.assertEqual(updated_employee.user.email, 'jane.doe@example.com')
        self.assertTrue(updated_employee.user.check_password('oldpass'))

    def test_form_update_with_password(self):
        employee = Employee.create_with_user(password='oldpass', first_name='John', last_name='Doe', group=self.group, email='john@example.com')
        data = self.form_data.copy()
        data['first_name'] = 'Jane'
        data['password1'] = 'newpass123'
        data['password2'] = 'newpass123'
        form = EmployeeForm(data=data, instance=employee)
        self.assertTrue(form.is_valid())
        updated_employee = form.save()
        updated_employee.user.refresh_from_db()
        self.assertTrue(updated_employee.user.check_password('newpass123'))
