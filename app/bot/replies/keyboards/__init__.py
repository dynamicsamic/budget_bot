from typing import Iterable, Literal

from aiogram import types
from aiogram.fsm.state import StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.callback_data import (
    CategoryItemActionData,
    EntryItemActionData,
    ReportTypeCallback,
)
from app.custom_types import _BaseModel
from app.db import models

from .. import buttons

signup_to_proceed = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [
            types.InlineKeyboardButton(
                text="Зарегистрироваться в один клик", callback_data="signup"
            )
        ]
    ]
)


def button_menu(*buttons, adjust: int = 1) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder([list(buttons)])
    builder.adjust(adjust)
    return builder.as_markup()


main_menu = InlineKeyboardBuilder(
    [
        [
            buttons.user_profile,
            buttons.show_categories,
            buttons.entry_menu,
            buttons.report_menu,
        ]
    ]
)
main_menu.adjust(1)


def interactive_item_list(
    items: Iterable[_BaseModel],
    callback_prefix: str,
    extra_buttons: list[InlineKeyboardButton] = None,
) -> InlineKeyboardMarkup:
    buttons = [
        [
            types.InlineKeyboardButton(
                text=item.render(),
                callback_data=f"{callback_prefix}:{item.id}",
            )
            for item in items
        ]
    ]
    if extra_buttons:
        buttons.append(extra_buttons)

    builder = InlineKeyboardBuilder(buttons)
    builder.adjust(1)
    return builder.as_markup()


def paginated_item_list(
    items: Iterable[_BaseModel],
    callback_prefix: str,
    paginator,
    extra_buttons: list[InlineKeyboardButton] = None,
) -> InlineKeyboardMarkup:
    buttons = [
        [
            types.InlineKeyboardButton(
                text=item.render(),
                callback_data=f"{callback_prefix}:{item.id}",
            )
            for item in items
        ]
    ]
    extra_buttons = extra_buttons or []

    if paginator.prev_page_offset is not None:
        extra_buttons.append(
            types.InlineKeyboardButton(
                text="Предыдущие",
                callback_data=f"{paginator.callback_prefix}:previous",
            )
        )

    if paginator.next_page_offset is not None:
        extra_buttons.append(
            types.InlineKeyboardButton(
                text="Следующие",
                callback_data=f"{paginator.callback_prefix}:next",
            )
        )

    buttons.append(extra_buttons)

    builder = InlineKeyboardBuilder(buttons)
    builder.adjust(1)
    return builder.as_markup()


def create_callback_buttons(
    button_names: dict[str, str], callback_prefix: str
):
    builder = InlineKeyboardBuilder()

    for button_name, callback_suffix in button_names.items():
        builder.button(
            text=button_name.capitalize(),
            callback_data=f"{callback_prefix}:{callback_suffix.lower()}",
        )

    return builder.as_markup()


category_update_options = create_callback_buttons(
    button_names={
        "название": "name",
        "тип": "type",
        "завершить": "finish",
    },
    callback_prefix="update_category",
)


def states_group_callback_buttons(
    states_group: StatesGroup, callback_prefix: str
):
    builder = InlineKeyboardBuilder()
    for state in states_group.__state_names__:
        _, state_name = state.split(":")
        if not state_name.startswith("_"):
            button_name, callback_suffix = state_name.split("@")
            builder.button(
                text=button_name.capitalize(),
                callback_data=f"{callback_prefix}_{callback_suffix.lower()}",
            )
    return builder.as_markup()


def paginated_category_item_list(
    categories: Iterable[models.Category], paginator
):
    return paginated_item_list(
        categories,
        "category_id",
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
