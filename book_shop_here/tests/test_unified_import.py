"""
Tests for unified import functionality (CSV and XML)
"""

import csv
import io
import xml.etree.ElementTree as ET
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from book_shop_here.models import Author, Book, Customer
from book_shop_here.unified_import import UnifiedImportHandler


class CSVImportTest(TestCase):
    """Test CSV import functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user("testuser", "test@test.com", "testpass")
        self.group = Group.objects.create(name="Staff")
        self.client.login(username="testuser", password="testpass")

    def create_csv_content(self, headers, rows):
        """Helper to create CSV content"""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        return output.getvalue().encode("utf-8")

    def test_parse_author_csv(self):
        """Test parsing CSV with author data"""
        headers = ["last_name", "first_name", "birth_year", "death_year", "description"]
        rows = [
            {
                "last_name": "Austen",
                "first_name": "Jane",
                "birth_year": "1775",
                "death_year": "1817",
                "description": "English novelist",
            },
            {
                "last_name": "Twain",
                "first_name": "Mark",
                "birth_year": "1835",
                "death_year": "1910",
                "description": "",
            },
            {
                "last_name": "Christie",
                "first_name": "",
                "birth_year": "null",
                "death_year": "",
                "description": "Mystery writer",
            },
        ]

        csv_content = self.create_csv_content(headers, rows)
        file = SimpleUploadedFile("authors.csv", csv_content, content_type="text/csv")

        handler = UnifiedImportHandler(file)
        self.assertEqual(handler.file_type, "csv")

        result = handler.parse_file()
        self.assertNotIn("error", result)
        self.assertEqual(len(result["data_by_type"].get("author", [])), 3)

        # Check null handling
        authors = result["data_by_type"]["author"]
        self.assertEqual(authors[0]["first_name"], "Jane")
        self.assertEqual(authors[2]["first_name"], "")  # Empty string preserved
        self.assertEqual(authors[2]["birth_year"], "")  # 'null' converted to empty

    def test_parse_book_csv_with_special_characters(self):
        """Test CSV parsing with special characters and different delimiters"""
        csv_content = "title;cost;suggested_retail_price;condition\n"
        csv_content += '"War & Peace";15.50;25.99;excellent\n'
        csv_content += '"The "Great" Gatsby";12.00;20.00;good\n'
        csv_content += "Simple Title;10;15;null\n"

        file = SimpleUploadedFile("books.csv", csv_content.encode("utf-8"), content_type="text/csv")

        handler = UnifiedImportHandler(file)
        result = handler.parse_file()

        self.assertNotIn("error", result)
        books = result["data_by_type"].get("book", [])
        self.assertEqual(len(books), 3)
        self.assertEqual(books[0]["title"], "War & Peace")

    def test_csv_type_detection(self):
        """Test automatic type detection for CSV files"""
        test_cases = [
            # Customer CSV
            (["first_name", "last_name", "phone_number", "mailing_address"], "customer"),
            # Employee CSV
            (["first_name", "last_name", "email", "hire_date", "group"], "employee"),
            # Order CSV
            (["customer_name", "employee_name", "sale_amount", "payment_method"], "order"),
        ]

        for headers, expected_type in test_cases:
            rows = [{h: f"value_{h}" for h in headers}]
            csv_content = self.create_csv_content(headers, rows)
            file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

            handler = UnifiedImportHandler(file)
            result = handler.parse_file()

            detected_type = result["sheets_info"][0]["type"]
            self.assertEqual(
                detected_type,
                expected_type,
                f"Failed to detect {expected_type} from headers {headers}",
            )

    def test_csv_encoding_detection(self):
        """Test CSV files with different encodings"""
        # Latin-1 encoded content with special characters
        text = "Müller,José,Château"
        csv_content = f"last_name,first_name,description\n{text}"

        for encoding in ["utf-8", "latin-1", "iso-8859-1"]:
            encoded = csv_content.encode(encoding)
            file = SimpleUploadedFile("test.csv", encoded, content_type="text/csv")

            handler = UnifiedImportHandler(file)
            result = handler.parse_file()

            # Should handle without errors
            self.assertNotIn("error", result)


class XMLImportTest(TestCase):
    """Test XML import functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user("testuser", "test@test.com", "testpass")
        self.client.login(username="testuser", password="testpass")

    def create_xml_content(self, root_tag, items):
        """Helper to create XML content"""
        root = ET.Element(root_tag)
        for item_data in items:
            item = ET.SubElement(root, item_data.get("_tag", "item"))
            for key, value in item_data.items():
                if key != "_tag":
                    child = ET.SubElement(item, key)
                    child.text = str(value) if value is not None else ""
        return ET.tostring(root, encoding="utf-8")

    def test_parse_author_xml(self):
        """Test parsing XML with author data"""
        authors_data = [
            {
                "_tag": "author",
                "last_name": "Hemingway",
                "first_name": "Ernest",
                "birth_year": "1899",
                "death_year": "1961",
            },
            {
                "_tag": "author",
                "last_name": "Orwell",
                "first_name": "George",
                "birth_year": "1903",
                "death_year": "null",
            },
            {
                "_tag": "author",
                "last_name": "King",
                "first_name": None,
                "birth_year": "1947",
                "death_year": "",
            },
        ]

        xml_content = self.create_xml_content("authors", authors_data)
        file = SimpleUploadedFile("authors.xml", xml_content, content_type="text/xml")

        handler = UnifiedImportHandler(file)
        self.assertEqual(handler.file_type, "xml")

        result = handler.parse_file()
        self.assertNotIn("error", result)

        authors = result["data_by_type"].get("author", [])
        self.assertEqual(len(authors), 3)

        # Check null handling
        self.assertEqual(authors[1]["death_year"], "")  # 'null' converted to empty
        self.assertEqual(authors[2]["first_name"], "")  # None converted to empty

    def test_parse_nested_xml(self):
        """Test parsing XML with nested structure"""
        xml_content = """<?xml version="1.0"?>
        <books>
            <book>
                <title>Advanced Python</title>
                <cost>30.00</cost>
                <suggested_retail_price>50.00</suggested_retail_price>
                <publisher>
                    <name>Tech Publishers</name>
                    <location>New York</location>
                </publisher>
                <condition>excellent</condition>
            </book>
            <book>
                <title>Data Science Basics</title>
                <cost>25.50</cost>
                <suggested_retail_price>40.00</suggested_retail_price>
                <publisher>null</publisher>
                <condition>good</condition>
            </book>
        </books>"""

        file = SimpleUploadedFile("books.xml", xml_content.encode("utf-8"), content_type="text/xml")

        handler = UnifiedImportHandler(file)
        result = handler.parse_file()

        self.assertNotIn("error", result)
        books = result["data_by_type"].get("book", [])
        self.assertEqual(len(books), 2)

        # Check nested handling
        self.assertIn("publisher", books[0])
        # Nested dict should be converted
        if isinstance(books[0]["publisher"], dict):
            self.assertIn("name", books[0]["publisher"])

    def test_xml_with_attributes(self):
        """Test XML parsing with attributes"""
        xml_content = """<?xml version="1.0"?>
        <customers>
            <customer id="1" status="active">
                <first_name>Alice</first_name>
                <last_name>Smith</last_name>
                <phone_number>555-0101</phone_number>
                <mailing_address>123 Main St</mailing_address>
            </customer>
            <customer id="2" status="inactive">
                <first_name>Bob</first_name>
                <last_name>Jones</last_name>
                <phone_number>null</phone_number>
                <mailing_address></mailing_address>
            </customer>
        </customers>"""

        file = SimpleUploadedFile(
            "customers.xml", xml_content.encode("utf-8"), content_type="text/xml"
        )

        handler = UnifiedImportHandler(file)
        result = handler.parse_file()

        self.assertNotIn("error", result)
        customers = result["data_by_type"].get("customer", [])
        self.assertEqual(len(customers), 2)

        # Check attributes are included
        self.assertIn("id", customers[0])
        self.assertIn("status", customers[0])
        self.assertEqual(customers[0]["id"], "1")

        # Check null handling
        self.assertEqual(customers[1]["phone_number"], "")

    def test_xml_type_detection(self):
        """Test automatic type detection for XML"""
        test_cases = [
            ("<books><book><title>Test</title><cost>10</cost></book></books>", "book"),
            ("<authors><author><last_name>Test</last_name></author></authors>", "author"),
            ("<orders><order><sale_amount>100</sale_amount></order></orders>", "order"),
        ]

        for xml_str, expected_type in test_cases:
            file = SimpleUploadedFile("test.xml", xml_str.encode("utf-8"), content_type="text/xml")

            handler = UnifiedImportHandler(file)
            result = handler.parse_file()

            self.assertIn(
                expected_type, result["data_by_type"], f"Failed to detect {expected_type} from XML"
            )


class UnifiedImportIntegrationTest(TestCase):
    """Integration tests for unified import"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser("admin", "admin@test.com", "admin123")
        self.group = Group.objects.create(name="Staff")
        self.client.login(username="admin", password="admin123")

    def test_import_csv_authors(self):
        """Test end-to-end CSV import of authors"""
        headers = ["last_name", "first_name", "birth_year"]
        rows = [
            {"last_name": "Shakespeare", "first_name": "William", "birth_year": "1564"},
            {"last_name": "Poe", "first_name": "Edgar Allan", "birth_year": "1809"},
        ]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        csv_content = output.getvalue()

        response = self.client.post(
            "/import/upload/",
            {
                "file": SimpleUploadedFile(
                    "authors.csv", csv_content.encode("utf-8"), content_type="text/csv"
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["file_type"], "csv")

    def test_import_xml_books(self):
        """Test end-to-end XML import of books"""
        xml_content = """<?xml version="1.0"?>
        <books>
            <book>
                <title>Test Book 1</title>
                <cost>20.00</cost>
                <suggested_retail_price>35.00</suggested_retail_price>
                <condition>new</condition>
            </book>
            <book>
                <title>Test Book 2</title>
                <cost>15.50</cost>
                <suggested_retail_price>25.00</suggested_retail_price>
                <condition>good</condition>
            </book>
        </books>"""

        response = self.client.post(
            "/import/upload/",
            {
                "file": SimpleUploadedFile(
                    "books.xml", xml_content.encode("utf-8"), content_type="text/xml"
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["file_type"], "xml")
        self.assertIn("book", data["data"]["data_by_type"])

    def test_unsupported_format(self):
        """Test handling of unsupported file formats"""
        response = self.client.post(
            "/import/upload/",
            {
                "file": SimpleUploadedFile(
                    "test.txt", b"Some text content", content_type="text/plain"
                )
            },
        )

        # Should still try to parse as CSV if text/plain
        self.assertEqual(response.status_code, 200)

        # Try truly unsupported format
        response = self.client.post(
            "/import/upload/",
            {
                "file": SimpleUploadedFile(
                    "test.pdf", b"PDF content", content_type="application/pdf"
                )
            },
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
