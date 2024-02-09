from typing import Literal

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.callback_data import (
    EntryItemActionData,
    ReportTypeCallback,
)
from app.db import models

from .base import (
    interactive_item_list,
)
from .buttons import create_entry, switch_to_main_menu


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


def create_entry_show_budgets(
    budgets: list,
) -> InlineKeyboardBuilder:
    return interactive_item_list(
        budgets, "entry_budget_item", [switch_to_main_menu]
    )


def create_entry_show_categories(
    categories: list[models.Category],
) -> InlineKeyboardBuilder:
    return interactive_item_list(
        categories,
        "entry_category_item",
        [switch_to_main_menu],
    )


def entry_item_list_interactive(entries: list[models.Entry]):
    return interactive_item_list(
        entries,
        "entry_id",
        [create_entry, switch_to_main_menu],
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
    builder.add(switch_to_main_menu)
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
        callback_data=ReportTypeCallback(type=report_type, period="today"),
    )
    builder.button(
        text="Вчера",
        callback_data=ReportTypeCallback(type=report_type, period="yesterday"),
    )
    builder.button(
        text="Эта неделя",
        callback_data=ReportTypeCallback(type=report_type, period="this_week"),
    )
    builder.adjust(1)
    return builder
