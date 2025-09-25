from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from book_shop_here.models import Book, Author, Order, Role, Customer, Employee
from book_shop_here.forms import BookForm, CustomerForm, RoleForm, AuthorForm, OrderForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
import re

class BookModelTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(first_name="John", last_name="Doe")
        self.book = Book.objects.create(
            book_id="doej1234",
            title="Test Book",
            cost=10.00,
            retail_price=15.00,
            publication_date=date(2020, 1, 1),
            edition="1st",
            rating="excellent",
            book_status="available"
        )
        self.book.authors.add(self.author)

    def test_generate_pk(self):
        book = Book(title="New Book", cost=5.00, retail_price=10.00, publication_date=date(2020, 1, 1))
        book_id = book.generate_pk(self.author)
        self.assertTrue(re.match(r"[a-z]{4}[0-9]{4}", book_id), "Book ID should match pattern: four letters + four digits")
        self.assertTrue(book_id.startswith("doe"), "Book ID should start with author's last name")

    def test_book_str(self):
        self.assertEqual(str(self.book), "doej1234: Test Book")

    def test_invalid_book_id(self):
        book = Book(
            book_id="invalid",
            title="Invalid Book",
            cost=5.00,
            retail_price=10.00,
            publication_date=date(2020, 1, 1)
        )
        with self.assertRaises(ValidationError):
            book.full_clean()

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
        customer.full_clean()  # Should not raise
        self.assertEqual(str(customer), "Alice Smith")

class OrderModelTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(title="Clerk")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.employee = Employee.objects.create(
            first_name="Test",
            last_name="Employee",
            address="123 St",
            zip_code="12345",
            state="CA",
            birth_date=date(1990, 1, 1),
            phone_number="1234567890",
            position_id=self.role,
            user=self.user
        )
        self.customer = Customer.objects.create(first_name="Bob", last_name="Jones")
        self.book = Book.objects.create(
            book_id="test1234",
            title="Test Book",
            cost=10.00,
            retail_price=15.00,
            publication_date=date(2020, 1, 1),
            book_status="available"
        )
        self.order = Order.objects.create(
            customer_id=self.customer,
            employee_id=self.employee,
            sale_amount=15.00,
            payment_method="cash",
            order_status="to_ship"
        )
        self.order.books.add(self.book)

    def test_completed_order(self):
        self.order.completed_order()
        self.book.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.book.book_status, "sold")
        self.assertEqual(self.order.order_status, "shipped")
        self.assertEqual(self.order.delivery_pickup_date, date.today())

class BookFormTests(TestCase):
    def setUp(self):
        self.author = Author.objects.create(first_name="John", last_name="Doe")

    def test_book_form_valid(self):
        form_data = {
            "title": "Test Book",
            "cost": 10.00,
            "retail_price": 15.00,
            "publication_date": date(2020, 1, 1),
            "edition": "1st",
            "rating": "excellent",
            "book_status": "available",
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
            "edition": "1st",
            "rating": "excellent",
            "book_status": "available",
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

class RoleFormTests(TestCase):
    def test_role_form_valid(self):
        form_data = {
            "title": "Manager",
            "description": "Manages store operations"
        }
        form = RoleForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_role_form_no_description(self):
        form_data = {"title": "Clerk"}
        form = RoleForm(data=form_data)
        self.assertTrue(form.is_valid())

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
        self.role = Role.objects.create(title="Clerk")
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.employee = Employee.objects.create(
            first_name="Test",
            last_name="Employee",
            address="123 St",
            zip_code="12345",
            state="CA",
            birth_date=date(1990, 1, 1),
            phone_number="1234567890",
            position_id=self.role,
            user=self.user
        )
        self.customer = Customer.objects.create(first_name="Bob", last_name="Jones")
        self.book = Book.objects.create(
            book_id="test1234",
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
            "sale_amount": 15.00,
            "payment_method": "cash",
            "order_status": "to_ship",
            "books": [self.book.book_id]
        }
        form = OrderForm(data=form_data)
        self.assertTrue(form.is_valid())

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.owner_group = Group.objects.create(name="OwnerGroup")
        self.user.groups.add(self.owner_group)
        self.author = Author.objects.create(first_name="John", last_name="Doe")
        self.book = Book.objects.create(
            book_id="doej1234",
            title="Test Book",
            cost=10.00,
            retail_price=15.00,
            publication_date=date(2020, 1, 1),
            rating="excellent",
            book_status="available"
        )
        self.book.authors.add(self.author)
        self.role = Role.objects.create(title="Manager", description="Store manager")
        self.customer = Customer.objects.create(first_name="Bob", last_name="Jones")
        self.employee = Employee.objects.create(
            first_name="Test",
            last_name="Employee",
            address="123 St",
            zip_code="12345",
            state="CA",
            birth_date=date(1990, 1, 1),
            phone_number="1234567890",
            position_id=self.role,
            user=self.user
        )
        self.order = Order.objects.create(
            customer_id=self.customer,
            employee_id=self.employee,
            sale_amount=15.00,
            payment_method="cash",
            order_status="to_ship"
        )
        self.order.books.add(self.book)

    def test_home_view_authenticated(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, reverse("book_list"))
        self.assertTemplateNotUsed(response, "book_shop_here/home.html")

    def test_home_view_unauthenticated(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/home.html")
        self.assertContains(response, "Login to manage books")

    def test_book_list_view(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("book_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/book_list.html")
        self.assertContains(response, "Test Book")
        self.assertContains(response, "Add Book")  # Visible due to OwnerGroup

    def test_book_list_search(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("book_list"), {"q": "Test"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Book")
        response = self.client.get(reverse("book_list"), {"q": "Nonexistent"})
        self.assertContains(response, "No books found")

    def test_add_book_view_permission(self):
        self.client.login(username="testuser", password="testpass")
        self.user.groups.remove(self.owner_group)
        response = self.client.get(reverse("add_book"))
        self.assertEqual(response.status_code, 403)  # No add_book permission

        # Add permission
        content_type = ContentType.objects.get_for_model(Book)
        permission = Permission.objects.get(codename="add_book", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("add_book"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/book_form.html")
        self.assertContains(response, "Add Book")

    def test_add_book_post(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Book)
        permission = Permission.objects.get(codename="add_book", content_type=content_type)
        self.user.user_permissions.add(permission)
        form_data = {
            "title": "New Book",
            "cost": 10.00,
            "retail_price": 15.00,
            "publication_date": "2020-01-01",
            "edition": "1st",
            "rating": "excellent",
            "book_status": "available",
            "authors": [self.author.author_id]
        }
        response = self.client.post(reverse("add_book"), form_data)
        self.assertRedirects(response, reverse("book_list"))
        self.assertTrue(Book.objects.filter(title="New Book").exists())

    def test_delete_book_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Book)
        permission = Permission.objects.get(codename="delete_book", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.post(reverse("delete_book", args=["doej1234"]))
        self.assertRedirects(response, reverse("book_list"))
        self.assertFalse(Book.objects.filter(book_id="doej1234").exists())

    def test_author_list_view(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("author_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/author_list.html")
        self.assertContains(response, "John Doe")
        self.assertContains(response, "Add Author")  # Visible due to OwnerGroup

    def test_add_author_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Author)
        permission = Permission.objects.get(codename="add_author", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("add_author"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/author_form.html")
        self.assertContains(response, "Add Author")

    def test_role_list_view(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("role_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/role_list.html")
        self.assertContains(response, "Manager - Store manager")
        self.assertContains(response, "Add Role")  # Visible due to OwnerGroup

    def test_add_role_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Role)
        permission = Permission.objects.get(codename="add_role", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("add_role"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/role_form.html")
        self.assertContains(response, "Add Role")

    def test_order_list_view(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("order_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/order_list.html")
        self.assertContains(response, str(self.order.order_id))
        self.assertContains(response, "Add Order")  # Visible due to OwnerGroup

    def test_add_order_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Order)
        permission = Permission.objects.get(codename="add_order", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("add_order"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/order_form.html")

class CustomFilterTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.owner_group = Group.objects.create(name="OwnerGroup")
        self.manager_group = Group.objects.create(name="ManagerGroup")

    def test_is_in_group_filter(self):
        self.client.login(username="testuser", password="testpass")
        self.user.groups.add(self.owner_group)
        response = self.client.get(reverse("book_list"))
        self.assertContains(response, "Roles")  # Visible due to OwnerGroup
        self.assertContains(response, "Orders")
        self.user.groups.remove(self.owner_group)
        self.user.groups.add(self.manager_group)
        response = self.client.get(reverse("book_list"))
        self.assertContains(response, "Roles")  # Visible due to ManagerGroup
        self.assertContains(response, "Orders")

class URLTests(TestCase):
    def test_url_resolves(self):
        self.assertEqual(reverse("home"), "/")
        self.assertEqual(reverse("book_list"), "/books/")
        self.assertEqual(reverse("add_book"), "/books/add/")
        self.assertEqual(reverse("delete_book", args=["test1234"]), "/books/delete_book/test1234/")
        self.assertEqual(reverse("role_list"), "/roles/")
        self.assertEqual(reverse("add_role"), "/roles/add/")
        self.assertEqual(reverse("author_list"), "/authors/")
        self.assertEqual(reverse("add_author"), "/authors/add")
        self.assertEqual(reverse("order_list"), "/orders/")
        self.assertEqual(reverse("add_order"), "/orders/add")