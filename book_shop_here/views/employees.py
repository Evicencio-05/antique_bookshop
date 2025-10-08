import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from ..forms import EmployeeForm
from ..models import Employee
from ..utils.search import build_advanced_search

logger = logging.getLogger(__name__)


class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = "book_shop_here/employee_list.html"
    context_object_name = "employees"

    def get_queryset(self):
        qs = Employee.objects.select_related("group")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            fields = ["first_name", "last_name", "email", "group__name"]
            q_obj, annotations = build_advanced_search(
                q,
                fields=fields,
                nospace_fields=[],
                include_unaccent=True,
                mode="AND",
                prefixed_fields={
                    "name": ["first_name", "last_name"],
                    "email": ["email"],
                    "role": ["group__name"],
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


class EmployeeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "book_shop_here/employee_form.html"
    success_url = reverse_lazy("book_shop_here:employee-list")
    permission_required = "book_shop_here.add_employee"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Employee"
        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Employee added successfully.")
            return response
        except Exception as e:
            logger.error(f"Error adding employee: {e}")
            messages.error(self.request, "Failed to add employee.")
            return self.form_invalid(form)


class EmployeeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "book_shop_here/employee_form.html"
    success_url = reverse_lazy("book_shop_here:employee-list")
    permission_required = "book_shop_here.change_employee"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Employee"
        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Employee updated successfully.")
            return response
        except Exception as e:
            logger.error(f"Error updating employee: {e}")
            messages.error(self.request, "Failed to update employee.")
            return self.form_invalid(form)


class EmployeeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Employee
    template_name = "book_shop_here/employee_delete_confirm.html"
    success_url = reverse_lazy("book_shop_here:employee-list")
    permission_required = "book_shop_here.delete_employee"
    raise_exception = True


class EmployeeDetailView(LoginRequiredMixin, TemplateView):
    template_name = "book_shop_here/employee_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["employee"] = get_object_or_404(
            Employee.objects.select_related("group"), pk=self.kwargs["pk"]
        )
        return context

    def form_valid(self, form):
        try:
            messages.success(self.request, "Employee removed.")
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error deleting employee: {e}")
            messages.error(self.request, "Failed to delete employee.")
            return self.form_invalid(form)
