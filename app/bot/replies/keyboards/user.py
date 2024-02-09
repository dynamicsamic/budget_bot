from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .base import button_menu, create_callback_buttons
from .buttons import (
    activate_user,
    cancel_operation,
    show_user_profile,
    signup_user,
    switch_to_main_menu,
)

user_signup_menu = button_menu(
    signup_user, cancel_operation, switch_to_main_menu
)

user_activation_menu = button_menu(
    activate_user, cancel_operation, switch_to_main_menu
)

user_profile_menu = button_menu(
    show_user_profile, cancel_operation, switch_to_main_menu
)

choose_signup_type = create_callback_buttons(
    button_names={
        "стандартная регистрация": "basic",
        "продвинутая регистрация": "advanced",
    },
    callback_prefix="signup_user",
    extra_buttons=[cancel_operation, switch_to_main_menu],
)

finish_signup = create_callback_buttons(
    button_names={
        "завершить": "finish",
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
