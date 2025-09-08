# shared/utils/login_utils.py

from typing import Optional


def get_persian_role_text(role: str, role_fa: Optional[str]) -> str:
    """Helper for converting role to display text."""
    if role_fa:
        return role_fa
    role_mapping = {'admin': 'مدیر', 'translator': 'مترجم', 'clerk': 'منشی', 'accountant': 'حسابدار'}
    return role_mapping.get(role, 'کاربر')
