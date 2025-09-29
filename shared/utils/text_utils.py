# shared/utils/text_utils.py

from num2fawords import words


def amount_to_persian_words(amount: int) -> str:
    """
    Converts a numerical amount to its Persian word representation.
    Returns an empty string if the amount is zero.
    """
    if amount == 0:
        return ""
    return words(amount)
