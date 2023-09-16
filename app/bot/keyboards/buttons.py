from aiogram.types import InlineKeyboardButton

main_menu = InlineKeyboardButton(
    text="🔙 Вернуться в главное меню",
    callback_data="main_menu_return",
)

create_new_category = InlineKeyboardButton(
    text="🟢 Создать новую категорию",
    callback_data="category_create",
)

create_new_budget = InlineKeyboardButton(
    text="🟢 Создать новый бюджет",
    callback_data="budget_create",
)

budget_menu = InlineKeyboardButton(
    text="💰 Мои бюджеты", callback_data="budget_menu"
)

category_menu = InlineKeyboardButton(
    text="🗂️ Мои категории", callback_data="category_menu"
)

entry_menu = InlineKeyboardButton(
    text="💶 Мои транзакции", callback_data="entry_menu"
)

report_menu = InlineKeyboardButton(
    text="📋 Отчеты", callback_data="report_menu"
)
