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
