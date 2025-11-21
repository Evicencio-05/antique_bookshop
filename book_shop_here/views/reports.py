import logging
from datetime import datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from ..models import Author, Book, Customer, Employee, Order

logger = logging.getLogger(__name__)


class EmployeeSalesView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "book_shop_here/employee_sales.html"
    permission_required = "book_shop_here.view_employee_sales"
    raise_exception = True

    def _parse_date(self, value):
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = get_object_or_404(Employee.objects.select_related("group"), pk=self.kwargs["pk"])
        start_date = self._parse_date(self.request.GET.get("start"))
        end_date = self._parse_date(self.request.GET.get("end"))

        completed_statuses = [Order.OrderStatus.SHIPPED, Order.OrderStatus.PICKED_UP]
        orders_qs = Order.objects.filter(employee_id=employee, order_status__in=completed_statuses)
        if start_date:
            orders_qs = orders_qs.filter(order_date__gte=start_date)
        if end_date:
            orders_qs = orders_qs.filter(order_date__lte=end_date)

        total_orders = orders_qs.count()
        total_revenue = orders_qs.aggregate(v=Sum("sale_amount"))["v"] or 0
        total_books_sold = orders_qs.aggregate(v=Count("books"))["v"] or 0

        sold_books = Book.objects.filter(orders__in=orders_qs).distinct().order_by("-pk")

        frequent_customers = (
            Customer.objects.filter(order__in=orders_qs)
            .annotate(purchase_count=Count("order", filter=Q(order__in=orders_qs)))
            .order_by("-purchase_count", "last_name", "first_name")[:10]
        )

        context.update(
            {
                "employee": employee,
                "start": start_date.isoformat() if start_date else "",
                "end": end_date.isoformat() if end_date else "",
                "totals": {
                    "revenue": total_revenue,
                    "orders": total_orders,
                    "books": total_books_sold,
                },
                "sold_books": sold_books[:25],
                "frequent_customers": frequent_customers,
            }
        )
        return context


class SalesDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "book_shop_here/sales_dashboard.html"
    permission_required = "book_shop_here.view_sales_reports"
    raise_exception = True

    def _parse_date(self, value):
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start_date = self._parse_date(self.request.GET.get("start"))
        end_date = self._parse_date(self.request.GET.get("end"))

        if not start_date and not end_date:
            end_date = datetime.today().date()
            start_date = end_date - timedelta(days=30)

        completed_statuses = [Order.OrderStatus.SHIPPED, Order.OrderStatus.PICKED_UP]
        completed = Order.objects.filter(order_status__in=completed_statuses)
        open_orders = Order.objects.exclude(order_status__in=completed_statuses)
        if start_date:
            completed = completed.filter(order_date__gte=start_date)
            open_orders = open_orders.filter(order_date__gte=start_date)
        if end_date:
            completed = completed.filter(order_date__lte=end_date)
            open_orders = open_orders.filter(order_date__lte=end_date)

        summary_orders = completed.count()
        summary_revenue = completed.aggregate(v=Sum("sale_amount"))["v"] or 0
        summary_books = completed.aggregate(v=Count("books"))["v"] or 0
        summary_discount = completed.aggregate(v=Sum("discount_amount"))["v"] or 0
        summary_avg_order_value = completed.aggregate(v=Avg("sale_amount"))["v"] or 0
        logger.debug(summary_avg_order_value)

        inventory_by_status = list(
            Book.objects.values("book_status")
            .annotate(count=Count("book_id"))
            .order_by("book_status")
        )

        open_by_status = list(
            open_orders.values("order_status")
            .annotate(count=Count("order_id"))
            .order_by("order_status")
        )

        payment_breakdown = list(
            completed.values("payment_method")
            .annotate(count=Count("order_id"), revenue=Sum("sale_amount"))
            .order_by("payment_method")
        )

        top_employees = list(
            completed.values("employee_id", "employee_id__first_name", "employee_id__last_name")
            .annotate(books_sold=Count("books"), revenue=Sum("sale_amount"))
            .order_by("-books_sold", "-revenue")[:10]
        )

        top_customers = list(
            completed.values("customer_id", "customer_id__first_name", "customer_id__last_name")
            .annotate(purchase_count=Count("order_id"), revenue=Sum("sale_amount"))
            .order_by("-purchase_count", "-revenue")[:10]
        )

        top_authors = list(
            Author.objects.filter(books__orders__in=completed)
            .values("author_id", "first_name", "last_name")
            .annotate(books_sold=Count("books__orders"))
            .order_by("-books_sold", "last_name")[:10]
        )

        context.update(
            {
                "start": start_date.isoformat() if start_date else "",
                "end": end_date.isoformat() if end_date else "",
                "summary": {
                    "revenue": summary_revenue,
                    "orders": summary_orders,
                    "books_sold": summary_books,
                    "total_discount": summary_discount,
                    "avg_order_value": summary_avg_order_value if summary_orders > 0 else 0,
                },
                "inventory_by_status": inventory_by_status,
                "open_by_status": open_by_status,
                "payment_breakdown": payment_breakdown,
                "top_employees": top_employees,
                "top_customers": top_customers,
                "top_authors": top_authors,
            }
        )
        return context
