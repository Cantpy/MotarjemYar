"""
Business logic layer for Invoice Details functionality.
"""
from datetime import datetime
import logging

from InvoicePage.invoice_details import (
    InvoiceData, InvoiceDetailsRequest, InvoiceDetailsResponse,
    TranslationOfficeInfo, Language, FinancialData,
    CustomerInfo, DocumentCounts
)
from InvoicePage.invoice_details import InvoiceDetailsRepository

logger = logging.getLogger(__name__)


class InvoiceDetailsLogic:
    """Business logic for invoice details operations."""

    def __init__(self, repository: InvoiceDetailsRepository):
        """Initialize with repository dependency."""
        self.repository = repository

    def initialize_invoice_data(self, request: InvoiceDetailsRequest) -> InvoiceDetailsResponse:
        """Initialize invoice data with required information."""
        try:
            # Validate user permissions
            if not self._validate_user_access(request.current_user):
                return InvoiceDetailsResponse(
                    success=False,
                    message="دسترسی کاربر معتبر نیست"
                )

            # Get next invoice number
            next_receipt_number = self.repository.get_next_invoice_number()

            # Get user information
            user_info = self.repository.get_user_info(request.current_user)
            if not user_info:
                return InvoiceDetailsResponse(
                    success=False,
                    message="اطلاعات کاربر یافت نشد"
                )

            # Get translation office information
            office_info = self.repository.get_translation_office_info()
            if not office_info:
                logger.warning("Translation office information not found")
                office_info = self._create_default_office_info()

            # Create initial invoice data
            invoice_data = InvoiceData(
                receipt_number=next_receipt_number,
                username=request.current_user,
                receive_date=datetime.now(),
                source_language=Language.FARSI,
                target_language=Language.ENGLISH,
                financial=FinancialData(),
                office_info=office_info,
                customer_info=request.customer_info,
                document_counts=DocumentCounts(total_items=request.document_count or 0)
            )

            return InvoiceDetailsResponse(
                success=True,
                message="اطلاعات فاکتور با موفقیت مقداردهی شد",
                invoice_data=invoice_data,
                next_receipt_number=next_receipt_number,
                office_info=office_info,
                user_info=user_info
            )

        except Exception as e:
            logger.error(f"Error initializing invoice data: {str(e)}")
            return InvoiceDetailsResponse(
                success=False,
                message=f"خطا در مقداردهی اطلاعات فاکتور: {str(e)}"
            )

    def validate_invoice_data(self, invoice_data: InvoiceData) -> InvoiceDetailsResponse:
        """Validate invoice data for completeness and correctness."""
        try:
            errors = []

            # Validate basic information
            if not invoice_data.receipt_number or invoice_data.receipt_number.strip() == "":
                errors.append("شماره رسید الزامی است")

            if not invoice_data.username or invoice_data.username.strip() == "":
                errors.append("نام کاربر الزامی است")

            # Validate dates
            if invoice_data.delivery_date and invoice_data.delivery_date < datetime.now().date():
                errors.append("تاریخ تحویل نمی‌تواند قبل از تاریخ جاری باشد")

            # Validate financial data
            if invoice_data.financial:
                financial_errors = self._validate_financial_data(invoice_data.financial)
                errors.extend(financial_errors)

            # Validate languages
            if invoice_data.source_language == invoice_data.target_language:
                errors.append("زبان مبدأ و مقصد نمی‌توانند یکسان باشند")

            # Validate customer information
            if invoice_data.customer_info:
                customer_errors = self._validate_customer_info(invoice_data.customer_info)
                errors.extend(customer_errors)

            # Check if receipt number already exists
            if self.repository.invoice_number_exists(invoice_data.receipt_number):
                errors.append(f"شماره رسید {invoice_data.receipt_number} قبلاً استفاده شده است")

            if errors:
                return InvoiceDetailsResponse(
                    success=False,
                    message="خطاهای اعتبارسنجی یافت شد",
                    errors=errors
                )

            return InvoiceDetailsResponse(
                success=True,
                message="اطلاعات فاکتور معتبر است"
            )

        except Exception as e:
            logger.error(f"Error validating invoice data: {str(e)}")
            return InvoiceDetailsResponse(
                success=False,
                message=f"خطا در اعتبارسنجی اطلاعات: {str(e)}"
            )

    def calculate_financial_totals(self, financial_data: FinancialData) -> FinancialData:
        """Calculate financial totals and final amount."""
        try:
            # Calculate subtotal
            subtotal = (
                    financial_data.translation_cost +
                    financial_data.confirmation_cost +
                    financial_data.office_affairs_cost +
                    financial_data.copy_certification_cost
            )

            # Add emergency cost if applicable
            if financial_data.is_emergency:
                # Emergency cost is typically 50% of translation cost
                emergency_cost = financial_data.translation_cost * 0.5
                financial_data.emergency_cost = emergency_cost
                subtotal += emergency_cost
            else:
                financial_data.emergency_cost = 0

            # Calculate final amount
            final_amount = subtotal - financial_data.discount_amount - financial_data.advance_payment
            financial_data.final_amount = max(0, final_amount)  # Ensure non-negative

            return financial_data

        except Exception as e:
            logger.error(f"Error calculating financial totals: {str(e)}")
            raise Exception(f"خطا در محاسبه مبالغ مالی: {str(e)}")

    def get_suggested_receipt_number(self, current_user: str) -> str:
        """Get suggested receipt number for new invoice."""
        try:
            return self.repository.get_next_invoice_number()
        except Exception as e:
            logger.error(f"Error getting suggested receipt number: {str(e)}")
            return "1"

    def update_office_information(self, office_info: TranslationOfficeInfo,
                                  current_user: str) -> InvoiceDetailsResponse:
        """Update translation office information."""
        try:
            # Check permissions - only admin or manager can update office info
            user_info = self.repository.get_user_info(current_user)
            if not user_info or user_info.role not in ['admin', 'manager']:
                return InvoiceDetailsResponse(
                    success=False,
                    message="دسترسی کافی برای به‌روزرسانی اطلاعات دارالترجمه ندارید"
                )

            # Validate office information
            validation_errors = self._validate_office_info(office_info)
            if validation_errors:
                return InvoiceDetailsResponse(
                    success=False,
                    message="خطاهای اعتبارسنجی یافت شد",
                    errors=validation_errors
                )

            # Update in database
            success = self.repository.update_translation_office_info(office_info)

            if success:
                return InvoiceDetailsResponse(
                    success=True,
                    message="اطلاعات دارالترجمه با موفقیت به‌روزرسانی شد",
                    office_info=office_info
                )
            else:
                return InvoiceDetailsResponse(
                    success=False,
                    message="خطا در به‌روزرسانی اطلاعات دارالترجمه"
                )

        except Exception as e:
            logger.error(f"Error updating office information: {str(e)}")
            return InvoiceDetailsResponse(
                success=False,
                message=f"خطا در به‌روزرسانی اطلاعات: {str(e)}"
            )

    def _validate_user_access(self, username: str) -> bool:
        """Validate if user has access to invoice details functionality."""
        try:
            user_info = self.repository.get_user_info(username)
            return user_info is not None and user_info.active
        except Exception as e:
            logger.error(f"Error validating user access: {str(e)}")
            return False

    def _validate_financial_data(self, financial: FinancialData) -> list:
        """Validate financial data."""
        errors = []

        # Check for negative values
        if financial.translation_cost < 0:
            errors.append("هزینه ترجمه نمی‌تواند منفی باشد")

        if financial.confirmation_cost < 0:
            errors.append("هزینه تاییدات نمی‌تواند منفی باشد")

        if financial.office_affairs_cost < 0:
            errors.append("هزینه امور دفتری نمی‌تواند منفی باشد")

        if financial.copy_certification_cost < 0:
            errors.append("هزینه کپی برابر اصل نمی‌تواند منفی باشد")

        if financial.discount_amount < 0:
            errors.append("مبلغ تخفیف نمی‌تواند منفی باشد")

        if financial.advance_payment < 0:
            errors.append("مبلغ پیش‌پرداخت نمی‌تواند منفی باشد")

        # Check if total costs are positive
        total_cost = (
                financial.translation_cost +
                financial.confirmation_cost +
                financial.office_affairs_cost +
                financial.copy_certification_cost +
                financial.emergency_cost
        )

        if total_cost <= 0:
            errors.append("مجموع هزینه‌ها باید بیشتر از صفر باشد")

        # Check if discount is not more than total cost
        if financial.discount_amount > total_cost:
            errors.append("مبلغ تخفیف نمی‌تواند بیشتر از مجموع هزینه‌ها باشد")

        # Check if advance payment is not more than payable amount
        payable_amount = total_cost - financial.discount_amount
        if financial.advance_payment > payable_amount:
            errors.append("مبلغ پیش‌پرداخت نمی‌تواند بیشتر از مبلغ قابل پرداخت باشد")

        return errors

    def _validate_customer_info(self, customer: CustomerInfo) -> list:
        """Validate customer information."""
        errors = []

        if not customer.name or customer.name.strip() == "":
            errors.append("نام مشتری الزامی است")

        if not customer.phone or customer.phone.strip() == "":
            errors.append("تلفن مشتری الزامی است")

        if not customer.national_id or customer.national_id.strip() == "":
            errors.append("کد ملی مشتری الزامی است")

        # Validate national ID format (basic validation)
        if customer.national_id and not self._is_valid_national_id(customer.national_id):
            errors.append("فرمت کد ملی نامعتبر است")

        # Validate phone number format (basic validation)
        if customer.phone and not self._is_valid_phone_number(customer.phone):
            errors.append("فرمت شماره تلفن نامعتبر است")

        return errors

    def _validate_office_info(self, office: TranslationOfficeInfo) -> list:
        """Validate translation office information."""
        errors = []

        if not office.name or office.name.strip() == "":
            errors.append("نام دارالترجمه الزامی است")

        if not office.registration_number or office.registration_number.strip() == "":
            errors.append("شماره ثبت دارالترجمه الزامی است")

        if not office.representative or office.representative.strip() == "":
            errors.append("نام نماینده دارالترجمه الزامی است")

        if not office.address or office.address.strip() == "":
            errors.append("آدرس دارالترجمه الزامی است")

        if not office.phone or office.phone.strip() == "":
            errors.append("تلفن دارالترجمه الزامی است")

        return errors

    def _is_valid_national_id(self, national_id: str) -> bool:
        """Basic national ID validation (Iranian format)."""
        # Remove any spaces or dashes
        national_id = national_id.replace(" ", "").replace("-", "")

        # Should be 10 digits
        if len(national_id) != 10 or not national_id.isdigit():
            return False

        # Basic checksum validation for Iranian national ID
        check_sum = 0
        for i in range(9):
            check_sum += int(national_id[i]) * (10 - i)

        remainder = check_sum % 11
        check_digit = int(national_id[9])

        if remainder < 2:
            return check_digit == remainder
        else:
            return check_digit == 11 - remainder

    def _is_valid_phone_number(self, phone: str) -> bool:
        """Basic phone number validation."""
        # Remove spaces, dashes, and plus signs
        phone = phone.replace(" ", "").replace("-", "").replace("+", "")

        # Should contain only digits and be at least 10 digits long
        if not phone.isdigit() or len(phone) < 10:
            return False

        # Iranian mobile numbers start with 09 or country code
        if phone.startswith("09") and len(phone) == 11:
            return True

        # International format
        if phone.startswith("989") and len(phone) == 12:
            return True

        # Landline numbers (basic check)
        if len(phone) >= 10:
            return True

        return False

    def _create_default_office_info(self) -> TranslationOfficeInfo:
        """Create default office information when none exists."""
        return TranslationOfficeInfo(
            name="نامشخص",
            registration_number="نامشخص",
            representative="نامشخص",
            manager="نامشخص",
            address="نامشخص",
            phone="نامشخص"
        )
