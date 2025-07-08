import importlib

__all__ = [
    "InvoiceBackend", "ValidationService", "InvoicePage", "DatabaseManager", "Customer", "Service", "InvoiceItem",
    "IssuedInvoice", "OtherService", "FixedPrice", "get_customer_by_national_id", "get_service_by_name",
    "get_fixed_price_by_name", "get_other_service_by_name", "InvoicePageUI",
]


def __getattr__(name: str):
    if name in {"InvoiceBackend", "ValidationService"}:
        module = importlib.import_module("features.InvoicePage.backend.invoice_page_backend")
    elif name in {"InvoicePage"}:
        module = importlib.import_module("features.InvoicePage.controller.invoice_page_controller")
    elif name in {
        "DatabaseManager", "Customer", "Service", "InvoiceItem",
        "IssuedInvoice", "OtherService", "FixedPrice",
        "get_customer_by_national_id", "get_service_by_name",
        "get_fixed_price_by_name", "get_other_service_by_name"
    }:
        module = importlib.import_module("features.InvoicePage.models.invoice_page_models")
    elif name in {"InvoicePageUI"}:
        module = importlib.import_module("features.InvoicePage.ui.invoice_page_ui")
    else:
        raise AttributeError(f"module 'features.InvoicePage' has no attribute '{name}'")

    return getattr(module, name)
