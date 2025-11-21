from datetime import timedelta
from decimal import Decimal
from random import choice, randint  # noqa: S311  # Dev seeding only

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import Author, Book, Customer, Employee, Order


class Command(BaseCommand):
    help = "Seed development data for the Antique Bookshop app. Safe to run multiple times."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding development data..."))

        # Roles
        owner_group, _ = Group.objects.get_or_create(name="Owner")
        manager_group, _ = Group.objects.get_or_create(name="Assistant Manager")
        staff_group, _ = Group.objects.get_or_create(name="Staff")

        # Employees + Users
        if not Employee.objects.exists():
            self.stdout.write("Creating employees and users...")
            for first, last, grp in [
                ("Alice", "Owner", owner_group),
                ("Bob", "Manager", manager_group),
                ("Carol", "Staff", staff_group),
            ]:
                username = f"{first.lower()}.{last.lower()}"
                user, _ = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "first_name": first,
                        "last_name": last,
                        "email": f"{username}@example.com",
                    },
                )
                user.set_password("password")
                user.save()
                user.groups.add(grp)
                Employee.objects.get_or_create(
                    user=user,
                    first_name=first,
                    last_name=last,
                    phone_number="555-0100",
                    address="123 Main St",
                    group=grp,
                    email=f"{username}@example.com",
                )

        # Authors
        if Author.objects.count() < 10:
            self.stdout.write("Creating authors...")
            for i in range(10):
                Author.objects.get_or_create(
                    last_name=f"Author{i}",
                    defaults={"first_name": f"First{i}", "description": "A notable author"},
                )

        # Books
        if Book.objects.count() < 30:
            self.stdout.write("Creating books...")
            authors = list(Author.objects.all())
            for i in range(30):
                b, created = Book.objects.get_or_create(
                    legacy_id=f"B{i:04d}",
                    defaults={
                        "title": f"Sample Book {i}",
                        "cost": Decimal("5.00") + Decimal(i % 5),
                        "suggested_retail_price": Decimal("10.00") + Decimal(i % 10),
                        "condition": Book.Condition.UNRATED,
                        "book_status": Book.BookStatus.AVAILABLE,
                    },
                )
                if created:
                    b.authors.set(
                        authors[max(0, i % len(authors) - 1) : (i % len(authors)) + 1]
                        or authors[:1]
                    )

        # Customers
        if Customer.objects.count() < 10:
            self.stdout.write("Creating customers...")
            for i in range(10):
                Customer.objects.get_or_create(
                    last_name=f"Customer{i}",
                    first_name=f"C{i}",
                    phone_number=f"555-01{i:02d}",
                    mailing_address=f"{100 + i} Market St",
                )

        # Orders
        if Order.objects.count() < 20:
            self.stdout.write("Creating orders...")
            employees = list(Employee.objects.all())
            customers = list(Customer.objects.all())
            books = list(Book.objects.all())
            for _i in range(20):  # noqa: B007
                cust = choice(customers)  # noqa: S311
                emp = choice(employees)  # noqa: S311
                order = Order.objects.create(
                    customer_id=cust,
                    employee_id=emp,
                    order_date=timezone.now().date() - timedelta(days=randint(0, 20)),  # noqa: S311
                    sale_amount=Decimal("0.00"),
                    discount_amount=Decimal("0.00"),
                    payment_method=choice(  # noqa: S311
                        [
                            Order.PaymentMethod.CASH,
                            Order.PaymentMethod.CREDIT,
                            Order.PaymentMethod.CHECK,
                        ]
                    ),
                    order_status=choice([Order.OrderStatus.TO_SHIP, Order.OrderStatus.PICKUP]),  # noqa: S311
                )
                selected = [choice(books) for _ in range(randint(1, 3))]  # noqa: S311
                order.books.set(selected)
                # Auto-calc approximate amount
                total = sum(b.suggested_retail_price for b in selected)
                order.sale_amount = total
                order.save()

        self.stdout.write(self.style.SUCCESS("Seeding complete."))
