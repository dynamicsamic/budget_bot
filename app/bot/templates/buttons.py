from aiogram.types import InlineKeyboardButton

from app.bot import string_constants as sc
from app.bot.filters import (
    CategoryItemActionData,
    CurrencyUpdateData,
    UserSignupData,
)

##############
### COMMON ###
##############

cancel_operation = InlineKeyboardButton(
    text="Отменить действие", callback_data=sc.CANCEL_CALL
)

switch_to_main_menu = InlineKeyboardButton(
    text="🔙 Вернуться в главное меню",
    callback_data=sc.SHOW_MAIN_MENU_CALL,
)


############
### USER ###
############

signup_user = InlineKeyboardButton(
    text="Зарегистрировать аккаунт",
    callback_data=UserSignupData(action="start").pack(),
)

activate_user = InlineKeyboardButton(
    text="Активировать аккаунт", callback_data=sc.ACTIVATE_USER
)

update_user = InlineKeyboardButton(
    text="Изменить данные аккаунта", callback_data=sc.UPDATE_USER
)

update_budget_currency = InlineKeyboardButton(
    text="Изменить валюту",
    callback_data=CurrencyUpdateData(action="start").pack(),
)

delete_user = InlineKeyboardButton(
    text="Удалить аккаунт", callback_data=sc.DELETE_USER
)

show_user_profile = InlineKeyboardButton(
    text="Мой аккаунт", callback_data=sc.SHOW_USER_PROFILE
)


################
### CATEGORY ###
################

create_category = InlineKeyboardButton(
    text="🟢 Создать новую категорию",
    callback_data="create_category",
)


show_categories = InlineKeyboardButton(
    text="🗂️ Мои категории", callback_data="show_categories"
)


def switch_to_update_category(category_id: int):
    callback_data = CategoryItemActionData(
        action="update", category_id=category_id
    )
    return InlineKeyboardButton(
        text="Лучше изменить категорию",
        callback_data=callback_data.pack(),
    )


def confirm_delete_category(category_id: int):
    return InlineKeyboardButton(
        text="Все-таки удалить",
        callback_data=f"{sc.DELETE_CATEGORY}:{category_id}",
    )


#############
### ENTRY ###
#############

entry_menu = InlineKeyboardButton(
    text="💶 Мои транзакции", callback_data="entry_menu"
)

report_menu = InlineKeyboardButton(
    text="📋 Отчеты", callback_data="report_menu"
)

create_entry = InlineKeyboardButton(
    text="🟢 Создать новую транзакцию",
    callback_data="entry_create",
)
