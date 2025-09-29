# features/Invoice_Page/invoice_preview/invoice_preview_assets.py

"""
Stores the file paths for SVG icons.
This allows for easy management and modification of icons without changing the application code.
"""

from shared import get_resource_path

# Icon Paths
PRINT_ICON_PATH = get_resource_path('resources', 'icons', 'print_invoice.svg')
PDF_ICON_PATH = get_resource_path('resources', 'icons', 'invoice_to_png.svg')
PNG_ICON_PATH = get_resource_path('resources', 'icons', 'invoice_to_pdf.svg')
SHARE_ICON_PATH = get_resource_path('resources', 'icons', 'share_invoice.svg')
