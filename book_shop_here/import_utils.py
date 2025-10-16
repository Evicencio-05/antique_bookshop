"""
Simple error handling utilities for data import operations
"""

import logging
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction

logger = logging.getLogger(__name__)


class ImportErrorHandler:
    """Simple error handler for import operations"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.failed_count = 0

    def add_error(self, row_num: int, field: str, message: str):
        """Add an error message"""
        error = {"row": row_num, "field": field, "message": message, "type": "error"}
        self.errors.append(error)
        self.failed_count += 1
        logger.error(f"Row {row_num}, Field {field}: {message}")

    def add_warning(self, row_num: int, field: str, message: str):
        """Add a warning message"""
        warning = {"row": row_num, "field": field, "message": message, "type": "warning"}
        self.warnings.append(warning)
        logger.warning(f"Row {row_num}, Field {field}: {message}")

    def record_success(self):
        """Increment success counter"""
        self.success_count += 1

    def get_summary(self) -> dict[str, Any]:
        """Get import summary"""
        return {
            "total_processed": self.success_count + self.failed_count,
            "successful": self.success_count,
            "failed": self.failed_count,
            "errors": self.errors,
            "warnings": self.warnings,
            "has_errors": len(self.errors) > 0,
        }

    def clear(self):
        """Clear all errors and counters"""
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.failed_count = 0


def clean_value(value: Any, field_type: str = "text") -> Any:
    """Clean and normalize input values"""

    # Handle None
    if value is None:
        return None

    # Convert to string and strip
    if isinstance(value, str):
        value = value.strip()

        # Check for null-like strings
        if value.lower() in ["null", "none", "nan", "n/a", "#n/a"]:
            return None

        # Empty string handling
        if value == "":
            if field_type in ["number", "decimal", "integer"]:
                return None
            return ""

    # Type-specific cleaning
    if field_type == "integer":
        try:
            return int(value) if value != "" else None
        except (ValueError, TypeError):
            return None

    elif field_type == "decimal":
        try:
            from decimal import Decimal

            return Decimal(str(value)) if value != "" else None
        except Exception:
            return None
            return None

    elif field_type == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ["true", "yes", "1", "t", "y"]
        return bool(value)

    return value


def validate_required_fields(data: dict, required_fields: list[str]) -> tuple[bool, list[str]]:
    """Validate that required fields are present and not empty"""

    missing_fields = []

    for field in required_fields:
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing_fields.append(field)

    is_valid = len(missing_fields) == 0
    return is_valid, missing_fields


def safe_import(import_function, data: dict, error_handler: ImportErrorHandler, row_num: int = 0):
    """Safely execute an import operation with error handling"""

    try:
        with transaction.atomic():
            result = import_function(data)
            error_handler.record_success()
            return result
    except ValidationError as e:
        error_handler.add_error(row_num, "validation", str(e))
        return None
    except Exception as e:
        error_handler.add_error(row_num, "import", f"Unexpected error: {str(e)}")
        logger.exception(f"Import error at row {row_num}")
        return None


def format_import_errors(errors: list[dict]) -> str:
    """Format errors for display"""

    if not errors:
        return "No errors"

    # Group errors by row
    errors_by_row: dict[str, list[str]] = {}
    for error in errors:
        row = error.get("row", "Unknown")
        if row not in errors_by_row:
            errors_by_row[row] = []
        errors_by_row[row].append(f"{error['field']}: {error['message']}")

    # Format output
    lines = []
    for row, row_errors in sorted(errors_by_row.items()):
        lines.append(f"Row {row}:")
        for msg in row_errors:
            lines.append(f"  - {msg}")

    return "\n".join(lines)


class NullValueProcessor:
    """Process and handle null values in imports"""

    @staticmethod
    def process_row(row_data: dict, field_configs: dict) -> dict:
        """Process a row of data according to field configurations

        field_configs example:
        {
            'first_name': {'type': 'text', 'required': True, 'default': None},
            'birth_year': {'type': 'integer', 'required': False, 'default': None}
        }
        """

        processed = {}

        for field, config in field_configs.items():
            value = row_data.get(field)

            # Clean the value
            cleaned = clean_value(value, config.get("type", "text"))

            # Apply default if None and default is set
            if cleaned is None and "default" in config:
                cleaned = config["default"]

            # Skip None values for non-required fields unless explicitly included
            if (
                cleaned is not None
                or config.get("required", False)
                or config.get("include_none", False)
            ):
                processed[field] = cleaned

        return processed

    @staticmethod
    def validate_row(row_data: dict, field_configs: dict) -> tuple[bool, list[str]]:
        """Validate a row against field configurations"""

        errors = []

        for field, config in field_configs.items():
            value = row_data.get(field)
            cleaned = clean_value(value, config.get("type", "text"))

            # Check required fields
            if config.get("required", False) and (
                cleaned is None or (isinstance(cleaned, str) and not cleaned)
            ):
                errors.append(f"{field} is required")

            # Check min/max for numbers
            if cleaned is not None and config.get("type") in ["integer", "decimal"]:
                if "min" in config and cleaned < config["min"]:
                    errors.append(f"{field} must be at least {config['min']}")
                if "max" in config and cleaned > config["max"]:
                    errors.append(f"{field} must be at most {config['max']}")

        return len(errors) == 0, errors
