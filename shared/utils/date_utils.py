"""
Date and time utilities for Persian calendar support.
"""
import jdatetime
import re
from shared.utils.number_utils import to_persian_number


def get_persian_date():
    """
    Get the current Persian date and time formatted as string.

    Returns:
        str: Formatted Persian date and time (e.g., "۱۴۰۳/۰۱/۲۸ - ۱۵:۳۰")
    """
    now = jdatetime.datetime.now()
    # Formatted date and time (e.g., "1403/01/28 - 15:30")
    formatted_date = now.strftime("%Y/%m/%d - %H:%M")
    return to_persian_number(formatted_date)


def get_current_jalali_datetime():
    """
    Get current Jalali datetime object.

    Returns:
        jdatetime.datetime: Current Jalali datetime
    """
    return jdatetime.datetime.now()


def format_jalali_date(dt, format_string="%Y/%m/%d"):
    """
    Format a Jalali datetime object to string.

    Args:
        dt (jdatetime.datetime): Jalali datetime object
        format_string (str): Format string for output

    Returns:
        str: Formatted date string
    """
    return dt.strftime(format_string)


def parse_jalali_date(jalali_str):
    """
    Parses a Jalali date from 'YYYY/MM/DD' or 'YYYY/MM/DD - HH:MM' to Gregorian date.

    Args:
        jalali_str: Jalali datetime string

    Returns:
        str: formatted Gregorian date
    """
    try:
        # Extract only the date part
        match = re.match(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", jalali_str)
        if not match:
            return None
        year, month, day = map(int, match.groups())
        j_date = jdatetime.date(year, month, day)
        return j_date.togregorian()
    except Exception:
        return None
