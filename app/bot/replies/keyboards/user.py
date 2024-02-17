from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .base import button_menu, create_callback_buttons
from .buttons import (
    activate_user,
    cancel_operation,
    delete_user,
    show_user_profile,
    signup_user,
    switch_to_main_menu,
    update_user,
)

user_signup_menu = button_menu(
    signup_user, cancel_operation, switch_to_main_menu
)

user_activation_menu = button_menu(
    activate_user, cancel_operation, switch_to_main_menu
)

switch_to_user_profile = button_menu(
    show_user_profile, switch_to_main_menu, cancel_operation
)
user_profile_menu = button_menu(
    update_user, delete_user, cancel_operation, switch_to_main_menu
)
choose_signup_type = create_callback_buttons(
    button_names={
        "стандартная регистрация": "basic",
        "продвинутая регистрация": "advanced",
    },
    callback_prefix="signup_user",
    extra_buttons=[cancel_operation, switch_to_main_menu],
)

set_budget_currency_menu = create_callback_buttons(
    button_names={"установить валюту": "get_currency"},
    callback_prefix="signup_user",
    extra_buttons=[cancel_operation, switch_to_main_menu],
)

finish_advanced_signup = create_callback_buttons(
    button_names={
        "завершить": "basic",
    },
    callback_prefix="signup_user",
    extra_buttons=[cancel_operation, switch_to_main_menu],
)

signup_to_proceed = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Зарегистрироваться в один клик", callback_data="signup"
            )
        ]
    ]
)
