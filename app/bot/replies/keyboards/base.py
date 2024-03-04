from typing import Iterable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
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
