# file_exporter.py
import pandas as pd
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path
import io


class FileExporter:
    def __init__(self):
        # Register a Persian-supporting font.
        # Make sure 'Vazir.ttf' is in the same directory or provide the full path.
        font_path = Path("Vazir.ttf")
        if font_path.exists():
            pdfmetrics.registerFont(TTFont('Vazir', font_path))
            self.persian_font = 'Vazir'
        else:
            # Fallback font
            print("Warning: Vazir.ttf not found. Using IranSANS font.")
            self.persian_font = 'IranSANS'

    def to_excel(self, df: pd.DataFrame, save_path: str):
        if not save_path.endswith('.xlsx'):
            save_path += '.xlsx'
        df.to_excel(save_path, index=False, engine='openpyxl')

    def to_pdf(self, title: str, df: pd.DataFrame, report_info: str, chart_image_path: Path, save_path: str):
        if not save_path.endswith('.pdf'):
            save_path += '.pdf'

        doc = SimpleDocTemplate(save_path, pagesize=landscape(letter))
        styles = getSampleStyleSheet()

        # Custom RTL style
        rtl_style = ParagraphStyle(
            'rtl_style',
            parent=styles['Normal'],
            fontName=self.persian_font,
            alignment=2,  # 2 is for right alignment
            fontSize=12,
            leading=14
        )
        title_style = ParagraphStyle(
            'rtl_title', parent=rtl_style, fontSize=18, alignment=1
        )

        story = []

        # Helper to reverse strings for RTL display in ReportLab
        def rtl(text):
            return str(text)[::-1]

        # Title
        story.append(Paragraph(rtl(title), title_style))
        story.append(Spacer(1, 12))

        # Report Info
        story.append(Paragraph(rtl(report_info), rtl_style))
        story.append(Spacer(1, 24))

        # Chart
        if chart_image_path and chart_image_path.exists():
            img = Image(chart_image_path, width=400, height=200)
            img.hAlign = 'CENTER'
            story.append(img)
            story.append(Spacer(1, 24))

        # Table
        # Reverse column headers and data for RTL
        df_display = df.rename(columns={col: rtl(str(col)) for col in df.columns})
        data = [df_display.columns.values.tolist()] + df_display.applymap(lambda x: rtl(str(x))).values.tolist()

        table = Table(data, hAlign='CENTER')
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        table.setStyle(style)

        story.append(table)
        doc.build(story)
