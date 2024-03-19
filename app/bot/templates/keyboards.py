from typing import Iterable, Literal

from aiogram import types
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot import string_constants as sc
from app.bot.filters import (
    CategoryItemActionData,
    EntryItemActionData,
    ReportTypeData,
)
from app.db import models
from app.utils import OffsetPaginator

from . import buttons as btn
from .base import (
    button_menu,
    create_callback_buttons,
    interactive_item_list,
)

####################
# Common Keyboards #
####################
show_main_menu = button_menu(
    btn.show_user_profile,
    btn.show_categories,
    btn.entry_menu,
    btn.report_menu,
)

switch_to_main = button_menu(btn.switch_to_main_menu)
switch_to_main_or_cancel = button_menu(
    btn.switch_to_main_menu, btn.cancel_operation
)


####################
#  User Keyboards  #
####################
signup_menu = button_menu(
    btn.signup_user, btn.cancel_operation, btn.switch_to_main_menu
)

activation_menu = button_menu(
    btn.activate_user, btn.cancel_operation, btn.switch_to_main_menu
)

switch_to_user_profile = button_menu(
    btn.show_user_profile, btn.switch_to_main_menu, btn.cancel_operation
)

user_profile_menu = button_menu(
    btn.update_budget_currency,
    btn.delete_user,
    btn.switch_to_main_menu,
    btn.cancel_operation,
)

confirm_updated_currency_menu = create_callback_buttons(
    button_names={"Принять": "confirm", "Повторить ввод": "reset"},
    callback_prefix=sc.UPDATE_CURRENCY,
    extra_buttons=[btn.switch_to_main_menu, btn.cancel_operation],
)

choose_signup_type = create_callback_buttons(
    button_names={
        "стандартная регистрация": "basic",
        "продвинутая регистрация": "advanced",
    },
    callback_prefix=sc.SIGNUP_USER,
    extra_buttons=[btn.cancel_operation, btn.switch_to_main_menu],
)

get_budget_currency_menu = create_callback_buttons(
    button_names={"установить валюту": "get_currency"},
    callback_prefix=sc.SIGNUP_USER,
    extra_buttons=[btn.cancel_operation, btn.switch_to_main_menu],
)

finish_advanced_signup = create_callback_buttons(
    button_names={
        "завершить": "basic",
    },
    callback_prefix=sc.SIGNUP_USER,
    extra_buttons=[btn.cancel_operation, btn.switch_to_main_menu],
)


######################
# Category Keyboards #
######################
category_type_menu = create_callback_buttons(
    button_names={"Доходы": "income", "Расходы": "expenses"},
    callback_prefix=sc.SELECT_CATEGORY_TYPE,
    extra_buttons=[btn.cancel_operation, btn.switch_to_main_menu],
)


category_update_options = create_callback_buttons(
    button_names={
        "название": "name",
        "тип": "type",
        "завершить": "finish",
    },
    callback_prefix=sc.UPDATE_CATEGORY,
)


show_categories_menu = button_menu(
    btn.show_categories, btn.switch_to_main_menu
)
create_category_menu = button_menu(
    btn.create_category, btn.cancel_operation, btn.switch_to_main_menu
)


def delete_category_warning(category_id: int) -> ReplyKeyboardMarkup:
    return button_menu(
        btn.switch_to_update_category(category_id),
        btn.confirm_delete_category(category_id),
        btn.cancel_operation,
    )


def categories_paginated_list(
    categories: Iterable[models.Category], paginator: OffsetPaginator
) -> ReplyKeyboardMarkup:
    return interactive_item_list(
        sc.CATEGORY_ID,
        categories,
        paginator=paginator,
        extra_buttons=[btn.create_category, btn.switch_to_main_menu],
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


###################
# Entry Keyboards #
###################
def entry_item_choose_action(entry_id: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Изменить",
        callback_data=EntryItemActionData(
            entry_id=entry_id,
            action="update",
        ),
    )
    builder.button(
        text="Удалить",
        callback_data=EntryItemActionData(entry_id=entry_id, action="delete"),
    )
    builder.adjust(1)
    return builder.as_markup()


def entry_item_choose_action2():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Изменить",
        callback_data="entry_item_action_update",
    )
    builder.button(
        text="Удалить",
        callback_data="entry_item_action_delete",
    )
    builder.adjust(1)
    return builder.as_markup()


def show_entry_categories(
    categories: Iterable[models.Category], paginator: OffsetPaginator
) -> ReplyKeyboardMarkup:
    return interactive_item_list(
        sc.ENTRY_CATEGORY_ID,
        categories,
        adjust=3,
        paginator=paginator,
        extra_buttons=[btn.switch_to_main_menu, btn.cancel_operation],
    )


def create_entry_show_categories(
    categories: list[models.Category],
) -> InlineKeyboardBuilder:
    return interactive_item_list(
        "entry_category_item",
        categories,
        extra_buttons=[btn.switch_to_main_menu],
    )


def entry_item_list_interactive(entries: list[models.Entry]):
    return interactive_item_list(
        "entry_id",
        entries,
        extra_buttons=[btn.create_entry, btn.switch_to_main_menu],
    )


def entry_confirm_delete(id_: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Да (подтвердить удаление)",
        callback_data=f"entry_id_{id_}",
    )
    builder.button(
        text="Нет (отменить удаление)",
        callback_data="None",
    )
    builder.add(btn.switch_to_main_menu)
    builder.adjust(1)
    return builder.as_markup()


cmd_report_kb = InlineKeyboardBuilder(
    [
        [
            types.InlineKeyboardButton(
                text="Доходы", callback_data="check_income"
            ),
            types.InlineKeyboardButton(
                text="Расходы", callback_data="check_expenses"
            ),
            types.InlineKeyboardButton(
                text="Разница доход-расход", callback_data="check_balance"
            ),
        ]
    ]
)
cmd_report_kb.adjust(1)


def choose_period_kb(
    report_type: Literal["income", "expenses", "balance"]
) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Сегодня",
        callback_data=ReportTypeData(type=report_type, period="today"),
    )
    builder.button(
        text="Вчера",
        callback_data=ReportTypeData(type=report_type, period="yesterday"),
    )
    builder.button(
        text="Эта неделя",
        callback_data=ReportTypeData(type=report_type, period="this_week"),
    )
    builder.adjust(1)
    return builder
