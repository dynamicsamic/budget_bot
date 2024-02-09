from .base import button_menu
from .buttons import (
    cancel_operation,
    entry_menu,
    report_menu,
    show_categories,
    show_user_profile,
    switch_to_main_menu,
)

show_main_menu = button_menu(
    show_user_profile,
    show_categories,
    entry_menu,
    report_menu,
)

switch_to_main = button_menu(switch_to_main_menu)
switch_to_main_or_cancel = button_menu(switch_to_main_menu, cancel_operation)
