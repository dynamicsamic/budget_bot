from typing import Iterable

from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.callback_data import (
    CategoryItemActionData,
)
from app.bot.handlers import shared
from app.db import models

from .base import (
    button_menu,
    create_callback_buttons,
    interactive_item_list,
    paginated_item_list,
)
from .buttons import (
    cancel_operation,
    confirm_delete_category,
    create_category,
    show_categories,
    switch_to_main_menu,
    switch_to_update_category,
)

category_type_menu = create_callback_buttons(
    button_names={"Доходы": "income", "Расходы": "expenses"},
    callback_prefix=shared.select_category_type,
    extra_buttons=[cancel_operation, switch_to_main_menu],
)


category_update_options = create_callback_buttons(
    button_names={
        "название": "name",
        "тип": "type",
        "завершить": "finish",
    },
    callback_prefix=shared.update_category,
)


show_categories_menu = button_menu(show_categories, switch_to_main_menu)
create_category_menu = button_menu(
    create_category, cancel_operation, switch_to_main_menu
)


def delete_category_warning(category_id: int) -> ReplyKeyboardMarkup:
    return button_menu(
        switch_to_update_category(category_id),
        confirm_delete_category(category_id),
        cancel_operation,
    )


def categories_paginated_list(
    categories: Iterable[models.Category], paginator
):
    return paginated_item_list(
        categories,
        shared.category_id,
        paginator,
        [create_category, switch_to_main_menu],
    )


def categories_interactive_list(categories: Iterable[models.Category]):
    return interactive_item_list(
        categories,
        "category_item",
        [create_category, switch_to_main_menu],
    )


def category_choose_update_delete(category_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Изменить",
        callback_data=CategoryItemActionData(
            action="update",
            category_id=category_id,
        ),
    )
    builder.button(
        text="Удалить",
        callback_data=CategoryItemActionData(
            action="delete", category_id=category_id
        ),
    )
    builder.adjust(1)
    return builder.as_markup()
