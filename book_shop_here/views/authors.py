import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from ..forms import AuthorForm
from ..models import Author
from ..utils.search import build_advanced_search

logger = logging.getLogger(__name__)


class AuthorListView(LoginRequiredMixin, ListView):
    model = Author
    template_name = "book_shop_here/author_list.html"
    context_object_name = "authors"

    def get_queryset(self):
        qs = Author.objects.all()
        q = (self.request.GET.get("q") or "").strip()
        if q:
            fields = ["first_name", "last_name", "description"]
            q_obj, annotations = build_advanced_search(
                q,
                fields=fields,
                nospace_fields=[],
                include_unaccent=True,
                mode="AND",
                prefixed_fields={
                    "first": ["first_name"],
                    "last": ["last_name"],
                    "desc": ["description"],
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


class AuthorCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Author
    form_class = AuthorForm
    template_name = "book_shop_here/author_form.html"
    success_url = reverse_lazy("book_shop_here:author-list")
    permission_required = "book_shop_here.add_author"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Author"
        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Author added successfully.")
            return response
        except Exception as e:
            logger.error(f"Error adding author: {e}")
            messages.error(self.request, "Failed to add author.")
            return self.form_invalid(form)


class AuthorUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Author
    form_class = AuthorForm
    template_name = "book_shop_here/author_form.html"
    success_url = reverse_lazy("book_shop_here:author-list")
    permission_required = "book_shop_here.change_author"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Author"
        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Author updated successfully.")
            return response
        except Exception as e:
            logger.error(f"Error updating author: {e}")
            messages.error(self.request, "Failed to update author.")
            return self.form_invalid(form)


class AuthorDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Author
    template_name = "book_shop_here/author_delete_confirm.html"
    success_url = reverse_lazy("book_shop_here:author-list")
    permission_required = "book_shop_here.delete_author"
    raise_exception = True


class AuthorDetailView(LoginRequiredMixin, TemplateView):
    template_name = "book_shop_here/author_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["author"] = get_object_or_404(Author, pk=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        try:
            messages.success(self.request, "Author removed.")
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error deleting author: {e}")
            messages.error(self.request, "Failed to delete author.")
            return self.form_invalid(form)
