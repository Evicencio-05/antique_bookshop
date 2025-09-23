from django.test import TestCase
from .models import Book, Author, Employee, Role, Customer, Order
from datetime import date

class BookTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author1 = Author.objects.create(last_name='Charles', first_name='Bob')
        cls.book1 = Book.objects.create(title='My Title', cost='20.0', retail_price='40.0', publication_date=date(1900,1,1))

    def test_book_author_m2m(self):
        self.book1.authors.add(self.author1)

        self.assertEqual(self.book1.authors.count(), 1)
        self.assertIn(self.author1, self.book1.authors.all())