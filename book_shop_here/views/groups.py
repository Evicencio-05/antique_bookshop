import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import Group, Permission
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from ..forms import GroupForm
from ..utils.search import build_advanced_search

logger = logging.getLogger(__name__)


class GroupListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = "book_shop_here/group_list.html"
    context_object_name = "groups"

    def get_queryset(self):
        qs = (
            Group.objects.all()
            .select_related("profile")
            .prefetch_related("permissions")
            .order_by("name")
        )
        q = self.request.GET.get("q", "").strip()
        if q:
            fields = ["name", "profile__description", "permissions__codename", "permissions__name"]
            q_obj, annotations = build_advanced_search(
                q,
                fields=fields,
                nospace_fields=["name"],
                include_unaccent=True,
                mode="AND",
                prefixed_fields={
                    "name": ["name"],
                    "desc": ["profile__description"],
                    "perm": ["permissions__codename", "permissions__name"],
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
        display = []
        for g in context["groups"]:
            name = g.name
            base = name.split(" (")[0]
            desc = getattr(getattr(g, "profile", None), "description", "") or "-"
            g.perm_codenames = list(g.permissions.values_list("codename", flat=True))
            display.append({"name": name, "base_name": base, "description": desc, "id": g.id})
        context["groups_display"] = display

        context["permission_actions"] = [
            ("view", "View"),
            ("add", "Add"),
            ("change", "Update"),
            ("delete", "Delete"),
        ]
        context["permission_models"] = ["book", "author", "customer", "order", "employee"]
        context["permission_models_auth"] = [("user", "user"), ("group", "role")]
        return context


class GroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = "book_shop_here/group_form.html"
    success_url = reverse_lazy("book_shop_here:group-list")
    permission_required = "auth.add_group"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Role"

        # Main permission matrix
        permission_actions = [
            ("view", "View"),
            ("add", "Add"),
            ("change", "Update"),
            ("delete", "Delete"),
        ]
        domain_models = ["book", "author", "customer", "order", "employee"]
        auth_models = [("user", "user"), ("group", "role")]
        permission_models_all = [(m, m) for m in domain_models] + auth_models
        context["permission_domain_count"] = len(domain_models)
        perms = Permission.objects.filter(
            content_type__app_label__in=["book_shop_here", "auth"]
        ).values("id", "codename")
        perm_by_code = {p["codename"]: p["id"] for p in perms}

        rows = []
        for action_code, action_label in permission_actions:
            cells = []
            for code, label in permission_models_all:
                codename = f"{action_code}_{code}"
                cells.append(
                    {
                        "model_code": code,
                        "model_label": label,
                        "codename": codename,
                        "perm_id": perm_by_code.get(codename),
                    }
                )
            rows.append({"action_code": action_code, "action_label": action_label, "cells": cells})
        context["permission_rows"] = rows
        context["permission_models_all"] = permission_models_all

        # Additional permissions (the new reports permissions and others not in matrix)
        matrix_codenames = set()
        for row in rows:
            for cell in row["cells"]:
                if cell["perm_id"]:
                    matrix_codenames.add(cell["codename"])

        extra_perms = Permission.objects.filter(
            content_type__app_label__in=["book_shop_here", "auth"]
        ).exclude(codename__in=matrix_codenames)
        context["extra_permissions"] = extra_perms

        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Group added successfully.")
            return response
        except Exception as e:
            logger.error(f"Error adding group: {e}")
            messages.error(self.request, "Failed to add group.")
            return self.form_invalid(form)


class GroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = "book_shop_here/group_form.html"
    success_url = reverse_lazy("book_shop_here:group-list")
    permission_required = "auth.change_group"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Role"

        # Main permission matrix
        permission_actions = [
            ("view", "View"),
            ("add", "Add"),
            ("change", "Update"),
            ("delete", "Delete"),
        ]
        domain_models = ["book", "author", "customer", "order", "employee"]
        auth_models = [("user", "user"), ("group", "role")]
        permission_models_all = [(m, m) for m in domain_models] + auth_models
        context["permission_domain_count"] = len(domain_models)
        perms = Permission.objects.filter(
            content_type__app_label__in=["book_shop_here", "auth"]
        ).values("id", "codename")
        perm_by_code = {p["codename"]: p["id"] for p in perms}

        rows = []
        for action_code, action_label in permission_actions:
            cells = []
            for code, label in permission_models_all:
                codename = f"{action_code}_{code}"
                cells.append(
                    {
                        "model_code": code,
                        "model_label": label,
                        "codename": codename,
                        "perm_id": perm_by_code.get(codename),
                    }
                )
            rows.append({"action_code": action_code, "action_label": action_label, "cells": cells})
        context["permission_rows"] = rows
        context["permission_models_all"] = permission_models_all

        # Additional permissions
        matrix_codenames = set()
        for row in rows:
            for cell in row["cells"]:
                if cell["perm_id"]:
                    matrix_codenames.add(cell["codename"])

        extra_perms = Permission.objects.filter(
            content_type__app_label__in=["book_shop_here", "auth"]
        ).exclude(codename__in=matrix_codenames)
        context["extra_permissions"] = extra_perms

        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Group updated successfully.")
            return response
        except Exception as e:
            logger.error(f"Error updating group: {e}")
            messages.error(self.request, "Failed to update group.")
            return self.form_invalid(form)


class GroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Group
    template_name = "book_shop_here/group_delete_confirm.html"
    success_url = reverse_lazy("book_shop_here:group-list")
    permission_required = "auth.delete_group"
    raise_exception = True


class GroupDetailView(LoginRequiredMixin, TemplateView):
    template_name = "book_shop_here/group_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group"] = get_object_or_404(
            Group.objects.select_related("profile").prefetch_related("permissions"),
            pk=self.kwargs["pk"],
        )
        return context

    def form_valid(self, form):
        try:
            messages.success(self.request, "Group removed.")
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error deleting group: {e}")
            messages.error(self.request, "Failed to delete group.")
            return self.form_invalid(form)
