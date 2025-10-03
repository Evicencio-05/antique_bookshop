from django.template import Context, Template
from django.test import TestCase

from book_shop_here.forms import (
    AuthorForm,
    BookForm,
    CustomerForm,
    EmployeeForm,
    GroupForm,
    OrderForm,
)


class CrispyRenderTests(TestCase):
    def render_form(self, form):
        tmpl = Template("""{% load crispy_forms_tags %}{{ form|crispy }}""")
        return tmpl.render(Context({"form": form}))

    def test_author_form_renders(self):
        html = self.render_form(AuthorForm())
        self.assertIn('name="last_name"', html)

    def test_book_form_renders(self):
        html = self.render_form(BookForm())
        self.assertIn('name="title"', html)

    def test_customer_form_renders(self):
        html = self.render_form(CustomerForm())
        self.assertIn('name="first_name"', html)

    def test_employee_form_renders(self):
        html = self.render_form(EmployeeForm())
        self.assertIn('name="first_name"', html)

    def test_group_form_renders(self):
        html = self.render_form(GroupForm())
        self.assertIn('name="name"', html)

    def test_order_form_renders(self):
        html = self.render_form(OrderForm())
        self.assertIn('name="customer_id"', html)
