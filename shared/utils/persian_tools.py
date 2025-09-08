# motarjemyar/shared/utils/persian_tools.py

import jdatetime
from datetime import date
from shared.enums import DeliveryStatus

# Mapping of Persian to English numbers
PERSIAN_TO_ENGLISH_MAP = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
ENGLISH_TO_PERSIAN_MAP = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')


def to_persian_numbers(text: str | int) -> str:
    """Converts a string or integer containing English numbers to Persian numbers."""
    return str(text).translate(ENGLISH_TO_PERSIAN_MAP)


def to_english_numbers(text: str) -> str:
    """Converts a string containing Persian numbers to English numbers."""
    return str(text).translate(PERSIAN_TO_ENGLISH_MAP)


def to_jalali_string(g_date: date) -> str:
    """Converts a Gregorian date object to a standard Jalali date string (YYYY/MM/DD)."""
    if not isinstance(g_date, date):
        return str(g_date) # Return as is if not a date object
    return jdatetime.date.fromgregorian(date=g_date).strftime('%Y/%m/%d')


def to_persian_jalali_string(g_date: date) -> str:
    """Converts a Gregorian date object to a Jalali date string with Persian numbers."""
    jalali_str = to_jalali_string(g_date)
    return to_persian_numbers(jalali_str)


def get_persian_delivery_status(status: DeliveryStatus) -> str:
    """Helper function to get display text for a status."""
    status_map = {
        DeliveryStatus.ISSUED: "صادر شده",
        DeliveryStatus.ASSIGNED: "مترجم تعیین شده",
        DeliveryStatus.TRANSLATED: "ترجمه شده",
        DeliveryStatus.READY: "آماده تحویل",
        DeliveryStatus.COLLECTED: "تحویل داده شده"
    }
    return status_map.get(status, "نامشخص")