from typing import Literal

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.handlers.callback_data import (
    BudgetItemActionData,
    ReportTypeCallback,
)

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
            types.InlineKeyboardButton(
                text="💰 Мои бюджеты", callback_data="budget_menu"
            ),
            types.InlineKeyboardButton(
                text="🗂️ Мои категории", callback_data="category_menu"
            ),
            types.InlineKeyboardButton(
                text="💶 Мои транзакции", callback_data="entry_menu"
            ),
            types.InlineKeyboardButton(
                text="📋 Отчеты", callback_data="report_menu"
            ),
        ]
    ]
)
main_menu.adjust(1)

budget_menu = InlineKeyboardBuilder(
    [
        [
            types.InlineKeyboardButton(
                text="📂 Список бюджетов", callback_data="budget_list"
            ),
            types.InlineKeyboardButton(
                text="🟢 Добавить бюджет", callback_data="budget_create"
            ),
            types.InlineKeyboardButton(
                text="🔴 Удалить бюджет", callback_data="budget_delete"
            ),
            types.InlineKeyboardButton(
                text="🔙 Вернуться в главное меню",
                callback_data="main_menu_return",
            ),
        ]
    ]
)
budget_menu.adjust(1)


def budget_item_list_interactive(budgets: list):
    kb = InlineKeyboardBuilder(
        [
            [
                types.InlineKeyboardButton(
                    text=f"{budget.currency}, {len(budget.entries)} операций",
                    callback_data=f"budget_item_{budget.id}",
                )
                for budget in budgets
            ]
        ]
    )
    kb.button(text="🟢 Создать новый бюджет", callback_data="budget_create")
    kb.adjust(1)
    return kb.as_markup()


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
