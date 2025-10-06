# shared/utils/date_utils.py

import jdatetime
import re
from datetime import date, datetime
from typing import Optional, Union
from shared.utils.number_utils import to_persian_number


# --- PRIMARY CONVERSION FUNCTIONS ---

def to_jalali(datetime_input) -> str:
    """
    Converts various datetime/date/string inputs to Jalali format: YYYY/MM/DD - HH:MM
    Accepts:
      - datetime.datetime
      - datetime.date
      - string (various formats, with or without time, with or without microseconds)
    """
    # Step 1: Normalize input
    if isinstance(datetime_input, datetime):
        dt = datetime_input
    elif isinstance(datetime_input, date):
        # Convert to datetime with 00:00 time
        dt = datetime.combine(datetime_input, datetime.min.time())
    elif isinstance(datetime_input, str):
        # Try multiple formats
        formats = [
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S.%f",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%Y/%m/%d",
            "%Y/%m/%d - %H:%M"
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(datetime_input, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Unsupported datetime string format: {datetime_input}")
    else:
        raise TypeError(
            f"datetime_input must be a datetime, date, or str — got {type(datetime_input)}"
        )

    # Step 2: Convert to Jalali
    jdt = jdatetime.datetime.fromgregorian(datetime=dt)

    # Step 3: Return formatted string
    return to_persian_number(jdt.strftime("%Y/%m/%d - %H:%M"))


def to_jalali_string(gregorian_date_obj: Optional[Union[date, datetime]]) -> str:
    """
    Converts a Gregorian date or datetime object to a formatted Jalali string
    with Persian numerals, suitable for display in the UI.

    - If the input is a datetime object, it returns "YYYY/MM/DD - HH:MM".
    - If the input is a date object, it returns "YYYY/MM/DD".
    - If the input is None, it returns an empty string.

    Args:
        gregorian_date_obj: The Gregorian date or datetime object to convert.

    Returns:
        A formatted Jalali date string with Persian numerals.
    """
    if not gregorian_date_obj:
        return ""

    try:
        # Check if the object has a time component
        if isinstance(gregorian_date_obj, datetime):
            jalali_dt = jdatetime.datetime.fromgregorian(dt=gregorian_date_obj)
            formatted_str = jalali_dt.strftime("%Y/%m/%d - %H:%M")
        # Otherwise, treat it as a date
        else:
            jalali_dt = jdatetime.date.fromgregorian(date=gregorian_date_obj)
            formatted_str = jalali_dt.strftime("%Y/%m/%d")

        return to_persian_number(formatted_str)
    except Exception as e:
        print(f'failed to gregorian to jalali date: {e}')
        return "تاریخ نامعتبر"


def gregorian_str_to_jalali_str(
    gregorian_str: Optional[str],
    use_persian_numbers: bool = True
) -> str:
    """
    Converts a Gregorian datetime string (e.g. '2025/10/05 - 12:10')
    to a Jalali datetime string ('1404/07/13 - 12:10').

    If the time part is '00:00', it is omitted.

    Args:
        gregorian_str: Gregorian date-time string in '%Y/%m/%d - %H:%M' or '%Y/%m/%d' format
        use_persian_numbers: If True, output will use Persian numerals

    Returns:
        str: Jalali date(-time) string (Persian or English numerals)
    """
    if not gregorian_str:
        return ""

    try:
        formatted = ""
        # Parse the string
        if " - " in gregorian_str:
            g_dt = datetime.strptime(gregorian_str.strip(), "%Y/%m/%d - %H:%M")
            j_dt = jdatetime.datetime.fromgregorian(datetime=g_dt)
            # Only include time if it's not midnight
            if j_dt.hour == 0 and j_dt.minute == 0:
                formatted = j_dt.strftime("%Y/%m/%d")
            else:
                formatted = j_dt.strftime("%Y/%m/%d - %H:%M")
        else:
            g_date = datetime.strptime(gregorian_str.strip(), "%Y/%m/%d").date()
            j_date = jdatetime.date.fromgregorian(date=g_date)
            formatted = j_date.strftime("%Y/%m/%d")

        return to_persian_number(formatted) if use_persian_numbers else formatted

    except Exception as e:
        print(f"Failed to convert Gregorian string to Jalali: {e}")
        return "تاریخ نامعتبر"


def get_gregorian_now_to_minute() -> datetime:
    """Return current Gregorian datetime truncated to minute precision."""
    now = datetime.now()
    # Remove seconds and microseconds to match '%Y/%m/%d - %H:%M'
    return now.replace(second=0, microsecond=0)


def jalali_obj_to_gregorian(
    jalali_obj: Optional[Union[jdatetime.date, jdatetime.datetime]]
) -> Optional[Union[date, datetime]]:
    """
    Converts a Jalali date or datetime object to its Gregorian equivalent.

    - If the input is a jdatetime.datetime, returns a datetime.datetime.
    - If the input is a jdatetime.date, returns a datetime.date.
    - Returns None if input is invalid or None.

    Args:
        jalali_obj: The Jalali date or datetime object to convert.

    Returns:
        datetime.date or datetime.datetime or None
    """
    if not jalali_obj:
        return None

    try:
        return jalali_obj.togregorian()
    except Exception as e:
        print(f"Failed to convert Jalali object to Gregorian: {e}")
        return None


def to_gregorian(
    jalali_input: Optional[Union[str, jdatetime.date, jdatetime.datetime, date, datetime]],
    force_datetime: bool = False
) -> Optional[Union[date, datetime]]:
    """
    Robust converter that accepts:
      - Jalali string like "۱۴۰۴/۰۷/۱۳ - ۱۱:۲۳" or "۱۴۰۴/۰۷/۲۱"
      - jdatetime.date or jdatetime.datetime
      - already-Gregorian date/datetime (returns as-is)

    Returns:
      - datetime.datetime if input contains time (or force_datetime=True)
      - datetime.date if input is date-only
      - None on invalid input
    """
    if jalali_input is None or jalali_input == "":
        return None

    # If it's already a Python datetime/date, return it (respect force_datetime)
    if isinstance(jalali_input, datetime):
        return jalali_input
    if isinstance(jalali_input, date) and not isinstance(jalali_input, datetime):
        if force_datetime:
            return datetime(jalali_input.year, jalali_input.month, jalali_input.day)
        return jalali_input

    # jdatetime objects -> togregorian()
    if isinstance(jalali_input, jdatetime.datetime):
        return jalali_input.togregorian()
    if isinstance(jalali_input, jdatetime.date):
        g = jalali_input.togregorian()
        if force_datetime:
            # convert date -> datetime at midnight
            return datetime(g.year, g.month, g.day)
        return g  # date

    # Strings: sanitize Persian digits then regex-parse (robust)
    if isinstance(jalali_input, str):
        s = sanitize_date_string(jalali_input).strip()
        # Accept forms like:
        # YYYY/MM/DD - HH:MM   OR   YYYY/MM/DD-HH:MM   OR   YYYY/MM/DD
        m = re.match(r'^\s*(\d{4})/(\d{1,2})/(\d{1,2})(?:\s*-\s*|\s*-\s*?|\s+)?(?:([0-2]?\d):([0-5]?\d))?\s*$', s)
        if not m:
            return None
        y, mo, d, hh, mm = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        y, mo, d = int(y), int(mo), int(d)
        if hh is not None and mm is not None:
            hh, mm = int(hh), int(mm)
            jal = jdatetime.datetime(y, mo, d, hh, mm)
            return jal.togregorian()
        else:
            jal = jdatetime.date(y, mo, d)
            g = jal.togregorian()
            if force_datetime:
                return datetime(g.year, g.month, g.day)
            return g

    # Unsupported type
    return None


# --- HELPER AND EXISTING FUNCTIONS ---

def sanitize_date_string(persian_date_str: str) -> str:
    """
    Converts any Persian numerals within a date-time string to their
    English equivalents, preserving the entire string structure.
    """
    if not persian_date_str:
        return ""
    persian_to_english = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
    return persian_date_str.translate(persian_to_english)


def get_persian_date():
    """
    Get the current Persian date and time formatted as string.

    Returns:
        str: Formatted Persian date and time (e.g., "۱۴۰۳/۰۱/۲۸ - ۱۵:۳۰")
    """
    now = jdatetime.datetime.now()
    formatted_date = now.strftime("%Y/%m/%d - %H:%M")
    return to_persian_number(formatted_date)


def get_current_jalali_datetime():
    """
    Get current Jalali datetime object.

    Returns:
        jdatetime.datetime: Current Jalali datetime
    """
    return jdatetime.datetime.now()
