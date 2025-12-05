# features/Invoice_Table/invoice_table_repo.py

"""
Repository for invoice-related database operations.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session
# We remove the broad try/except blocks so errors propagate to the UI controller
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict

# Import the Data Classes and Models correctly
from features.Invoice_Table.invoice_table_models import InvoiceSummary
from shared.orm_models.business_models import (
    IssuedInvoiceModel, InvoiceItemModel, DeletedInvoiceModel,
    InvoiceItemData, InvoiceData, EditedInvoiceModel, EditedInvoiceData,
    DeletedInvoiceData, UsersModel, ServicesModel, ServiceDynamicPrice
)
from shared.orm_models.payroll_models import EmployeeModel, EmployeeRoleModel


class BusinessRepository:
    """
    Stateless and pure database access layer for business-related operations.
    Allows exceptions to bubble up to be handled by the Controller/UI.
    """

    # ────────────────────────────────────────────────────────────── #
    #                           INVOICES                             #
    # ────────────────────────────────────────────────────────────── #

    def get_all_invoices(self, session: Session) -> List[InvoiceData]:
        """
        Fetches all invoices.
        Note: Removed try/except so connection/schema errors appear in the UI.
        """
        invoices = session.query(IssuedInvoiceModel).all()
        # Convert ORM objects to Dataclasses
        return [invoice.to_dataclass() for invoice in invoices]

    def get_invoice_by_number(self, session: Session, invoice_number: str) -> Optional[InvoiceData]:
        invoice = (
            session.query(IssuedInvoiceModel)
            .filter(IssuedInvoiceModel.invoice_number == invoice_number)
            .one_or_none()
        )
        return invoice.to_dataclass() if invoice else None

    def get_invoice_and_items(
            self, session: Session, invoice_number: str
    ) -> Tuple[Optional[InvoiceData], List[InvoiceItemData]]:

        invoice_orm = (
            session.query(IssuedInvoiceModel)
            .filter_by(invoice_number=invoice_number)
            .one_or_none()
        )

        if not invoice_orm:
            return None, []

        items_orm = (
            session.query(InvoiceItemModel)
            .filter_by(invoice_number=invoice_number)
            .all()
        )

        return (
            invoice_orm.to_dataclass(),
            [item.to_dataclass() for item in items_orm],
        )

    def get_services_and_dynamic_prices(
            self, session: Session, service_ids: set[int], dynamic_price_ids: set[int]
    ) -> Tuple[Dict[int, str], Dict[int, str]]:

        service_map = {}
        dynamic_price_map = {}

        if service_ids:
            services = (
                session.query(ServicesModel)
                .filter(ServicesModel.id.in_(service_ids))
                .all()
            )
            service_map = {s.id: s.name for s in services}

        if dynamic_price_ids:
            dynamic_prices = (
                session.query(ServiceDynamicPrice)
                .filter(ServiceDynamicPrice.id.in_(dynamic_price_ids))
                .all()
            )
            dynamic_price_map = {dp.id: dp.name for dp in dynamic_prices}

        return service_map, dynamic_price_map

    def update_invoice(self, session: Session, invoice_number: str, updates: Dict[str, object]) -> bool:
        invoice = (
            session.query(IssuedInvoiceModel)
            .filter(IssuedInvoiceModel.invoice_number == invoice_number)
            .one_or_none()
        )

        if not invoice:
            return False

        for key, value in updates.items():
            if hasattr(invoice, key):
                setattr(invoice, key, value)

        session.commit()
        return True

    def update_pdf_path(self, session: Session, invoice_number: str, new_path: str) -> bool:
        return self.update_invoice(session, invoice_number, {"pdf_file_path": new_path})

    def update_translator(self, session: Session, invoice_number: str, translator_name: str) -> bool:
        return self.update_invoice(session, invoice_number, {"translator": translator_name})

    def delete_invoice(self, session: Session, invoice_number: str, deleted_by_user: str) -> bool:
        # Keep try/except here because this is a Transactional write operation
        # and we want to return False on failure rather than crashing,
        # allowing the controller to count failures.
        try:
            invoice_to_delete = session.query(IssuedInvoiceModel).filter(
                IssuedInvoiceModel.invoice_number == invoice_number
            ).first()

            if not invoice_to_delete:
                return False

            # Create archive record
            deleted_invoice = DeletedInvoiceModel(
                invoice_number=invoice_to_delete.invoice_number,
                name=invoice_to_delete.name,
                national_id=invoice_to_delete.national_id,
                phone=invoice_to_delete.phone,
                issue_date=invoice_to_delete.issue_date,
                delivery_date=invoice_to_delete.delivery_date,
                translator=invoice_to_delete.translator,
                total_items=invoice_to_delete.total_items,
                total_amount=invoice_to_delete.total_amount,
                total_translation_price=invoice_to_delete.total_translation_price,
                total_certified_copy_price=invoice_to_delete.total_certified_copy_price,
                total_registration_price=invoice_to_delete.total_registration_price,
                total_confirmation_price=invoice_to_delete.total_confirmation_price,
                total_additional_issues_price=invoice_to_delete.total_additional_issues_price,
                advance_payment=invoice_to_delete.advance_payment,
                discount_amount=invoice_to_delete.discount_amount,
                emergency_cost=invoice_to_delete.emergency_cost,
                final_amount=invoice_to_delete.final_amount,
                payment_status=invoice_to_delete.payment_status,
                delivery_status=invoice_to_delete.delivery_status,
                source_language=invoice_to_delete.source_language,
                target_language=invoice_to_delete.target_language,
                username=invoice_to_delete.username,
                pdf_file_path=invoice_to_delete.pdf_file_path,
                remarks=invoice_to_delete.remarks,
                deleted_at=datetime.now(timezone.utc),
                deleted_by=deleted_by_user
            )
            session.add(deleted_invoice)
            session.delete(invoice_to_delete)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error deleting invoice {invoice_number}: {e}")
            return False

    def get_document_count(self, session: Session, invoice_number: str) -> int:
        count = (
            session.query(func.sum(InvoiceItemModel.quantity))
            .filter(InvoiceItemModel.invoice_number == invoice_number)
            .scalar()
        )
        return count or 0

    def get_all_document_counts(self, session: Session) -> Dict[str, int]:
        results = (
            session.query(
                InvoiceItemModel.invoice_number,
                func.sum(InvoiceItemModel.quantity),
            )
            .group_by(InvoiceItemModel.invoice_number)
            .all()
        )
        return {inv_num: count for inv_num, count in results}

    def get_invoice_summary(self, session: Session) -> Optional[InvoiceSummary]:
        total_count = session.query(func.count(IssuedInvoiceModel.id)).scalar() or 0
        total_amount = session.query(func.sum(IssuedInvoiceModel.total_amount)).scalar() or 0

        translator_stats = [
            (translator, count)
            for translator, count in session.query(
                IssuedInvoiceModel.translator, func.count(IssuedInvoiceModel.id)
            )
            .filter(
                IssuedInvoiceModel.translator.isnot(None),
                IssuedInvoiceModel.translator != "نامشخص",
            )
            .group_by(IssuedInvoiceModel.translator)
            .all()
        ]

        return InvoiceSummary(
            total_count=total_count,
            total_amount=total_amount,
            translator_stats=translator_stats,
        )

    def export_invoices_data(self, session: Session, invoice_numbers: List[str]) -> List[dict]:
        invoices = (
            session.query(IssuedInvoiceModel)
            .filter(IssuedInvoiceModel.invoice_number.in_(invoice_numbers))
            .all()
        )
        return [
            {
                "invoice_number": inv.invoice_number,
                "name": inv.name,
                "national_id": inv.national_id,
                "phone": inv.phone,
                "issue_date": inv.issue_date,
                "delivery_date": inv.delivery_date,
                "translator": inv.translator,
                "total_amount": inv.total_amount,
            }
            for inv in invoices
        ]

    def add_invoice_edits(self, session: Session, edits: List[EditedInvoiceData]) -> bool:
        try:
            orm_edits = [
                EditedInvoiceModel(
                    invoice_number=edit.invoice_number,
                    edited_field=edit.edited_field,
                    old_value=edit.old_value,
                    new_value=edit.new_value,
                    edited_by=edit.edited_by,
                    edited_at=edit.edited_at,
                    remarks=edit.remarks
                )
                for edit in edits
            ]
            session.bulk_save_objects(orm_edits)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False

    def get_edit_history_by_invoice_number(self, session: Session, invoice_number: str) -> List[EditedInvoiceData]:
        history_orm = (
            session.query(EditedInvoiceModel)
            .filter(EditedInvoiceModel.invoice_number == invoice_number)
            .order_by(EditedInvoiceModel.edited_at.desc())
            .all()
        )
        return [item.to_dataclass() for item in history_orm]

    def get_all_deleted_invoices(self, session: Session) -> List[DeletedInvoiceData]:
        invoices = (
            session.query(DeletedInvoiceModel)
            .order_by(DeletedInvoiceModel.deleted_at.desc())
            .all()
        )
        return [invoice.to_dataclass() for invoice in invoices]

    # ────────────────────────────────────────────────────────────── #
    #                             USERS                              #
    # ────────────────────────────────────────────────────────────── #

    def get_user_with_employee_details(
            self,
            users_session: Session,
            payroll_session: Session,
            username: str
    ) -> Optional[dict]:

        user = users_session.query(UsersModel).filter(
            UsersModel.username == username
        ).first()

        if not user:
            return None

        employee = None
        if user.employee_id:
            employee = payroll_session.query(EmployeeModel).filter(
                EmployeeModel.employee_id == user.employee_id
            ).first()

        return {
            'username': user.username,
            'role': user.role,
            'active': user.active,
            'display_name': user.display_name,
            'avatar_path': user.avatar_path,
            'employee_id': user.employee_id,
            'employee_name': employee.full_name if employee else None,
            'email': employee.email if employee else None,
            'phone': employee.phone_number if employee else None,
            'national_id': employee.national_id if employee else None,
        }

    def update_display_name(
            self,
            users_session: Session,
            username: str,
            new_display_name: str
    ) -> bool:
        try:
            user = users_session.query(UsersModel).filter(
                UsersModel.username == username
            ).first()

            if user:
                user.display_name = new_display_name
                users_session.commit()
                return True
            return False
        except Exception:
            users_session.rollback()
            return False


class PayrollRepository:
    """
    Repository for payroll-related database operations.
    """

    def get_translator_names(self, payroll_session: Session) -> List[str]:
        """
        Get a list of translator names from the payroll database.
        """
        translator_names = ["نامشخص"]
        try:
            translators = (
                payroll_session.query(EmployeeModel)
                .join(EmployeeRoleModel, EmployeeModel.role_id == EmployeeRoleModel.role_id)
                .filter(
                    EmployeeRoleModel.role_name_en == 'translator',
                    EmployeeModel.termination_date.is_(None)
                )
                .all()
            )

            for translator in translators:
                if translator.full_name:
                    translator_names.append(translator.full_name)

        except Exception as e:
            print(f"Error loading translator names: {e}")

        unique_names = sorted(list(set(translator_names) - {"نامشخص"}))
        return ["نامشخص"] + unique_names


class RepositoryManager:
    """Manager class to coordinate different repositories"""

    def __init__(self):
        self.business_repo = BusinessRepository()
        self.payroll_repo = PayrollRepository()

    def get_business_repository(self) -> BusinessRepository:
        return self.business_repo

    def get_payroll_repository(self) -> PayrollRepository:
        return self.payroll_repo
