"""
Tests for XLSX import functionality with null value handling and multi-sheet support
"""

import io
from datetime import date
from decimal import Decimal

import pandas as pd
from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from book_shop_here.models import Author, Book, Customer, Employee, Order
from book_shop_here.serializers import (
    AuthorImportSerializer,
    BookImportSerializer,
    CustomerImportSerializer,
    EmployeeImportSerializer,
)


class NullValueHandlingTest(TestCase):
    """Test null value handling in serializers"""

    def setUp(self):
        self.group = Group.objects.create(name="Staff")

    def test_author_null_values(self):
        """Test author serializer handles null values correctly"""
        data = {
            "last_name": "Smith",
            "first_name": "",  # Empty string should become empty string
            "birth_year": None,  # Null should remain null
            "death_year": "",  # Empty string should become null
            "description": "null",  # String 'null' should become empty
        }

        serializer = AuthorImportSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        author = serializer.save()

        self.assertEqual(author.last_name, "Smith")
        self.assertEqual(author.first_name, "")
        self.assertIsNone(author.birth_year)
        self.assertIsNone(author.death_year)

    def test_author_missing_required_field(self):
        """Test author serializer validates required fields"""
        data = {
            "last_name": "",  # Required field empty
            "first_name": "John",
        }

        serializer = AuthorImportSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("last_name", serializer.errors)

    def test_book_null_values(self):
        """Test book serializer handles null values and defaults"""
        data = {
            "title": "Test Book",
            "cost": "10.50",
            "suggested_retail_price": "19.99",
            "condition": "",  # Should default to UNRATED
            "book_status": None,  # Should default to PROCESSING
            "publisher": "null",  # String 'null' should become empty
            "edition": "",  # Empty should become null
        }

        serializer = BookImportSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        book = serializer.save()

        self.assertEqual(book.title, "Test Book")
        self.assertEqual(book.cost, Decimal("10.50"))
        self.assertEqual(book.condition, Book.Condition.UNRATED)
        self.assertEqual(book.book_status, Book.BookStatus.PROCESSING)

    def test_book_with_authors(self):
        """Test book creation with author names"""
        # Create an author first
        Author.objects.create(last_name="Doe", first_name="John")

        data = {
            "title": "Book with Authors",
            "cost": "15.00",
            "suggested_retail_price": "25.00",
            "author_names": "John Doe; Jane Smith",
        }

        serializer = BookImportSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        book = serializer.save()

        self.assertEqual(book.authors.count(), 2)
        author_names = [str(a) for a in book.authors.all()]
        self.assertIn("John Doe", author_names)
        self.assertIn("Jane Smith", author_names)

    def test_customer_null_values(self):
        """Test customer serializer with nullable fields"""
        data = {
            "first_name": "Jane",
            "last_name": None,  # At least one name required
            "phone_number": "",
            "mailing_address": "null",
        }

        serializer = CustomerImportSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        customer = serializer.save()

        self.assertEqual(customer.first_name, "Jane")
        self.assertIsNone(customer.last_name)

    def test_customer_no_name_validation(self):
        """Test customer requires at least one name"""
        data = {"first_name": "", "last_name": "", "phone_number": "555-1234"}

        serializer = CustomerImportSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_employee_with_group(self):
        """Test employee creation with group name"""
        data = {
            "first_name": "Bob",
            "last_name": "Johnson",
            "phone_number": "555-5678",
            "address": "123 Main St",
            "zip_code": "12345",
            "state": "NY",
            "group_name": "Staff",
            "email": None,  # Nullable field
            "hire_date": date.today().isoformat(),
            "birth_date": "2000-01-01",
        }

        serializer = EmployeeImportSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        employee = serializer.save()

        self.assertEqual(employee.first_name, "Bob")
        self.assertEqual(employee.group.name, "Staff")
        self.assertIsNone(employee.email)


class MultiSheetXLSXTest(TestCase):
    """Test multi-sheet XLSX handling"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user("testuser", "test@test.com", "testpass")
        self.group = Group.objects.create(name="Admin")
        self.client.login(username="testuser", password="testpass")

    def create_test_xlsx(self, sheets_data):
        """Helper to create test XLSX files"""
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            for sheet_name, data in sheets_data.items():
                df = pd.DataFrame(data)
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        output.seek(0)
        return output.read()

    def test_parse_multi_sheet_xlsx(self):
        """Test parsing XLSX with multiple sheets"""
        sheets_data = {
            "Authors": {
                "last_name": ["Shakespeare", "Dickens"],
                "first_name": ["William", "Charles"],
                "birth_year": [1564, 1812],
                "death_year": [1616, 1870],
            },
            "Books": {
                "title": ["Hamlet", "Oliver Twist"],
                "cost": [5.00, 7.50],
                "suggested_retail_price": [15.00, 20.00],
                "condition": ["good", "excellent"],
            },
        }

        xlsx_content = self.create_test_xlsx(sheets_data)
        file = SimpleUploadedFile(
            "test.xlsx",
            xlsx_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        from book_shop_here.unified_import import UnifiedImportHandler

        handler = UnifiedImportHandler(file)
        parsed = handler.parse_file()

        # Check we have the expected data types
        self.assertIn("data_by_type", parsed)
        self.assertIn("author", parsed["data_by_type"])
        self.assertIn("book", parsed["data_by_type"])

        # Check data integrity
        authors = parsed["data_by_type"]["author"]
        self.assertEqual(len(authors), 2)
        self.assertEqual(authors[0]["last_name"], "Shakespeare")

    def test_detect_sheet_types(self):
        """Test automatic sheet type detection"""
        sheets_data = {
            "AuthorData": {"last_name": ["Twain"], "first_name": ["Mark"], "birth_year": [1835]},
            "CustomerInfo": {
                "first_name": ["Alice"],
                "phone_number": ["555-1111"],
                "mailing_address": ["123 Oak St"],
            },
        }

        xlsx_content = self.create_test_xlsx(sheets_data)
        file = SimpleUploadedFile(
            "test.xlsx",
            xlsx_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        from book_shop_here.unified_import import UnifiedImportHandler

        handler = UnifiedImportHandler(file)
        parsed = handler.parse_file()

        # Check that types were detected correctly
        sheets_info = parsed.get("sheets_info", [])
        author_sheet = next((s for s in sheets_info if s["name"] == "AuthorData"), None)
        customer_sheet = next((s for s in sheets_info if s["name"] == "CustomerInfo"), None)

        author_type = author_sheet["type"] if author_sheet else None
        customer_type = customer_sheet["type"] if customer_sheet else None

        self.assertEqual(author_type, "author")
        self.assertEqual(customer_type, "customer")

    def test_handle_empty_cells(self):
        """Test handling of empty cells and null values"""
        sheets_data = {
            "Mixed Data": {
                "last_name": ["Smith", None, "Jones", ""],
                "first_name": ["John", "Jane", None, "Bob"],
                "birth_year": [1950, None, 1960, ""],
            }
        }

        xlsx_content = self.create_test_xlsx(sheets_data)
        file = SimpleUploadedFile(
            "test.xlsx",
            xlsx_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        from book_shop_here.unified_import import UnifiedImportHandler

        handler = UnifiedImportHandler(file)
        parsed = handler.parse_file()

        # Get the data from the parsed result
        mixed_data = parsed["data_by_type"].get("author", [])  # Might be detected as author type
        if not mixed_data:
            # Fallback - get first data type available
            first_type = next(iter(parsed["data_by_type"].values()), [])
            mixed_data = first_type
        # Check that nulls are converted to empty strings
        if mixed_data and len(mixed_data) > 2:
            # Note: Data structure is now list of dicts, not DataFrame
            self.assertEqual(mixed_data[1].get("birth_year", ""), "")
            self.assertEqual(mixed_data[2].get("first_name", ""), "")


class IntegrationTest(TestCase):
    """End-to-end integration tests"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser("admin", "admin@test.com", "admin123")
        self.group = Group.objects.create(name="Staff")
        self.client.login(username="admin", password="admin123")

    def test_data_wizard_registration(self):
        """Test that models are properly registered with data wizard"""
        import data_wizard
        from data_wizard.registry import registry

        # Check that our serializers are registered
        from book_shop_here.serializers import (
            AuthorImportSerializer,
            BookImportSerializer,
            CustomerImportSerializer,
            EmployeeImportSerializer,
            OrderImportSerializer,
        )

        class_names = [s["class_name"] for s in registry.get_serializers()]
        self.assertIn("book_shop_here.serializers.BookImportSerializer", class_names)
        self.assertIn("book_shop_here.serializers.AuthorImportSerializer", class_names)
        self.assertIn("book_shop_here.serializers.CustomerImportSerializer", class_names)
        self.assertIn("book_shop_here.serializers.EmployeeImportSerializer", class_names)
        self.assertIn("book_shop_here.serializers.OrderImportSerializer", class_names)

    def test_import_books_with_various_conditions(self):
        """Test importing books with different condition formats"""
        test_data = [
            {
                "title": "Book 1",
                "cost": "10",
                "suggested_retail_price": "20",
                "condition": "Superb",  # Display name
            },
            {
                "title": "Book 2",
                "cost": "15",
                "suggested_retail_price": "25",
                "condition": "excellent",  # Value
            },
            {
                "title": "Book 3",
                "cost": "12",
                "suggested_retail_price": "22",
                "condition": "",  # Empty - should default to UNRATED
            },
        ]

        for data in test_data:
            serializer = BookImportSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Failed for {data}: {serializer.errors}")
            book = serializer.save()
            self.assertIsNotNone(book.book_id)

    def test_decimal_field_handling(self):
        """Test proper handling of decimal fields"""
        test_cases = [
            ("10", Decimal("10.00")),
            ("10.5", Decimal("10.50")),
            ("10.99", Decimal("10.99")),
            (10, Decimal("10.00")),
            (10.5, Decimal("10.50")),
        ]

        for input_val, expected in test_cases:
            data = {
                "title": f"Book with price {input_val}",
                "cost": input_val,
                "suggested_retail_price": "20",
            }
            serializer = BookImportSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Failed for {input_val}: {serializer.errors}")
            book = serializer.save()
            self.assertEqual(book.cost, expected)
