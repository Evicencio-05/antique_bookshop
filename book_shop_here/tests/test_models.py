from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group
from book_shop_here.models import Book, Author, Order, Customer, Employee, GroupProfile
from django.core.exceptions import ValidationError
from datetime import date


class BookModelTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(first_name="John", last_name="Doe")
        self.book = Book.objects.create(
            legacy_id="doej1234",
            title="Test Book",
            cost=10.00,
            retail_price=15.00,
            publication_date=date(2020, 1, 1),
            edition="1st",
            rating="excellent",
            book_status="available"
        )
        self.book.authors.add(self.author)

    def test_book_str(self):
        self.assertEqual(str(self.book), "doej1234: Test Book")
        book_no_legacy = Book.objects.create(title="No Legacy", cost=5.00, retail_price=10.00)
        self.assertEqual(str(book_no_legacy), f"{book_no_legacy.book_id}: No Legacy")

class AuthorModelTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(
            first_name="Jane",
            last_name="Austen",
            birth_year=1775,
            description="Famous novelist"
        )

    def test_author_str(self):
        self.assertEqual(str(self.author), "Jane Austen")

    def test_author_no_first_name(self):
        author = Author.objects.create(last_name="Smith")
        self.assertEqual(str(author), "Smith")

class CustomerModelTests(TestCase):
    def test_customer_name_constraint(self):
        customer = Customer(phone_number="1234567890")
        with self.assertRaises(ValidationError):
            customer.full_clean()

    def test_customer_valid(self):
        customer = Customer(first_name="Alice", last_name="Smith", phone_number="1234567890")
        customer.full_clean()
        self.assertEqual(str(customer), "Alice Smith")

class OrderModelTests(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Full Time Sales Clerk (OrderModel)")
        self.group_profile = GroupProfile.objects.create(group=self.group)
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
        self.order = Order.objects.create(
            sale_amount=15.00,
            payment_method="cash",
            order_status="to_ship"
        )
        self.order.customer_id.add(self.customer)
        self.order.employee_id.add(self.employee)
        self.order.books.add(self.book)

    def test_completed_order(self):
        self.order.completed_order()
        self.book.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.book.book_status, "sold")
        self.assertEqual(self.order.order_status, "shipped")
        self.assertEqual(self.order.delivery_pickup_date, date.today())

    def test_sale_amount_auto_calculation(self):
        self.order.books.add(self.book)
        self.order.save()
        self.order.refresh_from_db()
        self.assertEqual(self.order.sale_amount, self.book.retail_price)

class EmployeeModelTests(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Test Group")
        self.employee_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '1234567890',
            'address': '123 Main St',
            'birth_date': date(1990, 1, 1),
            'hire_date': date.today(),
            'group': self.group,
            'zip_code': '12345',
            'state': 'CA',
            'email': 'john.doe@example.com'
        }

    def test_create_with_user(self):
        employee = Employee.create_with_user(password='testpass123', **self.employee_data)
        self.assertIsNotNone(employee.user)
        self.assertEqual(employee.user.first_name, 'John')
        self.assertEqual(employee.user.last_name, 'Doe')
        self.assertEqual(employee.user.email, 'john.doe@example.com')
        self.assertTrue(employee.user.check_password('testpass123'))
        self.assertTrue(employee.user.groups.filter(name="Test Group").exists())
        self.assertEqual(employee.user.username, 'john.doe')

    def test_sync_user(self):
        employee = Employee.create_with_user(password='testpass123', **self.employee_data)
        employee.first_name = 'Jane'
        employee.last_name = 'Smith'
        employee.email = 'jane.smith@example.com'
        new_group = Group.objects.create(name="New Group")
        employee.group = new_group
        employee.save()
        employee.user.refresh_from_db()
        self.assertEqual(employee.user.first_name, 'Jane')
        self.assertEqual(employee.user.last_name, 'Smith')
        self.assertEqual(employee.user.email, 'jane.smith@example.com')
        self.assertEqual(employee.user.username, 'jane.smith')
        self.assertTrue(employee.user.groups.filter(name="New Group").exists())
        self.assertFalse(employee.user.groups.filter(name="Test Group").exists())

    def test_set_password(self):
        employee = Employee.create_with_user(password='oldpass', **self.employee_data)
        employee.set_password('newpass123')
        employee.user.refresh_from_db()
        self.assertTrue(employee.user.check_password('newpass123'))

    def test_generate_username_collision(self):
        User.objects.create_user(username='john.doe', password='pass')
        employee = Employee.create_with_user(password='testpass123', **self.employee_data)
        self.assertEqual(employee.user.username, 'john.doe1')

    def test_str(self):
        employee = Employee(**self.employee_data)
        self.assertEqual(str(employee), "John Doe")
