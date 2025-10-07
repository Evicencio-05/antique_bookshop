import shlex
from collections.abc import Iterable
from typing import Any

from django.db import connection
from django.db.models import F, Q, Value
from django.db.models.functions import Replace

try:
    from django.contrib.postgres.functions import Unaccent  # type: ignore
except Exception:  # pragma: no cover
    Unaccent = None


def _safe_annot_name(field: str, suffix: str) -> str:
    return f"search_{field.replace('__', '_')}_{suffix}"


def build_advanced_search(
    query: str,
    *,
    fields: Iterable[str],
    nospace_fields: Iterable[str] | None = None,
    include_unaccent: bool = True,
    mode: str = "AND",
    numeric_eq_fields: Iterable[str] | None = None,
    prefixed_fields: dict[str, list[str]] | None = None,
    choice_value_map: dict[str, dict[str, str]] | None = None,
) -> tuple[Q | None, dict[str, object]]:
    """
    Build a Q object and required annotations for advanced text search across fields.

    Features:
    - Tokenizes query with shlex (supports quoted phrases).
    - AND or OR across tokens (default AND).
    - OR across provided fields per-token.
    - Optional nospace matching (e.g., "View Tests" matches "ViewTests").
    - Optional unaccent matching on PostgreSQL using the unaccent extension.

    Returns (q_object or None, annotations dict). Apply annotations to queryset
    before filtering, e.g. queryset.annotate(**annotations).filter(q_object).
    """
    query = (query or "").strip()
    if not query:
        return None, {}

    try:
        tokens: list[str] = shlex.split(query)
    except ValueError:
        tokens = query.split()
    if not tokens:
        tokens = [query]

    nospace_fields = set(nospace_fields or [])
    numeric_eq_fields = list(numeric_eq_fields or [])
    prefixed_fields = prefixed_fields or {}
    choice_value_map = choice_value_map or {}

    use_unaccent = include_unaccent and connection.vendor == "postgresql" and Unaccent is not None

    annotations: dict[str, object] = {}

    def field_lookup(field: str, *, nospace: bool) -> str:
        """Return the lookup name (possibly annotated) for contains operations."""
        suffix_parts: list[str] = []
        expr: Any = F(field)
        if nospace:
            expr = Replace(expr, Value(" "), Value(""))
            suffix_parts.append("ns")
        if use_unaccent:
            expr = Unaccent(expr)
            suffix_parts.append("ua")
        if suffix_parts:
            annot_name = _safe_annot_name(field, "".join(suffix_parts))
            if annot_name not in annotations:
                annotations[annot_name] = expr
            return f"{annot_name}__icontains"
        else:
            # No annotation required
            return f"{field}__icontains"

    # Build Q across tokens
    combined_q: Q | None = None
    for raw_tok in tokens:
        tok = raw_tok.strip()
        if not tok:
            continue

        # Prefixed token support: prefix:value limits fields for this token
        token_fields = list(fields)
        token_choice_map = choice_value_map
        if ":" in tok:
            pref, val = tok.split(":", 1)
            pref = pref.strip().lower()
            val = val.strip()
            if pref in prefixed_fields:
                tok = val
                token_fields = prefixed_fields[pref]

        # Per-token, OR across fields
        token_q: Q | None = None
        tok_lower = tok.lower()
        for field in token_fields:
            # Choice label mapping: if label matches, include equality on value
            if field in token_choice_map:
                mapping = token_choice_map[field]
                code = mapping.get(tok_lower)
                if code is not None:
                    token_q = (
                        (token_q | Q(**{field: code}))
                        if token_q is not None
                        else Q(**{field: code})
                    )
            # Normal lookup
            lk = field_lookup(field, nospace=False)
            part = Q(**{lk: tok})
            token_q = part if token_q is None else (token_q | part)
            # Nospace variant if requested for this field
            if field in nospace_fields:
                tok_ns = tok.replace(" ", "")
                if tok_ns and tok_ns != tok:
                    lk_ns = field_lookup(field, nospace=True)
                    part_ns = Q(**{lk_ns: tok_ns})
                    token_q = token_q | part_ns
        # Numeric equality across specified fields
        if numeric_eq_fields and tok.isdigit():
            for nfield in numeric_eq_fields:
                eq_part = Q(**{nfield: int(tok)})
                token_q = eq_part if token_q is None else (token_q | eq_part)
        if token_q is None:
            continue
        if combined_q is None:
            combined_q = token_q
        else:
            combined_q = (combined_q & token_q) if mode.upper() == "AND" else (combined_q | token_q)

    return combined_q, annotations
