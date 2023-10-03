from aiogram.fsm.state import State, StatesGroup


class BudgetCreatetState(StatesGroup):
    currency = State()


class BudgetUpdateState(StatesGroup):
    currency = State()


class CategoryCreateState(StatesGroup):
    name = State()
    type = State()


class CategoryUpdateState(StatesGroup):
    name = State()


class EntryCreateState(StatesGroup):
    budget = State()
    category = State()
    sum = State()
    transcation_date = State()
    description = State()


class EntryList(StatesGroup):
    budgets = State()
