from typing import Callable, Literal

from aiogram import types
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.callback_data import (
    BudgetItemActionData,
    CategoryItemActionData,
    EntryItemActionData,
    ReportTypeCallback,
)
from app.bot.render import (
    render_budget_item,
    render_category_item,
    render_entry_item,
)
from app.db import models
from app.db.base import AbstractBaseModel

from . import buttons

signup_to_proceed = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [
            types.InlineKeyboardButton(
                text="Зарегистрироваться в один клик", callback_data="signup"
            )
        ]
    ]
)

main_menu = InlineKeyboardBuilder(
    [
        [
            buttons.budget_menu,
            buttons.category_menu,
            buttons.entry_menu,
            buttons.report_menu,
        ]
    ]
)
main_menu.adjust(1)


def interactive_item_list(
    items: list[AbstractBaseModel],
    render_func: Callable[..., str],
    callback_prefix: str,
    extra_buttons: list[InlineKeyboardButton] = None,
) -> InlineKeyboardBuilder:
    buttons = [
        [
            types.InlineKeyboardButton(
                text=render_func(item),
                callback_data=f"{callback_prefix}_{item.id}",
            )
            for item in items
        ]
    ]
    if extra_buttons:
        buttons.append(extra_buttons)

    builder = InlineKeyboardBuilder(buttons)
    builder.adjust(1)
    return builder.as_markup()


def budget_item_list_interactive(budgets: list[models.EntryCategory]):
    return interactive_item_list(
        budgets,
        render_budget_item,
        "budget_item",
        [buttons.create_new_budget, buttons.main_menu],
    )


def category_item_list_interactive(categories: list[models.EntryCategory]):
    return interactive_item_list(
        categories,
        render_category_item,
        "category_item",
        [buttons.create_new_category, buttons.main_menu],
    )


def budget_item_choose_action(budget_id: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Изменить",
        callback_data=BudgetItemActionData(
            budget_id=budget_id,
            action="update",
        ),
    )
    builder.button(
        text="Удалить",
        callback_data=BudgetItemActionData(
            budget_id=budget_id, action="delete"
        ),
    )
    builder.adjust(1)
    return builder.as_markup()


def choose_category_type():
    builder = InlineKeyboardBuilder()
    builder.button(text="Доходы", callback_data="choose_entry_category_income")
    builder.button(
        text="Расходы", callback_data="choose_entry_category_expenses"
    )
    builder.adjust(1)
    return builder.as_markup()


def category_item_choose_action(category_id: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Изменить",
        callback_data=CategoryItemActionData(
            category_id=category_id,
            action="update",
        ),
    )
    builder.button(
        text="Удалить",
        callback_data=CategoryItemActionData(
            category_id=category_id, action="delete"
        ),
    )
    builder.adjust(1)
    return builder.as_markup()


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


def show_categories_and_main_menu():
    builder = InlineKeyboardBuilder(
        [[buttons.category_menu, buttons.main_menu]]
    )
    builder.adjust(1)
    return builder.as_markup()


def create_entry_show_budgets(
    budgets: list[models.Budget],
) -> InlineKeyboardBuilder:
    return interactive_item_list(
        budgets, render_budget_item, "entry_budget_item", [buttons.main_menu]
    )


def create_entry_show_categories(
    categories: list[models.EntryCategory],
) -> InlineKeyboardBuilder:
    return interactive_item_list(
        categories,
        render_category_item,
        "entry_category_item",
        [buttons.main_menu],
    )


def entry_item_list_interactive(entries: list[models.Entry]):
    return interactive_item_list(
        entries,
        render_entry_item,
        "entry_id",
        [buttons.create_new_entry, buttons.main_menu],
    )


def confirm_delete(id_: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Да (подтвердить удаление)",
        callback_data=f"entry_id_{id_}",
    )
    builder.button(
        text="Нет (отменить удаление)",
        callback_data="None",
    )
    builder.add(buttons.main_menu)
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
