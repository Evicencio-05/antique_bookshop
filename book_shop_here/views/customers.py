import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from ..forms import CustomerForm
from ..models import Customer
from ..utils.search import build_advanced_search

logger = logging.getLogger(__name__)


class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = "book_shop_here/customer_list.html"
    context_object_name = "customers"

    def get_queryset(self):
        qs = Customer.objects.all()
        q = (self.request.GET.get("q") or "").strip()
        if q:
            fields = ["first_name", "last_name", "phone_number", "mailing_address"]
            q_obj, annotations = build_advanced_search(
                q,
                fields=fields,
                nospace_fields=["phone_number"],
                include_unaccent=True,
                mode="AND",
                prefixed_fields={
                    "name": ["first_name", "last_name"],
                    "phone": ["phone_number"],
                    "address": ["mailing_address"],
                },
            )
            if q_obj is not None:
                if annotations:
                    qs = qs.annotate(**annotations)
                qs = qs.filter(q_obj).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        return context


class CustomerCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = "book_shop_here/customer_form.html"
    success_url = reverse_lazy("book_shop_here:customer-list")
    permission_required = "book_shop_here.add_customer"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Customer"
        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Customer added successfully.")
            return response
        except Exception as e:
            logger.error(f"Error adding customer: {e}")
            messages.error(self.request, "Failed to add customer.")
            return self.form_invalid(form)


class CustomerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = "book_shop_here/customer_form.html"
    success_url = reverse_lazy("book_shop_here:customer-list")
    permission_required = "book_shop_here.change_customer"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Customer"
        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Customer updated successfully.")
            return response
        except Exception as e:
            logger.error(f"Error updating customer: {e}")
            messages.error(self.request, "Failed to update customer.")
            return self.form_invalid(form)


class CustomerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Customer
    template_name = "book_shop_here/customer_delete_confirm.html"
    success_url = reverse_lazy("book_shop_here:customer-list")
    permission_required = "book_shop_here.delete_customer"


class CustomerDetailView(LoginRequiredMixin, TemplateView):
    template_name = "book_shop_here/customer_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["customer"] = get_object_or_404(Customer, pk=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        try:
            messages.success(self.request, "Customer removed.")
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error deleting customer: {e}")
            messages.error(self.request, "Failed to delete customer.")
            return self.form_invalid(form)
