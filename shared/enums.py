# shared/enums.py

from enum import IntEnum
import enum


class DeliveryStatus(IntEnum):
    """
    Defines the lifecycle of an invoice's delivery status.
    Behaves like an integer.
    """
    ISSUED = 0      # فاکتور صادر شده، هنوز برای ترجمه ارسال نشده
    ASSIGNED = 1    # مترجم تعیین شده
    TRANSLATED = 2  # اسناد ترجمه شده، آماده امضا و مهر
    READY = 3       # کاملاً آماده، منتظر دریافت توسط مشتری
    COLLECTED = 4   # توسط مشتری دریافت شده

    @classmethod
    def get_status_text(cls, status_code: int) -> str:
        """
        A class method to convert a status code to its Persian text representation.

        Args:
            status_code: The integer value of the status.

        Returns:
            The corresponding Persian string.
        """
        status_map = {
            cls.ISSUED: "صادر شده",
            cls.ASSIGNED: "در حال ترجمه",
            cls.TRANSLATED: "در انتظار تاییدات",
            cls.READY: "آماده تحویل",
            cls.COLLECTED: "تحویل داده شد"
        }
        # Use .get() to return a default value if the code is not found
        return status_map.get(status_code, "وضعیت نامشخص")


class ChatType(enum.Enum):
    ONE_ON_ONE = "one_on_one"
    GROUP = "group"
    CHANNEL = "channel"


class ParticipantRole(enum.Enum):
    MEMBER = "member"
    ADMIN = "admin"
