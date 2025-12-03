"""
Unified import handler for multiple file formats (XLSX, CSV, XML)
"""

import csv
import json
import logging
import xml.etree.ElementTree as ET  # noqa: S314
from io import BytesIO, StringIO
from typing import Any, TypedDict, cast

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import UploadedFile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .import_utils import ImportErrorHandler, NullValueProcessor

logger = logging.getLogger(__name__)


class UnifiedImportHandler:
    """Handles imports from XLSX, CSV, and XML files"""

    SUPPORTED_FORMATS = {
        "xlsx": [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/octet-stream",
        ],
        "xls": ["application/vnd.ms-excel"],
        "csv": ["text/csv", "application/csv", "text/plain"],
        "xml": ["text/xml", "application/xml"],
    }

    def __init__(self, file_obj: UploadedFile):
        self.file_obj = file_obj
        self.file_type: str | None = self._detect_file_type()
        self.data: dict[str, Any] = {}
        self.errors: list[str] = []
        self.error_handler = ImportErrorHandler()

    def _detect_file_type(self) -> str | None:
        """Detect file type from extension or content type"""
        filename = str(self.file_obj.name).lower()

        if filename.endswith(".xlsx"):
            return "xlsx"
        elif filename.endswith(".xls"):
            return "xls"
        elif filename.endswith(".csv"):
            return "csv"
        elif filename.endswith(".xml"):
            return "xml"

        # Fallback to content type
        content_type = getattr(self.file_obj, "content_type", "").lower()
        for fmt, types in self.SUPPORTED_FORMATS.items():
            if any(t in content_type for t in types):
                return fmt

        return None

    def parse_file(self) -> dict[str, Any]:
        """Parse file based on detected type"""
        if not self.file_type:
            self.errors.append("Unsupported file format")
            return {"error": "Unsupported file format"}

        try:
            if self.file_type in ["xlsx", "xls"]:
                return self._parse_excel()
            elif self.file_type == "csv":
                return self._parse_csv()
            elif self.file_type == "xml":
                return self._parse_xml()
        except Exception as e:
            error_msg = f"Error parsing {self.file_type} file: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            return {"error": error_msg}
        # Fallback return to satisfy type checker
        return {"error": "Unknown parsing error"}

    def _parse_excel(self) -> dict[str, Any]:
        """Parse Excel file"""
        try:
            self.file_obj.seek(0)

            # Read all sheets
            xl_file = pd.ExcelFile(BytesIO(self.file_obj.read()))
            sheets_data = {}

            for sheet_name in xl_file.sheet_names:
                try:
                    df = pd.read_excel(xl_file, sheet_name=sheet_name)

                    # Handle empty sheets
                    if df.empty:
                        logger.warning(f"Sheet '{sheet_name}' is empty, skipping")
                        continue

                    # Clean column names
                    df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]

                    # Handle null values
                    df = df.fillna("")
                    df = df.replace(["nan", "NaN", "null", "NULL", "None"], "")

                    sheets_data[sheet_name] = df

                except Exception as e:
                    error_msg = f"Error parsing sheet '{sheet_name}': {str(e)}"
                    self.errors.append(error_msg)
                    logger.error(error_msg)

            # Prepare data for import
            sheets_info: list[dict[str, Any]] = []
            data_by_type: dict[str, list[dict[str, Any]]] = {}

            for sheet_name, df in sheets_data.items():
                # Sheet names from pandas can be strings or integers; normalize to string for
                # detection and logging.
                detected_type = self._detect_sheet_type(df, str(sheet_name))

                sheet_info = {
                    "name": sheet_name,
                    "type": detected_type,
                    "rows": len(df),
                    "columns": list(df.columns),
                }

                sheets_info.append(sheet_info)

                if detected_type:
                    # Columns were normalized to strings; pandas stubs use Hashable keys,
                    # so we cast here to help mypy.
                    records: list[dict[str, Any]] = cast(
                        list[dict[str, Any]], df.to_dict("records")
                    )
                    data_by_type.setdefault(detected_type, []).extend(records)

            import_data: dict[str, Any] = {
                "sheets_info": sheets_info,
                "data_by_type": data_by_type,
                "errors": self.errors.copy(),
            }
            return import_data

        except Exception as e:
            error_msg = f"Error parsing Excel file: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            return {"error": error_msg}

    def _detect_sheet_type(self, df: pd.DataFrame, sheet_name: str) -> str | None:
        """Detect what type of data is in each sheet based on column headers"""

        # Convert column names to lowercase for comparison
        columns = [col.lower() for col in df.columns]

        # Define patterns for each model type
        patterns = {
            "author": ["last_name", "first_name", "birth_year", "death_year"],
            "book": ["title", "cost", "suggested_retail_price", "condition"],
            "customer": ["first_name", "last_name", "phone_number", "mailing_address"],
            "employee": ["first_name", "last_name", "phone_number", "address", "group"],
            "order": ["customer", "employee", "sale_amount", "payment_method"],
        }

        # Score each pattern
        scores = {}
        for model_type, required_cols in patterns.items():
            score = sum(1 for col in required_cols if any(col in df_col for df_col in columns))
            if score > 0:  # At least one matching column
                scores[model_type] = score / len(required_cols)

        if not scores:
            logger.warning(f"Could not detect type for sheet '{sheet_name}'. Columns: {columns}")
            return None

        # Return the highest scoring type
        best_type = max(scores, key=lambda k: scores[k])
        confidence = scores[best_type]

        if confidence < 0.5:  # Less than 50% match
            logger.warning(
                f"Low confidence ({confidence:.2%}) for sheet '{sheet_name}' as {best_type}"
            )

        logger.info(f"Detected sheet '{sheet_name}' as {best_type} (confidence: {confidence:.2%})")
        return best_type

    def _parse_csv(self) -> dict[str, Any]:
        """Parse CSV file"""
        try:
            self.file_obj.seek(0)

            # Try to detect encoding
            content = self.file_obj.read()
            encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]

            decoded_content = None
            for encoding in encodings:
                try:
                    decoded_content = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if not decoded_content:
                raise ValueError("Could not decode CSV file with common encodings")

            # Parse CSV
            csv_file = StringIO(decoded_content)

            # Detect delimiter
            sample = decoded_content[:1024]
            sniffer = csv.Sniffer()
            try:
                sniffed = sniffer.sniff(sample)
                delimiter = sniffed.delimiter
            except Exception:
                delimiter = ","
            # Heuristic: fallback to ';' if header contains semicolons
            header_line = decoded_content.splitlines()[0] if decoded_content else ""
            if header_line.count(";") > header_line.count(","):
                delimiter = ";"

            # Read CSV with pandas for consistency (robust to embedded quotes)
            try:
                df = pd.read_csv(
                    csv_file,
                    delimiter=delimiter,
                    engine="python",
                    escapechar="\\",
                    quoting=csv.QUOTE_MINIMAL,
                    quotechar='"',
                    doublequote=True,
                )
            except Exception:
                # Fallback to Python csv module for malformed but common cases
                csv_file.seek(0)
                reader = csv.reader(
                    csv_file, delimiter=delimiter, quotechar='"', escapechar="\\", doublequote=True
                )
                rows = list(reader)
                if not rows:
                    raise ValueError("Empty CSV file") from None
                headers = [str(h).strip() for h in rows[0]]
                data_rows = [dict(zip(headers, r, strict=False)) for r in rows[1:]]
                df = pd.DataFrame(data_rows)
                df.columns = headers

            # Clean column names
            df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]

            # Handle null values
            df = df.fillna("")
            df = df.replace(["nan", "NaN", "null", "NULL", "None", "N/A"], "")

            # Detect data type based on columns
            detected_type = self._detect_csv_type(df)

            return {
                "sheets_info": [
                    {
                        "name": "CSV Data",
                        "type": detected_type,
                        "rows": len(df),
                        "columns": list(df.columns),
                    }
                ],
                "data_by_type": {detected_type: df.to_dict("records")} if detected_type else {},
                "errors": self.errors,
            }

        except Exception as e:
            error_msg = f"Error parsing CSV: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            return {"error": error_msg}

    def _detect_csv_type(self, df: pd.DataFrame) -> str | None:
        """Detect model type from CSV columns"""
        columns = [col.lower() for col in df.columns]

        # Scoring system for type detection
        type_scores = {"author": 0, "book": 0, "customer": 0, "employee": 0, "order": 0}

        # Strong signals
        if "payment_method" in columns or "sale_amount" in columns:
            type_scores["order"] += 5
        if "hire_date" in columns or "group" in columns:
            type_scores["employee"] += 4

        # General signals
        if any("author" in col or "birth" in col or "death" in col for col in columns):
            type_scores["author"] += 2
        if any("title" in col or "isbn" in col or "publisher" in col for col in columns):
            type_scores["book"] += 2
        if any("customer" in col for col in columns):
            type_scores["customer"] += 2
        # Only count 'employee' if accompanied by another employee-specific field
        if "employee" in columns and (
            "hire_date" in columns or "group" in columns or "email" in columns
        ):
            type_scores["employee"] += 2
        if any("order" in col or "payment" in col for col in columns):
            type_scores["order"] += 2

        # Additional specific checks
        if "last_name" in columns and "first_name" in columns:
            if "birth_year" in columns or "death_year" in columns:
                type_scores["author"] += 3
            elif "hire_date" in columns:
                type_scores["employee"] += 3
            elif "mailing_address" in columns:
                type_scores["customer"] += 3

        if "title" in columns and ("cost" in columns or "price" in columns):
            type_scores["book"] += 3

        # Return highest scoring type if score > 0
        max_type = max(type_scores, key=lambda k: type_scores[k])
        if type_scores[max_type] > 0:
            logger.info(f"Detected CSV as {max_type} (score: {type_scores[max_type]})")
            return max_type

        logger.warning(f"Could not reliably detect CSV type. Scores: {type_scores}")
        return None

    def _parse_xml(self) -> dict[str, Any]:
        """Parse XML file"""
        try:
            self.file_obj.seek(0)
            content = self.file_obj.read()

            # Try different encodings
            for encoding in ["utf-8", "latin-1", "iso-8859-1"]:
                try:
                    if isinstance(content, bytes):
                        content = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue

            # Parse XML
            root = ET.fromstring(content)  # noqa: S314

            # Detect structure and extract data
            data_by_type = self._extract_xml_data(root)

            # Prepare response
            result: dict[str, Any] = {"sheets_info": [], "data_by_type": {}, "errors": self.errors}

            for data_type, records in data_by_type.items():
                if records:
                    result["sheets_info"].append(
                        {
                            "name": f"XML {data_type.title()}",
                            "type": data_type,
                            "rows": len(records),
                            "columns": list(records[0].keys()) if records else [],
                        }
                    )
                    result["data_by_type"][data_type] = records

            return result

        except Exception as e:
            error_msg = f"Error parsing XML: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
            return {"error": error_msg}

    def _extract_xml_data(self, root: ET.Element) -> dict[str, list[dict]]:
        """Extract data from XML structure"""
        data_by_type = {}

        # Look for common patterns
        # Pattern 1: <books><book>...</book></books>
        for plural_tag in ["books", "authors", "customers", "employees", "orders"]:
            elements = root.findall(f".//{plural_tag}")
            if not elements:
                elements = root.findall(f"./{plural_tag}")

            for container in elements:
                singular_tag = plural_tag[:-1]  # Remove 's'
                items = container.findall(singular_tag)

                if items:
                    data_type = singular_tag
                    records = []

                    for item in items:
                        record = self._xml_element_to_dict(item)
                        if record:
                            records.append(record)

                    if records:
                        data_by_type[data_type] = records

        # Pattern 2: Direct children as records
        if not data_by_type:
            # Try to detect type from root tag
            root_tag = root.tag.lower()
            if any(t in root_tag for t in ["book", "author", "customer", "employee", "order"]):
                data_type = self._detect_xml_type(root_tag)
                records = []

                for child in root:
                    record = self._xml_element_to_dict(child)
                    if record:
                        records.append(record)

                if records:
                    data_by_type[data_type] = records
            else:
                # Assume direct children are records, detect type from content
                records = []
                for child in root:
                    record = self._xml_element_to_dict(child)
                    if record:
                        records.append(record)

                if records:
                    # Detect type from first record
                    detected_type = self._detect_record_type(records[0])
                    if detected_type:
                        data_by_type[detected_type] = records

        return data_by_type

    def _xml_element_to_dict(self, element: ET.Element) -> dict[str, Any]:
        """Convert XML element to dictionary"""
        result = {}

        # Add attributes
        for attr_key, attr_val in element.attrib.items():
            result[attr_key.lower().replace("-", "_")] = attr_val

        # Add child elements
        for child in element:
            key = child.tag.lower().replace("-", "_")
            value: Any = child.text or ""

            # Handle nested elements
            if len(child) > 0:
                value = self._xml_element_to_dict(child)

            # Clean the value
            if isinstance(value, str):
                value = value.strip()
                if value.lower() in ["null", "none", "nil"]:
                    value = ""

            result[key] = value

        # Add text content if no children
        if not result and element.text:
            return {"value": element.text.strip()}

        return result

    def _detect_xml_type(self, tag: str) -> str:
        """Detect model type from XML tag"""
        tag = tag.lower()

        if "book" in tag:
            return "book"
        elif "author" in tag:
            return "author"
        elif "customer" in tag:
            return "customer"
        elif "employee" in tag:
            return "employee"
        elif "order" in tag:
            return "order"

        return "unknown"

    def _detect_record_type(self, record: dict) -> str | None:
        """Detect model type from record fields"""
        fields = set(record.keys())

        # Check for distinctive fields
        if "title" in fields and ("cost" in fields or "price" in fields):
            return "book"
        elif "birth_year" in fields or "death_year" in fields:
            return "author"
        elif "hire_date" in fields or "group" in fields:
            return "employee"
        elif "mailing_address" in fields and "customer" not in str(fields):
            return "customer"
        elif "sale_amount" in fields or "payment_method" in fields:
            return "order"

        return None


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def unified_import_upload(request):
    """Handle file upload for any supported format"""

    if "file" not in request.FILES:
        return JsonResponse({"error": "No file provided"}, status=400)

    file_obj = request.FILES["file"]

    try:
        handler = UnifiedImportHandler(file_obj)

        if not handler.file_type:
            return JsonResponse(
                {"error": "Unsupported file format. Supported formats: XLSX, XLS, CSV, XML"},
                status=400,
            )

        # Parse the file
        import_data = handler.parse_file()

        if "error" in import_data:
            return JsonResponse(
                {"error": import_data["error"], "errors": handler.errors}, status=400
            )

        # Add file type info
        import_data["file_type"] = handler.file_type

        # Generate column mapping suggestions for each data type
        for sheet_info in import_data.get("sheets_info", []):
            if sheet_info["type"] and sheet_info["type"] != "unknown":
                data_type = sheet_info["type"]
                if data_type in import_data.get("data_by_type", {}):
                    records = import_data["data_by_type"][data_type]
                    if records:
                        df = pd.DataFrame(records)
                        suggestions = _get_column_mapping_suggestions(df, data_type)
                        sheet_info["suggested_mappings"] = suggestions

        return JsonResponse(
            {
                "success": True,
                "message": f"Successfully parsed {handler.file_type.upper()} file",
                "data": import_data,
            }
        )

    except Exception as e:
        logger.error(f"Error processing file upload: {str(e)}")
        return JsonResponse({"error": f"Error processing file: {str(e)}"}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def unified_import_process(request):
    """Process the import after user confirms mappings"""

    try:
        data = json.loads(request.body)
        error_handler = ImportErrorHandler()

        import_results = {
            "success": True,
            "file_type": data.get("file_type", "unknown"),
            "results": {},
            "errors": [],
        }

        # Process each data type
        for model_type, records in data.get("data_by_type", {}).items():
            if not records:
                continue

            try:
                # Apply null value processing
                processor = NullValueProcessor()
                field_configs = _get_field_configs(model_type)

                processed_records = []
                for i, record in enumerate(records):
                    # Process and validate
                    processed = processor.process_row(record, field_configs)
                    is_valid, validation_errors = processor.validate_row(processed, field_configs)

                    if not is_valid:
                        for error in validation_errors:
                            error_handler.add_error(i + 1, model_type, error)
                    else:
                        processed_records.append(processed)

                # Import processed records
                if processed_records:
                    result = _import_records_by_type(
                        model_type, processed_records, data.get("mappings", {})
                    )
                    import_results["results"][model_type] = result
                else:
                    import_results["results"][model_type] = {
                        "imported": 0,
                        "skipped": 0,
                        "errors": error_handler.errors,
                    }

            except Exception as e:
                error_msg = f"Error importing {model_type} records: {str(e)}"
                import_results["errors"].append(error_msg)
                logger.error(error_msg)

        # Add error handler summary
        summary = error_handler.get_summary()
        import_results["summary"] = summary

        # Set overall success
        import_results["success"] = not summary["has_errors"]

        return JsonResponse(import_results)

    except Exception as e:
        logger.error(f"Error in unified import: {str(e)}")
        return JsonResponse({"success": False, "error": f"Import error: {str(e)}"}, status=500)


def _get_field_configs(model_type: str) -> dict[str, dict]:
    """Get field configurations for each model type"""

    configs = {
        "author": {
            "last_name": {"type": "text", "required": True},
            "first_name": {"type": "text", "required": False, "default": ""},
            "birth_year": {"type": "integer", "required": False, "min": 1, "max": 2100},
            "death_year": {"type": "integer", "required": False, "min": 1, "max": 2100},
            "description": {"type": "text", "required": False},
        },
        "book": {
            "title": {"type": "text", "required": True},
            "cost": {"type": "decimal", "required": True, "min": 0},
            "suggested_retail_price": {"type": "decimal", "required": True, "min": 0},
            "legacy_id": {"type": "text", "required": False},
            "condition": {"type": "text", "required": False, "default": "unrated"},
            "book_status": {"type": "text", "required": False, "default": "processing"},
            "publisher": {"type": "text", "required": False},
            "edition": {"type": "text", "required": False},
        },
        "customer": {
            "first_name": {"type": "text", "required": False},
            "last_name": {"type": "text", "required": False},
            "phone_number": {"type": "text", "required": False},
            "mailing_address": {"type": "text", "required": False},
            "secondary_mailing_address": {"type": "text", "required": False, "default": "N/A"},
            "city": {"type": "text", "required": False},
            "state": {"type": "text", "required": False},
            "zip_code": {"type": "text", "required": False},
        },
        "employee": {
            "first_name": {"type": "text", "required": True},
            "last_name": {"type": "text", "required": True},
            "phone_number": {"type": "text", "required": True},
            "address": {"type": "text", "required": True},
            "city": {"type": "text", "required": True},
            "zip_code": {"type": "text", "required": True},
            "state": {"type": "text", "required": True},
            "email": {"type": "text", "required": False},
            "group_name": {"type": "text", "required": True},
        },
        "order": {
            "customer_name": {"type": "text", "required": True},
            "employee_name": {"type": "text", "required": True},
            "sale_amount": {"type": "decimal", "required": True, "min": 0},
            "discount_amount": {"type": "decimal", "required": False, "default": 0},
            "payment_method": {"type": "text", "required": True},
            "order_status": {"type": "text", "required": False, "default": "pickup"},
        },
    }

    return configs.get(model_type, {})


def _get_column_mapping_suggestions(df: pd.DataFrame, detected_type: str) -> dict[str, str]:
    """Suggest column mappings based on detected type"""

    columns = [col.lower() for col in df.columns]

    # Define mapping suggestions for each type
    mappings = {
        "author": {
            "last_name": ["last_name", "lastname", "surname", "family_name"],
            "first_name": ["first_name", "firstname", "given_name", "name"],
            "birth_year": ["birth_year", "born", "birth", "year_born"],
            "death_year": ["death_year", "died", "death", "year_died"],
            "description": ["description", "bio", "biography", "about"],
        },
        "book": {
            "title": ["title", "book_title", "name"],
            "cost": ["cost", "purchase_price", "buy_price"],
            "suggested_retail_price": ["price", "retail_price", "suggested_price", "sell_price"],
            "condition": ["condition", "state", "quality"],
            "publisher": ["publisher", "pub", "publishing_house"],
            "publication_date": ["publication_date", "pub_date", "published"],
            "author_names": ["author", "authors", "author_name", "author_names"],
            "legacy_id": ["legacy_id", "old_id", "isbn", "barcode"],
        },
        "customer": {
            "first_name": ["first_name", "firstname", "given_name"],
            "last_name": ["last_name", "lastname", "surname"],
            "phone_number": ["phone", "phone_number", "tel", "telephone"],
            "mailing_address": ["address", "mailing_address", "street", "location"],
            "secondary_mailing_address": ["secondary_address", "address_2", "apt"],
            "city": ["city", "town"],
            "state": ["state", "province", "region"],
            "zip_code": ["zip", "zip_code", "postal_code", "postcode"],
        },
        "employee": {
            "first_name": ["first_name", "firstname", "given_name"],
            "last_name": ["last_name", "lastname", "surname"],
            "email": ["email", "email_address", "mail"],
            "phone_number": ["phone", "phone_number", "tel"],
            "address": ["address", "street", "location"],
            "secondary_mailing_address": ["secondary_address", "address_2", "apt"],
            "city": ["city", "town"],
            "state": ["state", "province", "region"],
            "zip_code": ["zip", "zip_code", "postal_code", "postcode"],
            "group_name": ["group", "role", "position", "department"],
        },
        "order": {
            "customer_name": ["customer", "customer_name", "buyer"],
            "employee_name": ["employee", "employee_name", "seller"],
            "sale_amount": ["amount", "total", "sale_amount", "price"],
            "payment_method": ["payment", "payment_method", "pay_method"],
            "order_status": ["status", "order_status", "state"],
            "book_titles": ["books", "book_titles", "items"],
        },
    }

    if detected_type not in mappings:
        return {}

    suggestions = {}
    type_mappings = mappings[detected_type]

    for model_field, possible_columns in type_mappings.items():
        for col in columns:
            if any(possible in col for possible in possible_columns):
                suggestions[model_field] = col
                break

    return suggestions


class ImportResults(TypedDict):
    imported: int
    skipped: int
    errors: list[str]


def _import_records_by_type(
    model_type: str, records: list[dict[str, Any]], mappings: dict[str, Any]
) -> ImportResults:
    """Import records for a specific model type"""

    from .serializers import (
        AuthorImportSerializer,
        BookImportSerializer,
        CustomerImportSerializer,
        EmployeeImportSerializer,
        OrderImportSerializer,
    )

    serializer_map = {
        "author": AuthorImportSerializer,
        "book": BookImportSerializer,
        "customer": CustomerImportSerializer,
        "employee": EmployeeImportSerializer,
        "order": OrderImportSerializer,
    }

    if model_type not in serializer_map:
        raise ValueError(f"Unknown model type: {model_type}")

    serializer_class = serializer_map[model_type]
    type_mappings = mappings.get(model_type, {})

    results: ImportResults = {"imported": 0, "skipped": 0, "errors": []}

    for record in records:
        try:
            # Apply column mappings
            mapped_data: dict[str, Any] = {}
            for model_field, source_column in type_mappings.items():
                if source_column in record:
                    mapped_data[model_field] = record[source_column]

            # Skip empty records
            if not any(str(v).strip() for v in mapped_data.values()):
                results["skipped"] += 1
                continue

            # Create and validate
            serializer = serializer_class(data=mapped_data)
            if serializer.is_valid():
                serializer.save()
                results["imported"] += 1
            else:
                error_msg = f"Validation error: {serializer.errors}"
                results["errors"].append(error_msg)
                logger.warning(f"Validation failed for {model_type}: {error_msg}")

        except Exception as e:
            error_msg = f"Import error for {model_type} record: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)

    return results
