from typing import Any

from aiogram.types import (
    ForceReply,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from app.bot.replies import prompts
from app.bot.replies.keyboards import common, user


class Template:
    def __init__(
        self,
        text: str,
        reply_markup: (
            InlineKeyboardMarkup
            | ReplyKeyboardMarkup
            | ReplyKeyboardRemove
            | ForceReply
            | None
        ) = None,
        /,
        **kwargs: Any,
    ):
        self._properties = kwargs
        self._properties.update(text=text, reply_markup=reply_markup)

    def __getitem__(self, key) -> Any:
        return self._properties.get(key)

    def __iter__(self):
        return iter(self._properties.items())

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._properties})"

    def keys(self):
        return self._properties.keys()


start_message_anonymous = Template(
    prompts.start_message_anonymous, user.user_signup_menu
)
start_message_inactive = Template(
    prompts.start_message_inactive, user.user_activation_menu
)
start_message_active = Template(
    prompts.start_message_active, common.switch_to_main_or_cancel
)
cancel_operation = Template(
    prompts.cancel_operation_note, ReplyKeyboardRemove()
)
main_menu = Template(prompts.main_menu_note, common.show_main_menu)
