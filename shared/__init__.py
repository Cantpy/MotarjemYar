# shared/__init__.py

from shared.utils.date_utils import (
    get_persian_date,
    get_current_jalali_datetime,
    format_jalali_date,
    parse_jalali_date,
    convert_to_persian
)
from shared.utils.number_utils import (
    persian_to_english_number,
    to_english_number,
    to_persian_number,
    format_number_with_separators,
    clean_number_string
)
from shared.utils.path_utils import (
    get_resource_path,
    get_remembered_user_info,
    open_file
)
from shared.utils.theme_utils import is_dark_theme
from shared.utils.ui_utils import (
    show_error_message_box,
    show_question_message_box,
    show_warning_message_box,
    show_information_message_box,
    show_field_error_form,
    show_field_error,
    clear_field_error,
    render_colored_svg,
    set_svg_icon,
)
from shared.utils.validation_utils import (
    validate_email,
    validate_phone_number,
    validate_national_id,
    validate_required_field,
    validate_numeric_field,
    validate_text_length
)
from shared.widgets.clickable_label import ClickableLabel
from shared.widgets.color_delegate import PriorityColorDelegate, PriorityColorDelegateNoRole
from shared.widgets.toast_widget import show_toast
from shared.theming.palettes import (
    set_spring_palette,
    set_summer_palette,
    set_autumn_palette,
    set_winter_palette,
    set_dark_palette
)
from shared.dialogs.language_dialog import LanguageDialog
from shared.dialogs.notification_dialog import NotificationDialog
from shared.dialogs.rich_text_editor import RichTextEdit
from shared.dialogs.status_change_dialog import StatusChangeDialog

from shared.context.user_context import UserContext


__all__ = [
    # date_utils
    "get_persian_date", "get_current_jalali_datetime", "format_jalali_date", "parse_jalali_date", "convert_to_persian",
    # number_utils
    "persian_to_english_number", "to_english_number", "to_persian_number",
    "format_number_with_separators", "clean_number_string",
    # path_utils
    "get_resource_path", "get_remembered_user_info", "open_file",
    # theme_utils
    "is_dark_theme",
    # ui_utils
    "show_error_message_box", "show_question_message_box", "show_warning_message_box",
    "show_information_message_box", "show_field_error_form", "show_field_error", "clear_field_error",
    "render_colored_svg", "set_svg_icon",
    # validation_utils
    "validate_email", "validate_phone_number", "validate_national_id",
    "validate_required_field", "validate_numeric_field", "validate_text_length",
    # widgets
    "ClickableLabel", "PriorityColorDelegate", "PriorityColorDelegateNoRole", "show_toast",
    # palettes
    "set_spring_palette", "set_summer_palette", "set_autumn_palette",
    "set_winter_palette", "set_dark_palette",
    # dialogs
    "LanguageDialog", "NotificationDialog", "RichTextEdit", "StatusChangeDialog",
    # user context
    "UserContext",
]
