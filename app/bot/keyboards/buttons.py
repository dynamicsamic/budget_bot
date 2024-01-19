from aiogram.types import InlineKeyboardButton

signup_user = InlineKeyboardButton(
    text="Зарегистрировать аккаунт", callback_data="signup_user"
)

activate_user = InlineKeyboardButton(
    text="Активировать аккаунт", callback_data="activate_user"
)

delete_user = InlineKeyboardButton(
    text="Удалить аккаунт", callback_data="delete_user"
)

cancel_operation = InlineKeyboardButton(
    text="Отменить действие", callback_data="cancel"
)

main_menu = InlineKeyboardButton(
    text="🔙 Вернуться в главное меню",
    callback_data="main_menu_return",
)

create_new_category = InlineKeyboardButton(
    text="🟢 Создать новую категорию",
    callback_data="create_category",
)

create_new_entry = InlineKeyboardButton(
    text="🟢 Создать новую транзакцию",
    callback_data="entry_create",
)

user_profile = InlineKeyboardButton(
    text="Мой аккаунт", callback_data="show_user_profile"
)

show_categories = InlineKeyboardButton(
    text="🗂️ Мои категории", callback_data="show_categories"
)

entry_menu = InlineKeyboardButton(
    text="💶 Мои транзакции", callback_data="entry_menu"
)

report_menu = InlineKeyboardButton(
    text="📋 Отчеты", callback_data="report_menu"
)
