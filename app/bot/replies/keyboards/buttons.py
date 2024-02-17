from aiogram.types import InlineKeyboardButton

from app.bot.callback_data import (
    CategoryItemActionData,
    SignupUserCallbackData,
)
from app.bot.handlers import shared

##############
### COMMON ###
##############

cancel_operation = InlineKeyboardButton(
    text="Отменить действие", callback_data=shared.cancel_callback
)

switch_to_main_menu = InlineKeyboardButton(
    text="🔙 Вернуться в главное меню",
    callback_data=shared.show_main_menu_callback,
)


############
### USER ###
############

signup_user = InlineKeyboardButton(
    text="Зарегистрировать аккаунт",
    callback_data=SignupUserCallbackData(action="start").pack(),
)

activate_user = InlineKeyboardButton(
    text="Активировать аккаунт", callback_data=shared.activate_user
)

update_user = InlineKeyboardButton(
    text="Изменить данные аккаунта", callback_data=shared.update_user
)

delete_user = InlineKeyboardButton(
    text="Удалить аккаунт", callback_data=shared.delete_user
)

show_user_profile = InlineKeyboardButton(
    text="Мой аккаунт", callback_data="show_user_profile"
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
        callback_data=f"{shared.delete_category}:{category_id}",
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
