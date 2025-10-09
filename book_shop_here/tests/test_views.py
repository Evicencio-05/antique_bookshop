import logging
from datetime import date

from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase
from django.urls import reverse

from book_shop_here.models import Author, Book, Customer, Employee, GroupProfile, Order

Logger = logging.getLogger(__name__)


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
            book_status="available",
        )
        self.book.authors.add(self.author)
        self.group = Group.objects.create(name="Manager (ViewTests)")
        self.group_profile = GroupProfile.objects.create(
            group=self.group, description="Store manager"
        )
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
            email="test.employee@example.com",
        )
        self.order = Order.objects.create(
            customer_id=self.customer,
            employee_id=self.employee,
            sale_amount=15.00,
            payment_method="cash",
            order_status="to_ship",
        )
        self.order.books.add(self.book)

    def test_home_view_authenticated(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("book_shop_here:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/home.html")

    def test_home_view_unauthenticated(self):
        response = self.client.get(reverse("book_shop_here:home"))
        # Now unauthenticated users are redirected to the login page
        self.assertRedirects(
            response, reverse("book_shop_here:login"), fetch_redirect_response=False
        )

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
        # Prefixed by author
        response = self.client.get(reverse("book_shop_here:book-list"), {"q": "author:John"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Book")
        # Prefixed by legacy id
        response = self.client.get(
            reverse("book_shop_here:book-list"), {"q": f"legacy:{self.book.legacy_id}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Book")
        # Rating label
        response = self.client.get(reverse("book_shop_here:book-list"), {"q": "rating:Excellent"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Book")

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
            "authors": [self.author.author_id],
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
            "authors": [],
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
        response = self.client.get(
            reverse("book_shop_here:book-update", kwargs={"pk": self.book.book_id})
        )
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
            "authors": [self.author.author_id],
        }
        response = self.client.post(
            reverse("book_shop_here:book-update", kwargs={"pk": self.book.book_id}), form_data
        )
        self.assertRedirects(response, reverse("book_shop_here:book-list"))
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, "Updated Book")
        self.assertEqual(self.book.legacy_id, "doej1234")

    def test_book_delete_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Book)
        permission = Permission.objects.get(codename="delete_book", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.post(
            reverse("book_shop_here:book-delete", kwargs={"pk": self.book.book_id})
        )
        self.assertRedirects(response, reverse("book_shop_here:book-list"))
        self.assertFalse(Book.objects.filter(legacy_id="doej1234").exists())

    def test_author_list_view(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("book_shop_here:author-list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/author_list.html")
        self.assertContains(response, "John Doe")

    def test_order_close_action_marks_shipped(self):
        # Grant permission and login
        self.client.login(username="testuser", password="testpass")
        ct = ContentType.objects.get_for_model(Order)
        perm = Permission.objects.get(codename="change_order", content_type=ct)
        self.user.user_permissions.add(perm)
        # Ensure order initially open
        self.order.order_status = "to_ship"
        self.order.save()
        url = reverse("book_shop_here:order-close", kwargs={"pk": self.order.pk})
        resp = self.client.post(
            url, {"status": "shipped", "next": reverse("book_shop_here:order-list")}
        )
        self.assertRedirects(resp, reverse("book_shop_here:order-list"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.order_status, Order.OrderStatus.SHIPPED)
        self.assertIsNotNone(self.order.delivery_pickup_date)

    def test_order_close_action_marks_picked_up(self):
        # Grant permission and login
        self.client.login(username="testuser", password="testpass")
        ct = ContentType.objects.get_for_model(Order)
        perm = Permission.objects.get(codename="change_order", content_type=ct)
        self.user.user_permissions.add(perm)
        # Ensure order initially open
        self.order.order_status = "pickup"
        self.order.save()
        url = reverse("book_shop_here:order-close", kwargs={"pk": self.order.pk})
        resp = self.client.post(
            url, {"status": "picked_up", "next": reverse("book_shop_here:order-list")}
        )
        self.assertRedirects(resp, reverse("book_shop_here:order-list"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.order_status, Order.OrderStatus.PICKED_UP)
        self.assertIsNotNone(self.order.delivery_pickup_date)

    def test_home_include_hidden_books_toggle(self):
        # Mark book as sold so it's hidden by default
        self.book.book_status = "sold"
        self.book.save()
        self.client.login(username="testuser", password="testpass")
        # Default search should not include the book in lookup_results
        resp = self.client.get(reverse("book_shop_here:home"), {"q": "Test"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("lookup_results" in resp.context)
        self.assertTrue(not resp.context["lookup_results"].get("books"))
        # With include_hidden=1, lookup_results['books'] should include it
        resp2 = self.client.get(
            reverse("book_shop_here:home"), {"q": "Test", "include_hidden": "1"}
        )
        self.assertEqual(resp2.status_code, 200)
        books_list = resp2.context["lookup_results"].get("books") or []
        # Ensure at least one of the returned books matches our title
        self.assertTrue(any(getattr(b, "title", "") == "Test Book" for b in books_list))

    def test_order_update_displays_selected_books_even_if_not_available(self):
        # Change status to sold and verify it still appears on the edit form
        self.book.book_status = "sold"
        self.book.save()
        self.client.login(username="testuser", password="testpass")
        ct = ContentType.objects.get_for_model(Order)
        perm = Permission.objects.get(codename="change_order", content_type=ct)
        self.user.user_permissions.add(perm)
        resp = self.client.get(reverse("book_shop_here:order-update", kwargs={"pk": self.order.pk}))
        self.assertEqual(resp.status_code, 200)
        # The book title should be present and the checkbox value should include the book id
        self.assertContains(resp, self.book.title)
        self.assertContains(resp, f'value="{self.book.pk}"')

    def test_order_list_close_buttons_visible_for_open_orders(self):
        self.client.login(username="testuser", password="testpass")
        ct = ContentType.objects.get_for_model(Order)
        perm = Permission.objects.get(codename="change_order", content_type=ct)
        self.user.user_permissions.add(perm)
        self.order.order_status = "to_ship"
        self.order.save()
        resp = self.client.get(reverse("book_shop_here:order-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Mark Shipped")
        self.assertContains(resp, "Mark Picked Up")

    def test_author_list_search(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("book_shop_here:author-list"), {"q": "John"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")
        response = self.client.get(reverse("book_shop_here:author-list"), {"q": "Nonexistent"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No authors found")

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
            "description": "Famous novelist",
        }
        response = self.client.post(reverse("book_shop_here:author-create"), form_data)
        self.assertRedirects(response, reverse("book_shop_here:author-list"))
        self.assertTrue(Author.objects.filter(last_name="Austen").exists())

    def test_author_update_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Author)
        permission = Permission.objects.get(codename="change_author", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(
            reverse("book_shop_here:author-update", kwargs={"pk": self.author.author_id})
        )
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
            "description": "Updated description",
        }
        response = self.client.post(
            reverse("book_shop_here:author-update", kwargs={"pk": self.author.author_id}), form_data
        )
        self.assertRedirects(response, reverse("book_shop_here:author-list"))
        self.author.refresh_from_db()
        self.assertEqual(self.author.first_name, "Jane")
        self.assertEqual(self.author.description, "Updated description")

    def test_author_delete_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Author)
        permission = Permission.objects.get(codename="delete_author", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.post(
            reverse("book_shop_here:author-delete", kwargs={"pk": self.author.author_id})
        )
        self.assertRedirects(response, reverse("book_shop_here:author-list"))
        self.assertFalse(Author.objects.filter(author_id=self.author.author_id).exists())

    def test_group_list_view(self):
        self.client.login(username="testuser", password="testpass")
        GroupProfile.objects.update_or_create(
            group=self.owner_group, defaults={"description": "The Owner"}
        )
        response = self.client.get(reverse("book_shop_here:group-list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/group_list.html")
        self.assertContains(response, "Owner - The Owner")
        self.assertContains(response, "Add Role")

    def test_group_list_search_filters_by_name_and_description(self):
        self.client.login(username="testuser", password="testpass")
        # Ensure owner has a profile matching 'Owner'
        GroupProfile.objects.update_or_create(
            group=self.owner_group, defaults={"description": "The Owner"}
        )
        # Search by name
        response = self.client.get(reverse("book_shop_here:group-list"), {"q": "Owner"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.owner_group.name)
        # Manager group should not appear when filtering by 'Owner'
        self.assertNotContains(response, self.group.name)

    def test_group_list_search_multiple_tokens_and_phrase(self):
        self.client.login(username="testuser", password="testpass")
        GroupProfile.objects.update_or_create(
            group=self.owner_group, defaults={"description": "The Owner"}
        )
        # Multiple tokens should be ANDed across fields
        response = self.client.get(reverse("book_shop_here:group-list"), {"q": "Owner ViewTests"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.owner_group.name)
        self.assertNotContains(response, self.group.name)
        # Quoted phrase should be treated as one token
        response = self.client.get(reverse("book_shop_here:group-list"), {"q": '"The Owner"'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.owner_group.name)

    def test_group_list_search_spaceless_normalization(self):
        self.client.login(username="testuser", password="testpass")
        # Owner name contains "ViewTests" without a space; quoted phrase with a space should still match
        response = self.client.get(reverse("book_shop_here:group-list"), {"q": '"View Tests"'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.owner_group.name)

    def test_group_list_search_by_permission_fields(self):
        self.client.login(username="testuser", password="testpass")
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        ct = ContentType.objects.get_for_model(Book)
        add_book = Permission.objects.get(codename="add_book", content_type=ct)
        # Give Manager group a perm so it's discoverable by search
        self.group.permissions.add(add_book)

        # Search by codename
        response = self.client.get(reverse("book_shop_here:group-list"), {"q": "add_book"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.group.name)
        self.assertNotContains(response, self.owner_group.name)

        # Search by permission name fragment
        response = self.client.get(reverse("book_shop_here:group-list"), {"q": "add book"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.group.name)

        # Search using prefix
        response = self.client.get(reverse("book_shop_here:group-list"), {"q": "perm:add_book"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.group.name)

    def test_group_list_auth_dropdown_renders(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("book_shop_here:group-list"))
        self.assertEqual(response.status_code, 200)
        # Dropdown summary text is present
        self.assertContains(response, "Show auth permissions")
        # The auth model headers should be present in the collapsed section's markup
        self.assertContains(response, ">User<")
        self.assertContains(response, ">Role<")

    def test_group_create_form_permissions_matrix(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Group)
        permission = Permission.objects.get(codename="add_group", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("book_shop_here:group-create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/group_form.html")
        # Headers from matrix
        self.assertContains(response, ">Book<")
        self.assertContains(response, ">Author<")
        self.assertContains(response, ">User<")
        self.assertContains(response, ">Role<")
        # Contains at least one permissions checkbox
        self.assertContains(response, 'name="permissions"', html=False)
        # Domain/auth select buttons present
        self.assertContains(response, "Select domain")
        self.assertContains(response, "Select auth")

    def test_group_permissions_matrix_display(self):
        self.client.login(username="testuser", password="testpass")
        # Give the group a single permission (e.g., add_book)
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        ct = ContentType.objects.get_for_model(Book)
        add_book = Permission.objects.get(codename="add_book", content_type=ct)
        self.group.permissions.add(add_book)

        response = self.client.get(reverse("book_shop_here:group-list"))
        self.assertEqual(response.status_code, 200)
        # Header includes models as columns
        self.assertContains(response, ">Book<")
        self.assertContains(response, ">Author<")
        self.assertContains(response, ">Employee<")
        # We expect at least one green check (✓) to render and no red Xs
        self.assertContains(response, "&#10003;")  # green check present somewhere
        self.assertNotContains(response, "&#10007;")  # red x removed for cleaner look

    def test_group_create_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Group)
        permission = Permission.objects.get(codename="add_group", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(reverse("book_shop_here:group-create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/group_form.html")
        self.assertContains(response, "Add Role")

    def test_group_create_post(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Group)
        permission = Permission.objects.get(codename="add_group", content_type=content_type)
        self.user.user_permissions.add(permission)
        form_data = {"name": "New Group", "description": "New group description", "permissions": []}
        response = self.client.post(reverse("book_shop_here:group-create"), form_data)
        self.assertRedirects(response, reverse("book_shop_here:group-list"))
        self.assertTrue(Group.objects.filter(name="New Group").exists())

    def test_group_update_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Group)
        permission = Permission.objects.get(codename="change_group", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(
            reverse("book_shop_here:group-update", kwargs={"pk": self.group.id})
        )
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
            "permissions": [],
        }
        response = self.client.post(
            reverse("book_shop_here:group-update", kwargs={"pk": self.group.id}), form_data
        )
        self.assertRedirects(response, reverse("book_shop_here:group-list"))
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "Updated Manager")
        self.assertEqual(self.group.profile.description, "Updated description")

    def test_group_delete_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Group)
        permission = Permission.objects.get(codename="delete_group", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.post(
            reverse("book_shop_here:group-delete", kwargs={"pk": self.group.id})
        )
        self.assertRedirects(response, reverse("book_shop_here:group-list"))
        self.assertFalse(Group.objects.filter(id=self.group.id).exists())

    def test_order_list_view(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("book_shop_here:order-list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/order_list.html")
        self.assertContains(response, str(self.order.order_id))
        self.assertContains(response, "Add Order")

    def test_order_list_search(self):
        self.client.login(username="testuser", password="testpass")
        # Search by customer last name
        response = self.client.get(
            reverse("book_shop_here:order-list"), {"q": self.customer.last_name}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.order.order_id))
        # Search by numeric order id
        response = self.client.get(
            reverse("book_shop_here:order-list"), {"q": str(self.order.order_id)}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.order.order_id))
        # Search by status label via prefix
        response = self.client.get(
            reverse("book_shop_here:order-list"), {"q": 'status:"To Be Shipped"'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.order.order_id))
        # Search by payment label via prefix
        response = self.client.get(reverse("book_shop_here:order-list"), {"q": "payment:Cash"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.order.order_id))

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
            "books": [self.book.legacy_id],
        }
        response = self.client.post(reverse("book_shop_here:order-create"), form_data)
        self.assertRedirects(response, reverse("book_shop_here:order-list"))
        self.assertTrue(Order.objects.filter(customer_id=self.customer).exists())

    def test_order_update_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Order)
        permission = Permission.objects.get(codename="change_order", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(
            reverse("book_shop_here:order-update", kwargs={"pk": self.order.order_id})
        )
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
            "books": [self.book.book_id],
        }
        response = self.client.post(
            reverse("book_shop_here:order-update", kwargs={"pk": self.order.order_id}), form_data
        )
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
        response = self.client.post(
            reverse("book_shop_here:order-delete", kwargs={"pk": self.order.order_id})
        )
        self.assertRedirects(response, reverse("book_shop_here:order-list"))
        self.assertFalse(Order.objects.filter(order_id=self.order.order_id).exists())

    def test_employee_list_view(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("book_shop_here:employee-list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/employee_list.html")
        self.assertContains(response, "Test Employee")
        self.assertContains(response, "Add Employee")

    def test_employee_list_search(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("book_shop_here:employee-list"), {"q": "Manager"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Employee")
        # Prefixed role
        response = self.client.get(reverse("book_shop_here:employee-list"), {"q": "role:Manager"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Employee")

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
            "first_name": "Jane",
            "last_name": "Smith",
            "phone_number": "1234567890",
            "address": "123 Main St",
            "birth_date": "1990-01-01",
            "hire_date": date.today(),
            "group": self.group.id,
            "zip_code": "12345",
            "state": "CA",
            "email": "jane.smith@example.com",
            "password1": "testpass123",
            "password2": "testpass123",
        }
        response = self.client.post(reverse("book_shop_here:employee-create"), form_data)
        self.assertRedirects(response, reverse("book_shop_here:employee-list"))
        self.assertTrue(Employee.objects.filter(first_name="Jane").exists())

    def test_employee_update_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Employee)
        permission = Permission.objects.get(codename="change_employee", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(
            reverse("book_shop_here:employee-update", kwargs={"pk": self.employee.employee_id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/employee_form.html")
        self.assertContains(response, "Edit Employee")

    def test_employee_update_post(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Employee)
        permission = Permission.objects.get(codename="change_employee", content_type=content_type)
        self.user.user_permissions.add(permission)
        form_data = {
            "first_name": "Jane",
            "last_name": "Employee",
            "phone_number": "1234567890",
            "address": "123 Main St",
            "birth_date": "1990-01-01",
            "hire_date": date.today(),
            "group": self.group.id,
            "zip_code": "12345",
            "state": "CA",
            "email": "jane.employee@example.com",
            "password1": "",
            "password2": "",
        }
        response = self.client.post(
            reverse("book_shop_here:employee-update", kwargs={"pk": self.employee.employee_id}),
            form_data,
        )
        self.assertRedirects(response, reverse("book_shop_here:employee-list"))
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.first_name, "Jane")

    def test_employee_delete_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Employee)
        permission = Permission.objects.get(codename="delete_employee", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.post(
            reverse("book_shop_here:employee-delete", kwargs={"pk": self.employee.employee_id})
        )
        self.assertRedirects(response, reverse("book_shop_here:employee-list"))
        self.assertFalse(Employee.objects.filter(employee_id=self.employee.employee_id).exists())

    def test_customer_list_view(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("book_shop_here:customer-list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "book_shop_here/customer_list.html")
        self.assertContains(response, "Bob Jones")
        self.assertContains(response, "Add Customer")

    def test_customer_list_search(self):
        self.client.login(username="testuser", password="testpass")
        # Use explicit name: prefix for deterministic match
        response = self.client.get(reverse("book_shop_here:customer-list"), {"q": "name:Bob"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bob Jones")
        # Prefixed search
        response = self.client.get(
            reverse("book_shop_here:customer-list"), {"q": f"phone:{self.customer.phone_number}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bob Jones")

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
            "mailing_address": "123 St",
        }
        response = self.client.post(reverse("book_shop_here:customer-create"), form_data)
        self.assertRedirects(response, reverse("book_shop_here:customer-list"))
        self.assertTrue(Customer.objects.filter(first_name="Alice").exists())

    def test_customer_update_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Customer)
        permission = Permission.objects.get(codename="change_customer", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.get(
            reverse("book_shop_here:customer-update", kwargs={"pk": self.customer.customer_id})
        )
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
            "mailing_address": "456 St",
        }
        response = self.client.post(
            reverse("book_shop_here:customer-update", kwargs={"pk": self.customer.customer_id}),
            form_data,
        )
        self.assertRedirects(response, reverse("book_shop_here:customer-list"))
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.first_name, "Alice")
        self.assertEqual(self.customer.phone_number, "9876543210")

    def test_customer_delete_view(self):
        self.client.login(username="testuser", password="testpass")
        content_type = ContentType.objects.get_for_model(Customer)
        permission = Permission.objects.get(codename="delete_customer", content_type=content_type)
        self.user.user_permissions.add(permission)
        response = self.client.post(
            reverse("book_shop_here:customer-delete", kwargs={"pk": self.customer.customer_id})
        )
        self.assertRedirects(response, reverse("book_shop_here:customer-list"))
        self.assertFalse(Customer.objects.filter(customer_id=self.customer.customer_id).exists())
