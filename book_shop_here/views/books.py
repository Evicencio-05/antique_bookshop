import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from ..forms import BookForm
from ..models import Book
from ..utils.search import build_advanced_search

logger = logging.getLogger(__name__)


class BookListView(LoginRequiredMixin, ListView):
    model = Book
    template_name = "book_shop_here/book_list.html"
    context_object_name = "books"

    def get_queryset(self):
        qs = Book.objects.filter(book_status="available").prefetch_related("authors")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            fields = [
                "title",
                "legacy_id",
                "authors__first_name",
                "authors__last_name",
                "publisher",
                "rating",
            ]
            rating_map = {label.lower(): value for value, label in Book.Rating.choices}
            q_obj, annotations = build_advanced_search(
                q,
                fields=fields,
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
            if q_obj is not None:
                if annotations:
                    qs = qs.annotate(**annotations)
                qs = qs.filter(q_obj).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        return context


class BookCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = "book_shop_here/book_form.html"
    success_url = reverse_lazy("book_shop_here:book-list")
    permission_required = "book_shop_here.add_book"
    raise_exception = True

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Book added.")
            return response
        except Exception as e:
            logger.error(f"Error adding book: {e}")
            messages.error(self.request, "Failed to add book.")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Book"
        return context


class BookUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = "book_shop_here/book_form.html"
    success_url = reverse_lazy("book_shop_here:book-list")
    permission_required = "book_shop_here.change_book"
    raise_exception = True

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Book updated.")
            return response
        except Exception as e:
            logger.error(f"Error updating book: {e}")
            messages.error(self.request, "Failed to update book.")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Book"
        return context


class BookDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Book
    template_name = "book_shop_here/book_delete_confirm.html"
    success_url = reverse_lazy("book_shop_here:book-list")
    permission_required = "book_shop_here.delete_book"
    raise_exception = True


class BookDetailView(LoginRequiredMixin, TemplateView):
    template_name = "book_shop_here/book_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["book"] = get_object_or_404(Book, book_id=self.kwargs["pk"])
        return context

    def get_object(self, queryset=None):
        return get_object_or_404(Book, book_id=self.kwargs["pk"])
