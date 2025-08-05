from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, date


@dataclass
class CustomerData:
    """Data class for customer information."""
    name: str = ""
    national_id: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""


@dataclass
class DocumentData:
    """Data class for document information."""
    name: str = ""
    doc_type: str = ""
    pages: int = 0
    source_language: str = ""
    target_language: str = ""
    cost: float = 0.0


@dataclass
class InvoiceDetailsData:
    """Data class for invoice details."""
    receipt_number: str = ""
    receive_date: date = field(default_factory=date.today)
    delivery_date: date = field(default_factory=lambda: date.today())
    username: str = ""
    total_amount: float = 0.0
    discount_amount: float = 0.0
    advance_payment: float = 0.0
    remarks: str = ""


@dataclass
class PreviewSettingsData:
    """Data class for preview settings."""
    paper_size: str = "A4"
    show_logo: bool = True
    custom_header: str = ""
    custom_footer: str = ""


@dataclass
class SharingOptionsData:
    """Data class for sharing options."""
    email_enabled: bool = True
    additional_emails: str = ""
    email_subject: str = "فاکتور ترجمه - دارالترجمه"
    email_message: str = ""
    whatsapp_enabled: bool = False
    telegram_enabled: bool = False
    sms_enabled: bool = False
    selected_template: str = ""


@dataclass
class WizardData:
    """Complete wizard data container."""
    customer: CustomerData = field(default_factory=CustomerData)
    documents: List[DocumentData] = field(default_factory=list)
    invoice_details: InvoiceDetailsData = field(default_factory=InvoiceDetailsData)
    preview_settings: PreviewSettingsData = field(default_factory=PreviewSettingsData)
    sharing_options: SharingOptionsData = field(default_factory=SharingOptionsData)

    def to_dict(self) -> Dict[str, Any]:
        """Convert wizard data to dictionary."""
        return {
            'customer': {
                'name': self.customer.name,
                'national_id': self.customer.national_id,
                'phone': self.customer.phone,
                'email': self.customer.email,
                'address': self.customer.address
            },
            'documents': [
                {
                    'name': doc.name,
                    'doc_type': doc.doc_type,
                    'pages': doc.pages,
                    'source_language': doc.source_language,
                    'target_language': doc.target_language,
                    'cost': doc.cost
                } for doc in self.documents
            ],
            'invoice_details': {
                'receipt_number': self.invoice_details.receipt_number,
                'receive_date': self.invoice_details.receive_date.isoformat(),
                'delivery_date': self.invoice_details.delivery_date.isoformat(),
                'username': self.invoice_details.username,
                'total_amount': self.invoice_details.total_amount,
                'discount_amount': self.invoice_details.discount_amount,
                'advance_payment': self.invoice_details.advance_payment,
                'remarks': self.invoice_details.remarks
            },
            'preview_settings': {
                'paper_size': self.preview_settings.paper_size,
                'show_logo': self.preview_settings.show_logo,
                'custom_header': self.preview_settings.custom_header,
                'custom_footer': self.preview_settings.custom_footer
            },
            'sharing_options': {
                'email_enabled': self.sharing_options.email_enabled,
                'additional_emails': self.sharing_options.additional_emails,
                'email_subject': self.sharing_options.email_subject,
                'email_message': self.sharing_options.email_message,
                'whatsapp_enabled': self.sharing_options.whatsapp_enabled,
                'telegram_enabled': self.sharing_options.telegram_enabled,
                'sms_enabled': self.sharing_options.sms_enabled,
                'selected_template': self.sharing_options.selected_template
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WizardData':
        """Create wizard data from dictionary."""
        wizard = cls()

        if 'customer' in data:
            customer_data = data['customer']
            wizard.customer = CustomerData(
                name=customer_data.get('name', ''),
                national_id=customer_data.get('national_id', ''),
                phone=customer_data.get('phone', ''),
                email=customer_data.get('email', ''),
                address=customer_data.get('address', '')
            )

        if 'documents' in data:
            wizard.documents = [
                DocumentData(
                    name=doc.get('name', ''),
                    doc_type=doc.get('doc_type', ''),
                    pages=doc.get('pages', 0),
                    source_language=doc.get('source_language', ''),
                    target_language=doc.get('target_language', ''),
                    cost=doc.get('cost', 0.0)
                ) for doc in data['documents']
            ]

        if 'invoice_details' in data:
            details_data = data['invoice_details']
            wizard.invoice_details = InvoiceDetailsData(
                receipt_number=details_data.get('receipt_number', ''),
                receive_date=date.fromisoformat(details_data.get('receive_date', date.today().isoformat())),
                delivery_date=date.fromisoformat(details_data.get('delivery_date', date.today().isoformat())),
                username=details_data.get('username', ''),
                total_amount=details_data.get('total_amount', 0.0),
                discount_amount=details_data.get('discount_amount', 0.0),
                advance_payment=details_data.get('advance_payment', 0.0),
                remarks=details_data.get('remarks', '')
            )

        if 'preview_settings' in data:
            preview_data = data['preview_settings']
            wizard.preview_settings = PreviewSettingsData(
                paper_size=preview_data.get('paper_size', 'A4'),
                show_logo=preview_data.get('show_logo', True),
                custom_header=preview_data.get('custom_header', ''),
                custom_footer=preview_data.get('custom_footer', '')
            )

        if 'sharing_options' in data:
            sharing_data = data['sharing_options']
            wizard.sharing_options = SharingOptionsData(
                email_enabled=sharing_data.get('email_enabled', True),
                additional_emails=sharing_data.get('additional_emails', ''),
                email_subject=sharing_data.get('email_subject', 'فاکتور ترجمه - دارالترجمه'),
                email_message=sharing_data.get('email_message', ''),
                whatsapp_enabled=sharing_data.get('whatsapp_enabled', False),
                telegram_enabled=sharing_data.get('telegram_enabled', False),
                sms_enabled=sharing_data.get('sms_enabled', False),
                selected_template=sharing_data.get('selected_template', '')
            )

        return wizard

    def reset(self):
        """Reset all wizard data to defaults."""
        self.customer = CustomerData()
        self.documents = []
        self.invoice_details = InvoiceDetailsData()
        self.preview_settings = PreviewSettingsData()
        self.sharing_options = SharingOptionsData()

    def calculate_total_cost(self) -> float:
        """Calculate total cost from documents."""
        return sum(doc.cost for doc in self.documents)

    def calculate_final_amount(self) -> float:
        """Calculate final amount after discount and advance payment."""
        total = self.invoice_details.total_amount
        discount = self.invoice_details.discount_amount
        advance = self.invoice_details.advance_payment
        return max(0, total - discount - advance)

    def is_step_valid(self, step_index: int) -> bool:
        """Check if a specific step has valid data."""
        if step_index == 0:  # CustomerModel info
            return bool(self.customer.name.strip())
        elif step_index == 1:  # Documents
            return len(self.documents) > 0
        elif step_index == 2:  # Invoice details
            return bool(self.invoice_details.receipt_number.strip())
        elif step_index == 3:  # Preview
            return True
        elif step_index == 4:  # Sharing
            return True
        return False


class WizardSteps:
    """Constants for wizard step indices."""
    CUSTOMER = 0
    DOCUMENTS = 1
    INVOICE_DETAILS = 2
    PREVIEW = 3
    SHARING = 4

    STEP_NAMES = [
        "1. اطلاعات مشتری",
        "2. اطلاعات اسناد",
        "3. جزئیات فاکتور",
        "4. پیش‌نمایش فاکتور",
        "5. اشتراک‌گذاری"
    ]

    TOTAL_STEPS = 5


class MessageTemplates:
    """Predefined message templates for sharing."""
    TEMPLATES = [
        "فاکتور شما آماده شد",
        "مدارک شما در حال ترجمه است",
        "لطفاً برای دریافت مراجعه کنید",
        "ترجمه اسناد شما تکمیل شد",
        "برای هماهنگی تحویل تماس بگیرید"
    ]
