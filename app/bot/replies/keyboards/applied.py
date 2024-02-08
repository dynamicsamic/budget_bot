from typing import Iterable, Literal

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.callback_data import (
    CategoryItemActionData,
    EntryItemActionData,
    ReportTypeCallback,
)
from app.bot.handlers import shared
from app.bot.replies import buttons
from app.db import models

from .base import (
    button_menu,
    create_callback_buttons,
    interactive_item_list,
    paginated_item_list,
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


main_menu = button_menu(
    buttons.user_profile,
    buttons.show_categories,
    buttons.entry_menu,
    buttons.report_menu,
)


category_update_options = create_callback_buttons(
    button_names={
        "название": "name",
        "тип": "type",
        "завершить": "finish",
    },
    callback_prefix=shared.update_category,
)


def paginated_category_item_list(
    categories: Iterable[models.Category], paginator
):
    return paginated_item_list(
        categories,
        shared.category_id,
        paginator,
        [buttons.create_new_category, buttons.main_menu],
    )


def category_item_list_interactive(categories: Iterable[models.Category]):
    return interactive_item_list(
        categories,
        "category_item",
        [buttons.create_new_category, buttons.main_menu],
    )


def category_item_choose_action(category_id: int):
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
        [[buttons.show_categories, buttons.main_menu]]
    )
    builder.adjust(1)
    return builder.as_markup()


def create_entry_show_budgets(
    budgets: list,
) -> InlineKeyboardBuilder:
    return interactive_item_list(
        budgets, "entry_budget_item", [buttons.main_menu]
    )


def create_entry_show_categories(
    categories: list[models.Category],
) -> InlineKeyboardBuilder:
    return interactive_item_list(
        categories,
        "entry_category_item",
        [buttons.main_menu],
    )


def entry_item_list_interactive(entries: list[models.Entry]):
    return interactive_item_list(
        entries,
        "entry_id",
        [buttons.create_new_entry, buttons.main_menu],
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
