from aiogram.fsm.state import State, StatesGroup


class CreateUser(StatesGroup):
    choose_signup_type = State()
    advanced_signup = State()
    get_budget_currency = State()


class UpdateUser(StatesGroup):
    budget_currency = State()


class CreateCategory(StatesGroup):
    set_name = State()
    set_type = State()


class ShowCategories(StatesGroup):
    show_many = State()
    show_one = State()


class UpdateCategory(StatesGroup):
    choose_attribute = State()
    update_name = State()
    confirm_update_name = State()
    update_type = State()
    confirm_update_type = State()
    finish = State()


class CreateEntry(StatesGroup):
    budget = State()
    category = State()
    sum = State()
    transcation_date = State()
    description = State()


class EntryList(StatesGroup):
    budgets = State()
    entry_id = State()
    action = State()
    confirm_delete = State()


class PreProcessEntry(StatesGroup):
    choose_budget = State()
    choose_category = State()
    choose_entry = State()
    choose_action = State()


class DeleteEntry(StatesGroup):
    confirm = State()
