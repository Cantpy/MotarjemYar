from typing import Dict, List, Optional, Tuple
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from modules.Documents.models.fixed_costs_models import FixedPrice, db_manager
from modules.helper_functions import (show_question_message_box, show_error_message_box, show_warning_message_box,
                                      show_information_message_box, to_persian_number)


class FixedCostsService:
    """ServicesModel class for managing fixed costs business logic."""

    DEFAULT_FIXED_COSTS = [
        "کپی برابر اصل",
        "ثبت در سامانه (امور دفتری)",
        "مهر دادگستری",
        "مهر امور خارجه",
        "نسخه اضافی"
    ]

    def __init__(self):
        self.db_manager = db_manager
        self.db_manager.create_tables()

    def get_all_fixed_costs(self) -> List[FixedPrice]:
        """Get all fixed costs from database, ordered by is_default DESC, name ASC."""
        session = self.db_manager.get_session()
        try:
            return session.query(FixedPrice).order_by(
                FixedPrice.is_default.desc(),
                FixedPrice.name.asc()
            ).all()
        finally:
            self.db_manager.close_session(session)

    def get_fixed_cost_by_id(self, cost_id: int) -> Optional[FixedPrice]:
        """Get a fixed cost by ID."""
        session = self.db_manager.get_session()
        try:
            return session.query(FixedPrice).filter(FixedPrice.id == cost_id).first()
        finally:
            self.db_manager.close_session(session)

    def add_fixed_cost(self, parent_widget, service_data: Dict[str, str]) -> bool:
        """
        Add a new fixed cost to the database.

        Args:
            parent_widget: Parent widget for message boxes
            service_data (Dict[str, str]): Dictionary with 'fixed_cost' and 'cost' keys

        Returns:
            bool: True if successful, False otherwise
        """
        session = self.db_manager.get_session()
        try:
            # Extract and validate data
            name = service_data.get('fixed_cost', '').strip()
            cost = service_data.get('cost', '0')

            if not name:
                show_warning_message_box(parent_widget, "خطا", "نام هزینه ثابت نمی‌تواند خالی باشد")
                return False

            # Convert cost to integer
            try:
                price = int(cost)
            except ValueError:
                message = (f"قیمت وارد شده {cost} نامعتبر است.\n"
                           f"\nلطفا هزینه را به صورت رقمی و بدون کاما وارد کنید."
                           f"هنگام وارد کردن هزینه مطمئن شوید از کیبورد انگلیسی یا فارسی FA استفاده می‌کنید (نه FAS).")
                show_warning_message_box(parent_widget, "خطا", message)
                return False

            # Create new fixed cost
            new_cost = FixedPrice(name=name, price=price, is_default=False)
            session.add(new_cost)
            session.commit()

            # Success message
            formatted_price = f"{price:,}"
            persian_price = f"{to_persian_number(formatted_price)}"
            message = (f"اطلاعات زیر با موفقیت به پایگاه داده اضافه شد:\n"
                       f"نام خدمت: {name}\n"
                       f"هزینه خدمت: {persian_price} تومان")
            show_information_message_box(parent_widget, "موفق", message)
            return True

        except IntegrityError as e:
            session.rollback()
            if "UNIQUE constraint failed" in str(e):
                message = f"خدمتی با نام '{name}' قبلا در پایگاه داده ثبت شده است."
                show_warning_message_box(parent_widget, "خطا", message)
            else:
                show_error_message_box(parent_widget, "خطا", str(e))
            return False
        except Exception as e:
            session.rollback()
            message = f"خطا در افزودن خدمت به پایگاه داده:\n{e}"
            show_error_message_box(parent_widget, "خطا", message)
            return False
        finally:
            self.db_manager.close_session(session)

    def edit_fixed_cost(self, parent_widget, cost_id: int, service_data: Dict[str, str]) -> bool:
        """
        Edit an existing fixed cost.

        Args:
            parent_widget: Parent widget for message boxes
            cost_id (int): ID of the fixed cost to update
            service_data (Dict[str, str]): Dictionary with 'fixed_cost' and 'cost' keys

        Returns:
            bool: True if successful, False otherwise
        """
        session = self.db_manager.get_session()
        try:
            # Extract and validate data
            name = service_data.get('fixed_cost', '').strip()
            cost = service_data.get('cost', '0')

            if not name:
                show_warning_message_box(parent_widget, "خطا", "نام هزینه ثابت نمی‌تواند خالی باشد")
                return False

            # Convert cost to integer
            try:
                price = int(cost)
            except ValueError:
                message = (f"قیمت وارد شده {cost} نامعتبر است.\n"
                           f"لطفا هزینه را به صورت رقمی و بدون کاما وارد کنید."
                           f"\nهنگام وارد کردن هزینه مطمئن شوید از کیبورد انگلیسی یا فارسی FA استفاده می‌کنید (نه FAS).")
                show_warning_message_box(parent_widget, "خطا", message)
                return False

            # Find and update the fixed cost
            fixed_cost = session.query(FixedPrice).filter(FixedPrice.id == cost_id).first()
            if not fixed_cost:
                message = (f"این هزینه ثابت در پایگاه داده پیدا نشد.\n"
                           f"شناسه در پایگاه داده: {cost_id}")
                show_error_message_box(parent_widget, "خطا", message)
                return False

            # Update fields
            fixed_cost.name = name
            fixed_cost.price = price
            session.commit()

            # Success message
            formatted_price = f"{price:,}"
            persian_price = f"{to_persian_number(formatted_price)}"
            message = (f"هزینه ثابت شما با شناسه {cost_id} در پایگاه داده بروزرسانی شد.\n"
                       f"نام جدید: {name}، هزینه جدید: {persian_price}")
            show_information_message_box(parent_widget, "موفق", message)
            return True

        except IntegrityError as e:
            session.rollback()
            if "UNIQUE constraint failed" in str(e):
                message = f"هزینه ثابتی با نام '{name}' قبلا در پایگاه داده ثبت شده است."
                show_warning_message_box(parent_widget, "خطا", message)
            else:
                show_error_message_box(parent_widget, "خطا", str(e))
            return False
        except Exception as e:
            session.rollback()
            message = f"خطا در ویرایش هزینه ثابت:\n{e}"
            show_error_message_box(parent_widget, "خطا", message)
            return False
        finally:
            self.db_manager.close_session(session)

    def delete_fixed_cost(self, parent_widget, cost_id: int, cost_name: str) -> bool:
        """
        Delete a fixed cost by ID.

        Args:
            parent_widget: Parent widget for message boxes
            cost_id (int): ID of the fixed cost to delete
            cost_name (str): Name of the cost for confirmation message

        Returns:
            bool: True if successful, False otherwise
        """
        session = self.db_manager.get_session()
        try:
            # Find the fixed cost
            fixed_cost = session.query(FixedPrice).filter(
                FixedPrice.id == cost_id,
                FixedPrice.is_default == False
            ).first()

            if not fixed_cost:
                message = "هزینه ثابت حذف نشد. ممکن است هزینه پیش‌فرض باشد."
                show_warning_message_box(parent_widget, "خطا", message)
                return False

            session.delete(fixed_cost)
            session.commit()

            message = f"هزینه ثابت '{cost_name}' با موفقیت حذف شد!"
            show_information_message_box(parent_widget, "موفق", message)
            return True

        except Exception as e:
            session.rollback()
            message = f"خطا در حذف هزینه ثابت:\n{str(e)}"
            show_error_message_box(parent_widget, "خطای پایگاه داده", message)
            return False
        finally:
            self.db_manager.close_session(session)

    def bulk_delete_fixed_costs(self, parent_widget, cost_ids: List[int]) -> Tuple[bool, int]:
        """
        Delete multiple fixed costs by IDs.

        Args:
            parent_widget: Parent widget for message boxes
            cost_ids (List[int]): List of cost IDs to delete

        Returns:
            Tuple[bool, int]: (Success status, number of deleted items)
        """
        session = self.db_manager.get_session()
        try:
            # Delete non-default items only
            deleted_count = session.query(FixedPrice).filter(
                FixedPrice.id.in_(cost_ids),
                FixedPrice.is_default == False
            ).delete(synchronize_session=False)

            session.commit()

            if deleted_count > 0:
                message = f"{deleted_count} مورد با موفقیت حذف شد!"
                show_information_message_box(parent_widget, "موفق", message)
                return True, deleted_count
            else:
                message = "هیچ موردی حذف نشد. ممکن است موارد انتخابی از نوع پیش‌فرض باشند."
                show_warning_message_box(parent_widget, "خطا", message)
                return False, 0

        except Exception as e:
            session.rollback()
            message = f"خطا در حذف موارد:\n{str(e)}"
            show_error_message_box(parent_widget, "خطای پایگاه داده", message)
            return False, 0
        finally:
            self.db_manager.close_session(session)

    def is_default_cost(self, cost_name: str) -> bool:
        """Check if a cost name is in the default costs list."""
        return cost_name in self.DEFAULT_FIXED_COSTS
