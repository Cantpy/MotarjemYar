# shared/utils/date_utils.py

import jdatetime
import re
from shared.utils.number_utils import to_persian_number


def sanitize_date_string(persian_date_str: str) -> str:
    """
    Converts any Persian numerals within a date-time string to their
    English equivalents, preserving the entire string structure.
    """
    if not persian_date_str:
        return ""

    # Dictionary for converting Persian numerals to English
    persian_to_english = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
    english_num_str = persian_date_str.translate(persian_to_english)

    # --- FIX: The line that removed the time has been deleted. ---
    # We now return the full string with converted numerals.
    return english_num_str


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


def convert_to_persian(date_str):
    """
    Convert a Gregorian date string (YYYY/MM/DD) to Persian date in YYYY/MM/DD format with Persian digits.
    """
    # Convert Persian digits map
    persian_digits = {
        '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
        '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
    }

    # Parse the Gregorian date
    year, month, day = map(int, date_str.split('/'))

    # Convert to jdatetime
    persian_date = jdatetime.date.fromgregorian(year=year, month=month, day=day)

    # Format as YYYY/MM/DD
    formatted = f"{persian_date.year:04}/{persian_date.month:02}/{persian_date.day:02}"

    # Convert to Persian digits
    persian_formatted = ''.join(persian_digits.get(c, c) for c in formatted)

    return persian_formatted


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
