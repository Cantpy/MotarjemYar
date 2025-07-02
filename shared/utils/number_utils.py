"""
Number conversion utilities for Persian/English numerals.
"""


def persian_to_english_number(persian_str):
    """
    Convert Persian/Arabic numerals to English numerals.

    Args:
        persian_str (str): String containing Persian numerals

    Returns:
        str: String with English numerals
    """
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    english_digits = "0123456789"
    trans_table = str.maketrans(persian_digits, english_digits)
    return persian_str.translate(trans_table)


def to_persian_number(number):
    """
    Convert an integer or string with separators to its Persian numeral representation.

    Args:
        number (int|str): Number to convert

    Returns:
        str: Number with Persian numerals
    """
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    return "".join(persian_digits[int(digit)] if digit.isdigit() else digit for digit in str(number))


def to_english_number(persian_str):
    """
    Alias for persian_to_english_number for consistency.

    Args:
        persian_str (str): String containing Persian numerals

    Returns:
        str: String with English numerals
    """
    return persian_to_english_number(persian_str)


def format_number_with_separators(number, separator=","):
    """
    Format a number with thousand separators.

    Args:
        number (int|float|str): Number to format
        separator (str): Separator character (default: comma)

    Returns:
        str: Formatted number string
    """
    try:
        if isinstance(number, str):
            # Remove existing separators first
            clean_number = number.replace(",", "").replace("٬", "")
            number = float(clean_number) if '.' in clean_number else int(clean_number)

        return f"{number:,}".replace(",", separator)
    except (ValueError, TypeError):
        return str(number)


def clean_number_string(number_str):
    """
    Clean a number string by removing separators and converting to English numerals.

    Args:
        number_str (str): Number string to clean

    Returns:
        str: Clean number string
    """
    if not isinstance(number_str, str):
        return str(number_str)

    # Convert Persian to English numerals
    cleaned = persian_to_english_number(number_str)

    # Remove common separators
    cleaned = cleaned.replace(",", "").replace("٬", "").replace(" ", "")

    return cleaned
