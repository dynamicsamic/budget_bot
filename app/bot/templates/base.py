from typing import Any, Iterable

from aiogram.types import (
    ForceReply,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.custom_types import _BaseModel
from app.utils import OffsetPaginator


def button_menu(
    *buttons: InlineKeyboardButton, adjust: int = 1
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder([list(buttons)])
    builder.adjust(adjust)
    return builder.as_markup()


def interactive_item_list(
    callback_prefix: str,
    items: Iterable[_BaseModel],
    *,
    adjust: int = 1,
    paginator: OffsetPaginator | None = None,
    extra_buttons: list[InlineKeyboardButton] | None = None,
) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=item.render(),
                callback_data=f"{callback_prefix}:{item.id}",
            )
            for item in items
        ]
    ]

    extra_buttons = extra_buttons or []

    if paginator:
        if paginator.prev_page_offset is not None:
            extra_buttons.append(
                InlineKeyboardButton(
                    text="Предыдущие",
                    callback_data=f"{paginator.callback_prefix}:previous",
                )
            )

        if paginator.next_page_offset is not None:
            extra_buttons.append(
                InlineKeyboardButton(
                    text="Следующие",
                    callback_data=f"{paginator.callback_prefix}:next",
                )
            )

    buttons.append(extra_buttons)

    builder = InlineKeyboardBuilder(buttons)
    builder.adjust(adjust)
    return builder.as_markup()


def create_callback_buttons(
    button_names: dict[str, str],
    callback_prefix: str,
    extra_buttons: list[InlineKeyboardButton] | None = None,
) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=button_name.capitalize(),
                callback_data=f"{callback_prefix}:{callback_suffix.lower()}",
            )
            for button_name, callback_suffix in button_names.items()
        ]
    ]

    if extra_buttons:
        buttons.append(extra_buttons)

    builder = InlineKeyboardBuilder(buttons)
    return builder.as_markup()


class Template:
    """Container type wrapper for args passed to aiogram Message methods.

    Intended to be used in `message.answer` or `callback.message.answer`
    or `message.reply` and such.

    Supports unpacking (`**template`), iterating (`for i,j in template`)
    and indexing (`template[key]`)
    """

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
        **kwargs: Any,
    ):
        self._properties = kwargs
        self._properties.update(text=text, reply_markup=reply_markup)

    def __contains__(self, key: str) -> bool:
        return key in self._properties

    def __getitem__(self, key) -> Any:
        return self._properties.get(key)

    def __iter__(self):
        return iter(self._properties.items())

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._properties})"

    def __setitem__(self, key: str, value: Any) -> None:
        self._properties[key] = value

    def keys(self):
        return self._properties.keys()

    def values(self):
        return self._properties.values()
