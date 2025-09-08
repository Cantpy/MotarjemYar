# shared/enums.py
from enum import IntEnum


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
