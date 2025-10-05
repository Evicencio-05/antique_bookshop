from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase
from django.urls import reverse

from book_shop_here.models import Author, Book, Customer, Employee, GroupProfile, Order


class FormActionsStylesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="tester", password="pass1234")
        self.client.login(username="tester", password="pass1234")

        # Grant add permissions used by create views
        perms = [
            ("book_shop_here", "book", "add_book"),
            ("book_shop_here", "author", "add_author"),
            ("book_shop_here", "customer", "add_customer"),
            ("book_shop_here", "employee", "add_employee"),
            ("book_shop_here", "order", "add_order"),
            ("auth", "group", "add_group"),
        ]
        for app_label, model, codename in perms:
            ct = ContentType.objects.get(app_label=app_label, model=model)
            perm = Permission.objects.get(content_type=ct, codename=codename)
            self.user.user_permissions.add(perm)

    def assertButtons(self, response):
        self.assertContains(response, "bg-green-600")
        self.assertContains(response, "bg-red-600")

    def test_book_create_buttons_colored(self):
        resp = self.client.get(reverse("book_shop_here:book-create"))
        self.assertEqual(resp.status_code, 200)
        self.assertButtons(resp)

    def test_author_create_buttons_colored(self):
        resp = self.client.get(reverse("book_shop_here:author-create"))
        self.assertEqual(resp.status_code, 200)
        self.assertButtons(resp)

    def test_order_create_buttons_colored(self):
        resp = self.client.get(reverse("book_shop_here:order-create"))
        self.assertEqual(resp.status_code, 200)
        self.assertButtons(resp)

    def test_customer_create_buttons_colored(self):
        resp = self.client.get(reverse("book_shop_here:customer-create"))
        self.assertEqual(resp.status_code, 200)
        self.assertButtons(resp)

    def test_employee_create_buttons_colored(self):
        resp = self.client.get(reverse("book_shop_here:employee-create"))
        self.assertEqual(resp.status_code, 200)
        self.assertButtons(resp)

    def test_group_create_buttons_colored(self):
        resp = self.client.get(reverse("book_shop_here:group-create"))
        self.assertEqual(resp.status_code, 200)
        self.assertButtons(resp)
