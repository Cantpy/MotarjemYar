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


class ChatType(enum.Enum):
    ONE_ON_ONE = "one_on_one"
    GROUP = "group"
    CHANNEL = "channel"


class ParticipantRole(enum.Enum):
    MEMBER = "member"
    ADMIN = "admin"
