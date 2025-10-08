import logging

from django.contrib.auth.models import Group
from django.shortcuts import redirect
from django.views.generic import TemplateView

from ..models import Author, Book, Customer, Employee, Order
from ..utils.search import build_advanced_search

logger = logging.getLogger(__name__)


class DocsView(TemplateView):
    template_name = "book_shop_here/docs.html"


class HomeView(TemplateView):
    template_name = "book_shop_here/home.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("book_shop_here:login")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = (self.request.GET.get("q") or "").strip()
        context["q"] = q

        context["recent_orders"] = Order.objects.select_related(
            "customer_id", "employee_id"
        ).order_by("-order_date")[:5]
        context["recent_books"] = Book.objects.order_by("-pk")[:5]
        context["recent_authors"] = Author.objects.order_by("-pk")[:5]
        context["recent_customers"] = Customer.objects.order_by("-pk")[:5]
        context["recent_employees"] = Employee.objects.select_related("group").order_by("-pk")[:5]

        # My employee linkage for "My Sales" link
        if self.request.user.is_authenticated:
            context["my_employee"] = Employee.objects.filter(user=self.request.user).first()

        results = {}
        if q:
            # Books
            b_qs = Book.objects.filter(book_status="available").prefetch_related("authors")
            b_fields = [
                "title",
                "legacy_id",
                "authors__first_name",
                "authors__last_name",
                "publisher",
                "rating",
            ]
            rating_map = {label.lower(): value for value, label in Book.Rating.choices}
            b_q, b_ann = build_advanced_search(
                q,
                fields=b_fields,
                nospace_fields=["legacy_id", "title"],
                include_unaccent=True,
                mode="AND",
                prefixed_fields={
                    "title": ["title"],
                    "author": ["authors__first_name", "authors__last_name"],
                    "legacy": ["legacy_id"],
                    "publisher": ["publisher"],
                    "rating": ["rating"],
                },
                choice_value_map={"rating": rating_map},
            )
            if b_q is not None:
                if b_ann:
                    b_qs = b_qs.annotate(**b_ann)
                results["books"] = list(b_qs.filter(b_q).distinct()[:5])

            # Authors
            a_qs = Author.objects.all()
            a_q, a_ann = build_advanced_search(
                q,
                fields=["first_name", "last_name", "description"],
                nospace_fields=[],
                include_unaccent=True,
                mode="AND",
                prefixed_fields={
                    "first": ["first_name"],
                    "last": ["last_name"],
                    "desc": ["description"],
                },
            )
            if a_q is not None:
                if a_ann:
                    a_qs = a_qs.annotate(**a_ann)
                results["authors"] = list(a_qs.filter(a_q).distinct()[:5])

            # Customers
            c_qs = Customer.objects.all()
            c_q, c_ann = build_advanced_search(
                q,
                fields=["first_name", "last_name", "phone_number", "mailing_address"],
                nospace_fields=["phone_number"],
                include_unaccent=True,
                mode="AND",
                prefixed_fields={
                    "name": ["first_name", "last_name"],
                    "phone": ["phone_number"],
                    "address": ["mailing_address"],
                },
            )
            if c_q is not None:
                if c_ann:
                    c_qs = c_qs.annotate(**c_ann)
                results["customers"] = list(c_qs.filter(c_q).distinct()[:5])

            # Employees
            e_qs = Employee.objects.select_related("group")
            e_q, e_ann = build_advanced_search(
                q,
                fields=["first_name", "last_name", "email", "group__name"],
                nospace_fields=[],
                include_unaccent=True,
                mode="AND",
                prefixed_fields={
                    "name": ["first_name", "last_name"],
                    "email": ["email"],
                    "role": ["group__name"],
                },
            )
            if e_q is not None:
                if e_ann:
                    e_qs = e_qs.annotate(**e_ann)
                results["employees"] = list(e_qs.filter(e_q).distinct()[:5])

            # Orders
            o_qs = Order.objects.select_related("customer_id", "employee_id").prefetch_related(
                "books"
            )
            status_map = {label.lower(): value for value, label in Order.OrderStatus.choices}
            payment_map = {label.lower(): value for value, label in Order.PaymentMethod.choices}
            o_q, o_ann = build_advanced_search(
                q,
                fields=[
                    "customer_id__first_name",
                    "customer_id__last_name",
                    "employee_id__first_name",
                    "employee_id__last_name",
                    "payment_method",
                    "order_status",
                    "books__title",
                ],
                nospace_fields=["customer_id__last_name", "employee_id__last_name"],
                include_unaccent=True,
                mode="AND",
                numeric_eq_fields=["order_id"],
                prefixed_fields={
                    "id": ["order_id"],
                    "customer": ["customer_id__first_name", "customer_id__last_name"],
                    "employee": ["employee_id__first_name", "employee_id__last_name"],
                    "status": ["order_status"],
                    "payment": ["payment_method"],
                    "book": ["books__title"],
                },
                choice_value_map={"order_status": status_map, "payment_method": payment_map},
            )
            if o_q is not None:
                if o_ann:
                    o_qs = o_qs.annotate(**o_ann)
                results["orders"] = list(o_qs.filter(o_q).distinct()[:5])

            # Roles (Groups)
            g_qs = Group.objects.select_related("profile").prefetch_related("permissions").all()
            g_q, g_ann = build_advanced_search(
                q,
                fields=[
                    "name",
                    "profile__description",
                    "permissions__codename",
                    "permissions__name",
                ],
                nospace_fields=["name"],
                include_unaccent=True,
                mode="AND",
                prefixed_fields={
                    "name": ["name"],
                    "desc": ["profile__description"],
                    "perm": ["permissions__codename", "permissions__name"],
                },
            )
            if g_q is not None:
                if g_ann:
                    g_qs = g_qs.annotate(**g_ann)
                results["roles"] = list(g_qs.filter(g_q).distinct()[:5])

        context["lookup_results"] = results
        return context
