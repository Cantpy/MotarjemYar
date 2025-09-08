# features/Invoice_Page/invoice_preview/invoice_preview_assets.py

"""
Stores the file paths for SVG icons.
This allows for easy management and modification of icons without changing the application code.
"""

from shared import return_resource

# Icon Paths
PRINT_ICON_PATH = return_resource('resources', 'print_invoice.svg', 'icons')
PDF_ICON_PATH = return_resource('resources', 'invoice_to_png.svg', 'icons')
PNG_ICON_PATH = return_resource('resources', 'invoice_to_pdf.svg', 'icons')
SHARE_ICON_PATH = return_resource('resources', 'share_invoice.svg', 'icons')
