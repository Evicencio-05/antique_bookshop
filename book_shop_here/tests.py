from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from book_shop_here.models import Book, Author, Order, Customer, Employee, GroupProfile
from book_shop_here.forms import BookForm, CustomerForm, AuthorForm, OrderForm, GroupForm, EmployeeForm
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
            "sale_amount": 15.00,
            "payment_method": "cash",
            "order_status": "to_ship",
            "books": [self.book.legacy_id]
        }
        form = OrderForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_order_form_no_books(self):
        form_data = {
            "customer_id": self.customer.customer_id,
            "employee_id": self.employee.employee_id,
            "sale_amount": 15.00,
            "payment_method": "cash",
            "order_status": "to_ship",
            "books": []
        }
        form = OrderForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("books", form.errors)

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
        del data['password1']
        del data['password2']
        form = EmployeeForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("Password and confirmation are required for new employees.", str(form.errors))

    def test_form_creation_password_mismatch(self):
        data = self.form_data.copy()
        data['password2'] = 'wrongpass'
        form = EmployeeForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("Passwords don't match.", str(form.errors))

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

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.owner_group = Group.objects.create(name="Owner (ViewTests)")
        self.user.groups.add(self.owner_group)
        self.author = Author.objects.create(first_name="John", last_name="Doe")
        self.book = Book.objects.create(
            legacy_id="test1234",
            title="Test Book",
            cost=10.00,
            retail_price=15.00,
            publication_date=date(2020, 1, 1),
            publisher="Test Publisher",
            edition="1st",
            rating="excellent",
            book_status="available"
        )
        self.book.authors.add(self.author)
        self.group = Group.objects.create(name="Manager (ViewTests)")
        self.group_profile = GroupProfile.objects.create(group=self.group, description="Store manager")
        self.customer = Customer.objects.create(first_name="Bob", last_name="Jones")
        self.employee = Employee.objects.create(
            first_name="Test",
            last_name="Employee",
            address="123 St",
            zip_code="12345",
            state="CA",
            birth_date=date(1990, 1, 1),
            phone_number="1234567890",
            group=self.group,
            user=self.user,
            email="test.employee@example.com"
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
        response = self.client.get(reverse("book_shop_here:home"))
        self.assertRedirects(response, reverse("book_shop_here:book-list"))
        self.assertTemplateNotUsed(response, "book_shop_here/home.html")

    def test_home_view_unauthenticated(self):
        response = self.client.get(reverse("book_shop_here:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/home.html")
        self.assertContains(response, "Login</a> to manage books")

    def test_book_list_view(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("book_shop_here:book-list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/book_list.html")
        self.assertContains(response, "Test Book")
        self.assertContains(response, "Add Book")

    def test_book_list_search(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("book_shop_here:book-list"), {"q": "Test"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Book")
        response = self.client.get(reverse("book_shop_here:book-list"), {"q": "Nonexistent"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No books found")

    def test_book_create_view_permission(self):
        self.client.login(username="testuser", password="testpass")
        self.user.groups.remove(self.owner_group)
        response = self.client.get(reverse("book_shop_here:book-create"))
        self.assertEqual(response.status_code, 403)

        content_type = ContentType.objects.get_for_model(Book)
        permission = Permission.objects.get(codename="add_book", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("book_shop_here:book-create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/book_form.html")
        self.assertContains(response, "Add Book")

    def test_book_create_post(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Book)
        permission = Permission.objects.get(codename="add_book", content_type=content_type)
        self.user.user_permissions.add(permission)
        form_data = {
            "title": "New Book",
            "cost": 10.00,
            "retail_price": 15.00,
            "publication_date": "2020-01-01",
            "publisher": "New Publisher",
            "edition": "1st",
            "rating": "excellent",
            "book_status": "available",
            "legacy_id": "newb1234",
            "authors": [self.author.author_id]
        }
        response = self.client.post(reverse("book_shop_here:book-create"), form_data)
        self.assertRedirects(response, reverse("book_shop_here:book-list"))
        self.assertTrue(Book.objects.filter(title="New Book", legacy_id="newb1234").exists())

    def test_book_create_invalid_post(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Book)
        permission = Permission.objects.get(codename="add_book", content_type=content_type)
        self.user.user_permissions.add(permission)
        form_data = {
            "title": "New Book",
            "cost": 10.00,
            "retail_price": 15.00,
            "publication_date": "2020-01-01",
            "publisher": "New Publisher",
            "edition": "1st",
            "rating": "excellent",
            "book_status": "available",
            "legacy_id": "invalid",
            "authors": []
        }
        response = self.client.post(reverse("book_shop_here:book-create"), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/book_form.html")
        self.assertFalse(Book.objects.filter(title="New Book").exists())

    def test_book_update_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Book)
        permission = Permission.objects.get(codename="change_book", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("book_shop_here:book-update", kwargs={"pk": self.book.book_id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/book_form.html")
        self.assertContains(response, "Edit Book")

    def test_book_update_post(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Book)
        permission = Permission.objects.get(codename="change_book", content_type=content_type)
        self.user.user_permissions.add(permission)
        form_data = {
            "title": "Updated Book",
            "cost": 12.00,
            "retail_price": 18.00,
            "publication_date": "2020-01-01",
            "publisher": "Updated Publisher",
            "edition": "2nd",
            "rating": "excellent",
            "book_status": "available",
            "legacy_id": "doej1234",
            "authors": [self.author.author_id]
        }
        response = self.client.post(reverse("book_shop_here:book-update", kwargs={"pk": self.book.book_id}), form_data)
        self.assertRedirects(response, reverse("book_shop_here:book-list"))
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, "Updated Book")
        self.assertEqual(self.book.legacy_id, "doej1234")

    def test_book_delete_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Book)
        permission = Permission.objects.get(codename="delete_book", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.post(reverse("book_shop_here:book-delete", kwargs={"pk": "doej1234"}))
        self.assertRedirects(response, reverse("book_shop_here:book-list"))
        self.assertFalse(Book.objects.filter(legacy_id="doej1234").exists())

    def test_author_list_view(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("book_shop_here:author-list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/author_list.html")
        self.assertContains(response, "John Doe")
        self.assertContains(response, "Add Author")

    def test_author_create_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Author)
        permission = Permission.objects.get(codename="add_author", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("book_shop_here:author-create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/author_form.html")
        self.assertContains(response, "Add Author")

    def test_author_create_post(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Author)
        permission = Permission.objects.get(codename="add_author", content_type=content_type)
        self.user.user_permissions.add(permission)
        form_data = {
            "first_name": "Jane",
            "last_name": "Austen",
            "birth_year": 1775,
            "description": "Famous novelist"
        }
        response = self.client.post(reverse("book_shop_here:author-create"), form_data)
        self.assertRedirects(response, reverse("book_shop_here:author-list"))
        self.assertTrue(Author.objects.filter(last_name="Austen").exists())

    def test_author_update_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Author)
        permission = Permission.objects.get(codename="change_author", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("book_shop_here:author-update", kwargs={"pk": self.author.author_id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/author_form.html")
        self.assertContains(response, "John Doe")

    def test_author_update_post(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Author)
        permission = Permission.objects.get(codename="change_author", content_type=content_type)
        self.user.user_permissions.add(permission)
        form_data = {
            "first_name": "Jane",
            "last_name": "Austen",
            "birth_year": 1775,
            "description": "Updated description"
        }
        response = self.client.post(reverse("book_shop_here:author-update", kwargs={"pk": self.author.author_id}), form_data)
        self.assertRedirects(response, reverse("book_shop_here:author-list"))
        self.author.refresh_from_db()
        self.assertEqual(self.author.first_name, "Jane")
        self.assertEqual(self.author.description, "Updated description")

    def test_author_delete_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Author)
        permission = Permission.objects.get(codename="delete_author", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.post(reverse("book_shop_here:author-delete", kwargs={"pk": self.author.author_id}))
        self.assertRedirects(response, reverse("book_shop_here:author-list"))
        self.assertFalse(Author.objects.filter(author_id=self.author.author_id).exists())

    def test_group_list_view(self):
        self.client.login(username="testuser", password="testpass")
        GroupProfile.objects.update_or_create(group=self.owner_group, defaults={'description': 'The Owner'})
        response = self.client.get(reverse("book_shop_here:group-list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/group_list.html")
        self.assertContains(response, "Owner - The Owner")
        self.assertContains(response, "Add Group")

    def test_group_create_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Group)
        permission = Permission.objects.get(codename="add_group", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("book_shop_here:group-create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/group_form.html")
        self.assertContains(response, "Add Group")

    def test_group_create_post(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Group)
        permission = Permission.objects.get(codename="add_group", content_type=content_type)
        self.user.user_permissions.add(permission)
        form_data = {
            "name": "New Group",
            "description": "New group description",
            "permissions": []
        }
        response = self.client.post(reverse("book_shop_here:group-create"), form_data)
        self.assertRedirects(response, reverse("book_shop_here:group-list"))
        self.assertTrue(Group.objects.filter(name="New Group").exists())

    def test_group_update_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Group)
        permission = Permission.objects.get(codename="change_group", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("book_shop_here:group-update", kwargs={"pk": self.group.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/group_form.html")
        self.assertContains(response, "Manager (ViewTests)")

    def test_group_update_post(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Group)
        permission = Permission.objects.get(codename="change_group", content_type=content_type)
        self.user.user_permissions.add(permission)
        form_data = {
            "name": "Updated Manager",
            "description": "Updated description",
            "permissions": []
        }
        response = self.client.post(reverse("book_shop_here:group-update", kwargs={"pk": self.group.id}), form_data)
        self.assertRedirects(response, reverse("book_shop_here:group-list"))
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "Updated Manager")
        self.assertEqual(self.group.profile.description, "Updated description")

    def test_group_delete_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Group)
        permission = Permission.objects.get(codename="delete_group", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.post(reverse("book_shop_here:group-delete", kwargs={"pk": self.group.id}))
        self.assertRedirects(response, reverse("book_shop_here:group-list"))
        self.assertFalse(Group.objects.filter(id=self.group.id).exists())

    def test_order_list_view(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("book_shop_here:order-list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/order_list.html")
        self.assertContains(response, str(self.order.order_id))
        self.assertContains(response, "Add Order")

    def test_order_create_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Order)
        permission = Permission.objects.get(codename="add_order", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("book_shop_here:order-create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/order_form.html")

    def test_order_create_post(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Order)
        permission = Permission.objects.get(codename="add_order", content_type=content_type)
        self.user.user_permissions.add(permission)
        form_data = {
            "customer_id": self.customer.customer_id,
            "employee_id": self.employee.employee_id,
            "sale_amount": 15.00,
            "payment_method": "cash",
            "order_status": "to_ship",
            "books": [self.book.legacy_id]
        }
        response = self.client.post(reverse("book_shop_here:order-create"), form_data)
        self.assertRedirects(response, reverse("book_shop_here:order-list"))
        self.assertTrue(Order.objects.filter(customer_id=self.customer).exists())

    def test_order_update_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Order)
        permission = Permission.objects.get(codename="change_order", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("book_shop_here:order-update", kwargs={"pk": self.order.order_id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/order_form.html")
        self.assertContains(response, "Edit Order")

    def test_order_update_post(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Order)
        permission = Permission.objects.get(codename="change_order", content_type=content_type)
        self.user.user_permissions.add(permission)
        form_data = {
            "customer_id": self.customer.customer_id,
            "employee_id": self.employee.employee_id,
            "sale_amount": 20.00,
            "payment_method": "credit",
            "order_status": "pickup",
            "books": [self.book.book_id]
        }
        response = self.client.post(reverse("book_shop_here:order-update", kwargs={"pk": self.order.order_id}), form_data)
        self.assertRedirects(response, reverse("book_shop_here:order-list"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.sale_amount, 20.00)
        self.assertEqual(self.order.payment_method, "credit")
        self.assertEqual(self.order.order_status, "pickup")

    def test_order_delete_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Order)
        permission = Permission.objects.get(codename="delete_order", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.post(reverse("book_shop_here:order-delete", kwargs={"pk": self.order.order_id}))
        self.assertRedirects(response, reverse("book_shop_here:order-list"))
        self.assertFalse(Order.objects.filter(order_id=self.order.order_id).exists())


    def test_employee_list_view(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("book_shop_here:employee-list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/employee_list.html")
        self.assertContains(response, "Test Employee")
        self.assertContains(response, "Add Employee")

    def test_employee_create_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Employee)
        permission = Permission.objects.get(codename="add_employee", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("book_shop_here:employee-create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/employee_form.html")
        self.assertContains(response, "Add Employee")

    def test_employee_create_post(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Employee)
        permission = Permission.objects.get(codename="add_employee", content_type=content_type)
        self.user.user_permissions.add(permission)
        form_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone_number': '1234567890',
            'address': '123 Main St',
            'birth_date': '1990-01-01',
            'hire_date': date.today(),
            'group': self.group.id,
            'zip_code': '12345',
            'state': 'CA',
            'email': 'jane.smith@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
        response = self.client.post(reverse("book_shop_here:employee-create"), form_data)
        self.assertRedirects(response, reverse("book_shop_here:employee-list"))
        self.assertTrue(Employee.objects.filter(first_name="Jane").exists())

    def test_employee_update_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Employee)
        permission = Permission.objects.get(codename="change_employee", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("book_shop_here:employee-update", kwargs={"pk": self.employee.employee_id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/employee_form.html")
        self.assertContains(response, "Edit Employee")

    def test_employee_update_post(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Employee)
        permission = Permission.objects.get(codename="change_employee", content_type=content_type)
        self.user.user_permissions.add(permission)
        form_data = {
            'first_name': 'Jane',
            'last_name': 'Employee',
            'phone_number': '1234567890',
            'address': '123 Main St',
            'birth_date': '1990-01-01',
            'hire_date': date.today(),
            'group': self.group.id,
            'zip_code': '12345',
            'state': 'CA',
            'email': 'jane.employee@example.com',
            'password1': '',
            'password2': ''
        }
        response = self.client.post(reverse("book_shop_here:employee-update", kwargs={"pk": self.employee.employee_id}), form_data)
        self.assertRedirects(response, reverse("book_shop_here:employee-list"))
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.first_name, "Jane")

    def test_employee_delete_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Employee)
        permission = Permission.objects.get(codename="delete_employee", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.post(reverse("book_shop_here:employee-delete", kwargs={"pk": self.employee.employee_id}))
        self.assertRedirects(response, reverse("book_shop_here:employee-list"))
        self.assertFalse(Employee.objects.filter(employee_id=self.employee.employee_id).exists())

    def test_customer_list_view(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("book_shop_here:customer-list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/customer_list.html")
        self.assertContains(response, "Bob Jones")
        self.assertContains(response, "Add Customer")

    def test_customer_create_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Customer)
        permission = Permission.objects.get(codename="add_customer", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("book_shop_here:customer-create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/customer_form.html")
        self.assertContains(response, "Add Customer")

    def test_customer_create_post(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Customer)
        permission = Permission.objects.get(codename="add_customer", content_type=content_type)
        self.user.user_permissions.add(permission)
        form_data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "phone_number": "1234567890",
            "mailing_address": "123 St"
        }
        response = self.client.post(reverse("book_shop_here:customer-create"), form_data)
        self.assertRedirects(response, reverse("book_shop_here:customer-list"))
        self.assertTrue(Customer.objects.filter(first_name="Alice").exists())

    def test_customer_update_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Customer)
        permission = Permission.objects.get(codename="change_customer", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("book_shop_here:customer-update", kwargs={"pk": self.customer.customer_id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/customer_form.html")
        self.assertContains(response, "Edit Customer")

    def test_customer_update_post(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Customer)
        permission = Permission.objects.get(codename="change_customer", content_type=content_type)
        self.user.user_permissions.add(permission)
        form_data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "phone_number": "9876543210",
            "mailing_address": "456 St"
        }
        response = self.client.post(reverse("book_shop_here:customer-update", kwargs={"pk": self.customer.customer_id}), form_data)
        self.assertRedirects(response, reverse("book_shop_here:customer-list"))
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.first_name, "Alice")
        self.assertEqual(self.customer.phone_number, "9876543210")

    def test_customer_delete_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Customer)
        permission = Permission.objects.get(codename="delete_customer", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.post(reverse("book_shop_here:customer-delete", kwargs={"pk": self.customer.customer_id}))
        self.assertRedirects(response, reverse("book_shop_here:customer-list"))
        self.assertFalse(Customer.objects.filter(customer_id=self.customer.customer_id).exists())