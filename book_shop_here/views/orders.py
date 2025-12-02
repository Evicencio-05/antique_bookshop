import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView, View

from ..forms import OrderForm
from ..models import Book, Order
from ..utils.search import build_advanced_search

logger = logging.getLogger(__name__)


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "book_shop_here/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        qs = Order.objects.select_related("customer_id", "employee_id").prefetch_related("books")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            fields = [
                "customer_id__first_name",
                "customer_id__last_name",
                "employee_id__first_name",
                "employee_id__last_name",
                "payment_method",
                "order_status",
                "books__title",
            ]
            status_map = {label.lower(): value for value, label in Order.OrderStatus.choices}
            payment_map = {label.lower(): value for value, label in Order.PaymentMethod.choices}
            q_obj, annotations = build_advanced_search(
                q,
                fields=fields,
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
            if q_obj is not None:
                if annotations:
                    qs = qs.annotate(**annotations)
                qs = qs.filter(q_obj).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        return context


class OrderCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = "book_shop_here/order_form.html"
    success_url = reverse_lazy("book_shop_here:order-list")
    permission_required = "book_shop_here.add_order"
    raise_exception = True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method in ("POST", "PUT"):
            data = self.request.POST.copy()
            if "books" in data:
                values = data.getlist("books")
                mapped = []
                for v in values:
                    if v.isdigit():
                        mapped.append(v)
                    else:
                        try:
                            b = Book.objects.get(legacy_id=v)
                            mapped.append(str(b.pk))
                        except Book.DoesNotExist:
                            mapped.append(v)
                data.setlist("books", mapped)
            kwargs["data"] = data
        return kwargs

    def form_valid(self, form):
        try:
            obj = form.save(commit=False)
            obj._skip_recalc = True
            selected_books = form.cleaned_data["books"].values_list("pk", flat=True)
            books = Book.objects.filter(pk__in=selected_books)
            for book in books:
                book.book_status = "processing"
                book.save()
            obj.save()
            form.save_m2m()
            self.object = obj
            messages.success(self.request, "Order added successfully.")
            return redirect(self.success_url)
        except Exception as e:
            logger.error(f"Error adding order: {e}")
            messages.error(self.request, "Failed to add order.")
            return self.form_invalid(form)


class OrderUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = "book_shop_here/order_form.html"
    success_url = reverse_lazy("book_shop_here:order-list")
    permission_required = "book_shop_here.change_order"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Order"
        return context

    def form_valid(self, form):
        try:
            obj = form.save(commit=False)
            obj._skip_recalc = True
            obj.save()
            form.save_m2m()
            self.object = obj
            messages.success(self.request, "Order updated successfully.")
            return redirect(self.success_url)
        except Exception as e:
            logger.error(f"Error updating order: {e}")
            messages.error(self.request, "Failed to update order.")
            return self.form_invalid(form)


class OrderDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Order
    template_name = "book_shop_here/order_delete_confirm.html"
    success_url = reverse_lazy("book_shop_here:order-list")
    permission_required = "book_shop_here.delete_order"
    raise_exception = True


class OrderDetailView(LoginRequiredMixin, TemplateView):
    template_name = "book_shop_here/order_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order"] = (
            Order.objects.select_related("customer_id", "employee_id")
            .prefetch_related("books")
            .get(pk=self.kwargs["pk"])
        )
        return context


class OrderCloseView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "book_shop_here.change_order"
    raise_exception = True

    def post(self, request, *args, **kwargs):

        order = Order.objects.get(pk=kwargs["pk"])
        order.completed_order()
        messages.success(request, "Order closed.")
        next_url = request.POST.get("next") or reverse_lazy("book_shop_here:order-list")
        return redirect(next_url)
