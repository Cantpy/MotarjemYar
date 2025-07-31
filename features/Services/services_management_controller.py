"""services_management_controller.py - Controller layer for services management using PySide6"""

from typing import List, Dict, Any, Optional, Callable
from PySide6.QtCore import QObject, Signal
from services_management_logic import ServicesLogic, FixedPricesLogic, OtherServicesLogic, ValidationError


class BaseController(QObject):
    """Base controller with common functionality"""

    # Signals for UI updates
    data_changed = Signal()
    error_occurred = Signal(str, str)  # title, message
    success_occurred = Signal(str, str)  # title, message
    warning_occurred = Signal(str, str)  # title, message

    def emit_error(self, title: str, message: str):
        """Emit error signal"""
        self.error_occurred.emit(title, message)

    def emit_success(self, title: str, message: str):
        """Emit success signal"""
        self.success_occurred.emit(title, message)

    def emit_warning(self, title: str, message: str):
        """Emit warning signal"""
        self.warning_occurred.emit(title, message)


class ServicesController(BaseController):
    """Controller for services management"""

    def __init__(self, db_path: str, excel_path: str = None):
        super().__init__()
        self.logic = ServicesLogic(db_path, excel_path)
        self._data_cache = []

    def load_services(self) -> List[Dict[str, Any]]:
        """Load all services"""
        try:
            self._data_cache = self.logic.get_all_services()
            self.data_changed.emit()
            return self._data_cache
        except Exception as e:
            self.emit_error("خطا", f"خطا در بارگذاری مدارک:\n{str(e)}")
            return []

    def get_cached_data(self) -> List[Dict[str, Any]]:
        """Get cached data without database call"""
        return self._data_cache

    def create_service(self, service_data: Dict[str, Any]) -> bool:
        """Create new service"""
        try:
            created_service = self.logic.create_service(service_data)
            self.load_services()  # Refresh data
            self.emit_success("موفق", f"مدرک '{created_service['name']}' با موفقیت اضافه شد!")
            return True
        except ValidationError as e:
            self.emit_warning("خطا", str(e))
            return False
        except Exception as e:
            self.emit_error("خطا", f"خطا در افزودن مدرک:\n{str(e)}")
            return False

    def update_service(self, service_id: int, service_data: Dict[str, Any]) -> bool:
        """Update existing service"""
        try:
            updated_service = self.logic.update_service(service_id, service_data)
            if updated_service:
                self.load_services()  # Refresh data
                self.emit_success("موفق", f"مدرک '{updated_service['name']}' با موفقیت ویرایش شد!")
                return True
            else:
                self.emit_warning("خطا", "مدرک مورد نظر یافت نشد")
                return False
        except ValidationError as e:
            self.emit_warning("خطا", str(e))
            return False
        except Exception as e:
            self.emit_error("خطا", f"خطا در ویرایش مدرک:\n{str(e)}")
            return False

    def delete_service(self, service_id: int, service_name: str = "") -> bool:
        """Delete single service"""
        try:
            if self.logic.delete_service(service_id):
                self.load_services()  # Refresh data
                self.emit_success("موفق", f"مدرک '{service_name}' با موفقیت حذف شد!")
                return True
            else:
                self.emit_warning("خطا", "مدرک مورد نظر یافت نشد")
                return False
        except Exception as e:
            self.emit_error("خطا", f"خطا در حذف مدرک:\n{str(e)}")
            return False

    def delete_multiple_services(self, service_ids: List[int]) -> bool:
        """Delete multiple services"""
        try:
            deleted_count = self.logic.delete_multiple_services(service_ids)
            if deleted_count > 0:
                self.load_services()  # Refresh data
                self.emit_success("موفق", f"{deleted_count} مدرک با موفقیت حذف شدند!")
                return True
            else:
                self.emit_warning("خطا", "هیچ مدرکی حذف نشد")
                return False
        except Exception as e:
            self.emit_error("خطا", f"خطا در حذف مدارک:\n{str(e)}")
            return False

    def search_services(self, search_term: str) -> List[Dict[str, Any]]:
        """Search services"""
        try:
            return self.logic.search_services(search_term)
        except Exception as e:
            self.emit_error("خطا", f"خطا در جستجو:\n{str(e)}")
            return []

    def import_from_excel(self, confirmation_callback: Callable = None) -> bool:
        """Import services from Excel with confirmation"""
        try:
            if confirmation_callback and not confirmation_callback():
                return False

            imported_count, errors = self.logic.import_from_excel()

            if errors:
                error_msg = f"تعداد {imported_count} مدرک وارد شد با خطاهای زیر:\n" + "\n".join(errors[:5])
                if len(errors) > 5:
                    error_msg += f"\n... و {len(errors) - 5} خطای دیگر"
                self.emit_warning("هشدار", error_msg)
            else:
                self.emit_success("موفق", f"تعداد {imported_count} مدرک با موفقیت از اکسل وارد شد!")

            self.load_services()  # Refresh data
            return True

        except ValidationError as e:
            self.emit_warning("خطا", str(e))
            return False
        except Exception as e:
            self.emit_error("خطا", f"خطا در بارگذاری از اکسل:\n{str(e)}")
            return False


class FixedPricesController(BaseController):
    """Controller for fixed prices management"""

    def __init__(self, db_path: str):
        super().__init__()
        self.logic = FixedPricesLogic(db_path)
        self._data_cache = []

    def load_fixed_prices(self) -> List[Dict[str, Any]]:
        """Load all fixed prices"""
        try:
            self._data_cache = self.logic.get_all_fixed_prices()
            self.data_changed.emit()
            return self._data_cache
        except Exception as e:
            self.emit_error("خطا", f"خطا در بارگذاری هزینه‌های ثابت:\n{str(e)}")
            return []

    def get_cached_data(self) -> List[Dict[str, Any]]:
        """Get cached data without database call"""
        return self._data_cache

    def create_fixed_price(self, price_data: Dict[str, Any]) -> bool:
        """Create new fixed price"""
        try:
            created_price = self.logic.create_fixed_price(price_data)
            self.load_fixed_prices()  # Refresh data
            self.emit_success("موفق", f"هزینه ثابت '{created_price['name']}' با موفقیت اضافه شد!")
            return True
        except ValidationError as e:
            self.emit_warning("خطا", str(e))
            return False
        except Exception as e:
            self.emit_error("خطا", f"خطا در افزودن هزینه ثابت:\n{str(e)}")
            return False

    def update_fixed_price(self, price_id: int, price_data: Dict[str, Any]) -> bool:
        """Update existing fixed price"""
        try:
            updated_price = self.logic.update_fixed_price(price_id, price_data)
            if updated_price:
                self.load_fixed_prices()  # Refresh data
                self.emit_success("موفق", f"هزینه ثابت '{updated_price['name']}' با موفقیت ویرایش شد!")
                return True
            else:
                self.emit_warning("خطا", "هزینه ثابت مورد نظر یافت نشد")
                return False
        except ValidationError as e:
            self.emit_warning("خطا", str(e))
            return False
        except Exception as e:
            self.emit_error("خطا", f"خطا در ویرایش هزینه ثابت:\n{str(e)}")
            return False

    def delete_fixed_price(self, price_id: int, price_name: str = "") -> bool:
        """Delete single fixed price"""
        try:
            if self.logic.delete_fixed_price(price_id):
                self.load_fixed_prices()  # Refresh data
                self.emit_success("موفق", f"هزینه ثابت '{price_name}' با موفقیت حذف شد!")
                return True
            else:
                self.emit_warning("خطا", "هزینه ثابت مورد نظر یافت نشد یا قابل حذف نیست")
                return False
        except Exception as e:
            self.emit_error("خطا", f"خطا در حذف هزینه ثابت:\n{str(e)}")
            return False

    def delete_multiple_fixed_prices(self, price_ids: List[int]) -> bool:
        """Delete multiple fixed prices"""
        try:
            deleted_count = self.logic.delete_multiple_fixed_prices(price_ids)
            if deleted_count > 0:
                self.load_fixed_prices()  # Refresh data
                self.emit_success("موفق", f"{deleted_count} هزینه ثابت با موفقیت حذف شدند!")
                return True
            else:
                self.emit_warning("خطا", "هیچ هزینه ثابتی حذف نشد (ممکن است پیش‌فرض باشند)")
                return False
        except Exception as e:
            self.emit_error("خطا", f"خطا در حذف هزینه‌های ثابت:\n{str(e)}")
            return False

    def search_fixed_prices(self, search_term: str) -> List[Dict[str, Any]]:
        """Search fixed prices"""
        try:
            return self.logic.search_fixed_prices(search_term)
        except Exception as e:
            self.emit_error("خطا", f"خطا در جستجو:\n{str(e)}")
            return []


class OtherServicesController(BaseController):
    """Controller for other services management"""

    def __init__(self, db_path: str):
        super().__init__()
        self.logic = OtherServicesLogic(db_path)
        self._data_cache = []

    def load_other_services(self) -> List[Dict[str, Any]]:
        """Load all other services"""
        try:
            self._data_cache = self.logic.get_all_other_services()
            self.data_changed.emit()
            return self._data_cache
        except Exception as e:
            self.emit_error("خطا", f"خطا در بارگذاری سایر خدمات:\n{str(e)}")
            return []

    def get_cached_data(self) -> List[Dict[str, Any]]:
        """Get cached data without database call"""
        return self._data_cache

    def create_other_service(self, service_data: Dict[str, Any]) -> bool:
        """Create new other service"""
        try:
            created_service = self.logic.create_other_service(service_data)
            self.load_other_services()  # Refresh data
            self.emit_success("موفق", f"خدمت '{created_service['name']}' با موفقیت اضافه شد!")
            return True
        except ValidationError as e:
            self.emit_warning("خطا", str(e))
            return False
        except Exception as e:
            self.emit_error("خطا", f"خطا در افزودن خدمت:\n{str(e)}")
            return False

    def update_other_service(self, service_id: int, service_data: Dict[str, Any]) -> bool:
        """Update existing other service"""
        try:
            updated_service = self.logic.update_other_service(service_id, service_data)
            if updated_service:
                self.load_other_services()  # Refresh data
                self.emit_success("موفق", f"خدمت '{updated_service['name']}' با موفقیت ویرایش شد!")
                return True
            else:
                self.emit_warning("خطا", "خدمت مورد نظر یافت نشد")
                return False
        except ValidationError as e:
            self.emit_warning("خطا", str(e))
            return False
        except Exception as e:
            self.emit_error("خطا", f"خطا در ویرایش خدمت:\n{str(e)}")
            return False

    def delete_other_service(self, service_id: int, service_name: str = "") -> bool:
        """Delete single other service"""
        try:
            if self.logic.delete_other_service(service_id):
                self.load_other_services()  # Refresh data
                self.emit_success("موفق", f"خدمت '{service_name}' با موفقیت حذف شد!")
                return True
            else:
                self.emit_warning("خطا", "خدمت مورد نظر یافت نشد یا قابل حذف نیست")
                return False
        except Exception as e:
            self.emit_error("خطا", f"خطا در حذف خدمت:\n{str(e)}")
            return False

    def delete_multiple_other_services(self, service_ids: List[int]) -> bool:
        """Delete multiple other services"""
        try:
            deleted_count = self.logic.delete_multiple_other_services(service_ids)
            if deleted_count > 0:
                self.load_other_services()  # Refresh data
                self.emit_success("موفق", f"{deleted_count} خدمت با موفقیت حذف شدند!")
                return True
            else:
                self.emit_warning("خطا", "هیچ خدمتی حذف نشد (ممکن است پیش‌فرض باشند)")
                return False
        except Exception as e:
            self.emit_error("خطا", f"خطا در حذف خدمات:\n{str(e)}")
            return False

    def search_other_services(self, search_term: str) -> List[Dict[str, Any]]:
        """Search other services"""
        try:
            return self.logic.search_other_services(search_term)
        except Exception as e:
            self.emit_error("خطا", f"خطا در جستجو:\n{str(e)}")
            return []
