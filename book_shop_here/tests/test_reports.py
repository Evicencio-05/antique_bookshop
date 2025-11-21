from datetime import date

from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase
from django.urls import reverse

from book_shop_here.models import Author, Book, Customer, Employee, GroupProfile, Order


class SalesReportsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")

        # Minimal data
        self.group = Group.objects.create(name="Owner (Reports)")
        GroupProfile.objects.create(group=self.group)
        self.user.groups.add(self.group)
        # Ensure the role has permissions required to access reports
        ct = ContentType.objects.get(app_label="book_shop_here", model="order")
        needed = Permission.objects.filter(
            content_type=ct, codename__in=["view_sales_reports", "view_employee_sales"]
        )
        # If they don't exist yet (e.g., migrations timing in test runner), create minimal stand-ins
        if needed.count() < 2:
            for codename, name in (
                ("view_sales_reports", "Can view sales reports"),
                ("view_employee_sales", "Can view employee sales"),
            ):
                Permission.objects.get_or_create(
                    codename=codename, content_type=ct, defaults={"name": name}
                )
            needed = Permission.objects.filter(
                content_type=ct, codename__in=["view_sales_reports", "view_employee_sales"]
            )
        self.group.permissions.add(*list(needed))

        self.emp_user = User.objects.create_user(username="empuser", password="testpass")
        self.employee = Employee.objects.create(
            first_name="Ella",
            last_name="Seller",
            address="123 St",
            zip_code="12345",
            state="CA",
            birth_date=date(1990, 1, 1),
            phone_number="1234567890",
            group=self.group,
            user=self.emp_user,
            email="ella@example.com",
        )

        self.customer1 = Customer.objects.create(first_name="Alice", last_name="Smith")
        self.customer2 = Customer.objects.create(first_name="Bob", last_name="Jones")

        self.author = Author.objects.create(first_name="Jane", last_name="Austen")
        self.book1 = Book.objects.create(
            legacy_id="bk000001",
            title="Pride and Prejudice",
            cost=10.00,
            suggested_retail_price=20.00,
            book_status="available",
        )
        self.book2 = Book.objects.create(
            legacy_id="bk000002",
            title="Sense and Sensibility",
            cost=12.00,
            suggested_retail_price=24.00,
            book_status="available",
        )
        self.book1.authors.add(self.author)
        self.book2.authors.add(self.author)

        # Completed order (shipped) with 2 books to customer1
        self.order1 = Order.objects.create(
            customer_id=self.customer1,
            employee_id=self.employee,
            sale_amount=44.00,
            discount_amount=4.00,
            payment_method="cash",
            order_status="shipped",
        )
        self.order1.books.add(self.book1, self.book2)

        # Completed order (picked_up) with 1 book to customer2
        self.order2 = Order.objects.create(
            customer_id=self.customer2,
            employee_id=self.employee,
            sale_amount=20.00,
            discount_amount=0,
            payment_method="credit",
            order_status="picked_up",
        )
        self.order2.books.add(self.book1)

        # Open order should be ignored in completed metrics
        self.order3 = Order.objects.create(
            customer_id=self.customer1,
            employee_id=self.employee,
            sale_amount=24.00,
            payment_method="check",
            order_status="to_ship",
        )
        self.order3.books.add(self.book2)

    def test_employee_sales_view(self):
        url = reverse("book_shop_here:employee-sales", args=[self.employee.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("totals", resp.context)
        totals = resp.context["totals"]
        # Completed books sold: order1(2) + order2(1) = 3
        self.assertEqual(totals["books"], 3)
        # Revenue is sum of sale_amount for completed orders: 44 + 20 = 64
        self.assertEqual(float(totals["revenue"]), 64.0)
        # Frequent customers include both; Alice has 1 completed order, Bob has 1
        customers = list(resp.context["frequent_customers"])
        self.assertGreaterEqual(len(customers), 1)

    def test_sales_dashboard_view(self):
        url = reverse("book_shop_here:sales-dashboard")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        summary = resp.context["summary"]
        # Orders: 2 completed
        self.assertEqual(summary["orders"], 2)
        # Books sold: 3
        self.assertEqual(summary["books_sold"], 3)
        # Revenue: 64 (sale_amount already net of discount)
        self.assertEqual(float(summary["revenue"]), 64.0)
        # Payment breakdown includes cash and credit
        methods = {row["payment_method"] for row in resp.context["payment_breakdown"]}
        self.assertTrue({"cash", "credit"}.issubset(methods))
