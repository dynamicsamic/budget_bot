from aiogram.fsm.state import State, StatesGroup


class BudgetCreateState(StatesGroup):
    set_name = State()
    set_currency = State()


class BudgetUpdateState(StatesGroup):
    choose_attribute = State()
    update_name = State()
    confirm_update_name = State()
    update_currency = State()
    confirm_update_currency = State()
    finish = State()


class BudgetShowState(StatesGroup):
    show_budgets = State()


class CategoryCreateState(StatesGroup):
    name = State()
    type = State()


class CategoryUpdateState(StatesGroup):
    name = State()


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
