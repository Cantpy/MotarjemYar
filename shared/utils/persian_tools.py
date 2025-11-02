# motarjemyar/shared/utils/persian_tools.py

import jdatetime
from datetime import date
from shared.enums import DeliveryStatus

# Mapping of Persian to English numbers
PERSIAN_TO_ENGLISH_MAP = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
ENGLISH_TO_PERSIAN_MAP = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')


def to_persian_numbers(value: str | int | float) -> str:
    """
    Converts English digits (and decimal dot) to Persian.
    Handles int, float, and str inputs.
    """
    return str(value).translate(ENGLISH_TO_PERSIAN_MAP)


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


def number_to_words_fa(n):
    """Converts an integer number to Persian words."""
    if n == 0:
        return 'صفر'

    ones = ['', 'یک', 'دو', 'سه', 'چهار', 'پنج', 'شش', 'هفت', 'هشت', 'نه']
    tens = ['', 'ده', 'بیست', 'سی', 'چهل', 'پنجاه', 'شصت', 'هفتاد', 'هشتاد', 'نود']
    teens = ['ده', 'یازده', 'دوازده', 'سیزده', 'چهارده', 'پانزده', 'شانزده', 'هفده', 'هجده', 'نوزده']
    hundreds = ['', 'یکصد', 'دویست', 'سیصد', 'چهارصد', 'پانصد', 'ششصد', 'هفتصد', 'هشتصد', 'نهصد']
    thousands = ['', 'هزار', 'میلیون', 'میلیارد', 'تریلیون']

    def get_word(num_str):
        num = int(num_str)
        if num == 0:
            return ''

        parts = []
        if len(num_str) == 3:
            h, t, o = int(num_str[0]), int(num_str[1]), int(num_str[2])
            if h > 0:
                parts.append(hundreds[h])
            if t == 1:
                parts.append(teens[o])
            else:
                if t > 1:
                    parts.append(tens[t])
                if o > 0:
                    parts.append(ones[o])
        elif len(num_str) == 2:
            t, o = int(num_str[0]), int(num_str[1])
            if t == 1:
                parts.append(teens[o])
            else:
                if t > 1:
                    parts.append(tens[t])
                if o > 0:
                    parts.append(ones[o])
        elif len(num_str) == 1:
            o = int(num_str[0])
            if o > 0:
                parts.append(ones[o])

        return ' و '.join(parts)

    s = str(int(n))
    if len(s) > 15:
        return "عدد بسیار بزرگ است"

    groups = []
    while len(s) > 0:
        groups.append(s[-3:])
        s = s[:-3]

    word_parts = []
    for i in range(len(groups) - 1, -1, -1):
        group_word = get_word(groups[i])
        if group_word:
            part = group_word
            if i > 0:
                part += ' ' + thousands[i]
            word_parts.append(part)

    return ' و '.join(word_parts)
