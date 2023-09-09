from aiogram.fsm.state import State, StatesGroup


class BudgetCreatetState(StatesGroup):
    currency = State()


class BudgetDeleteState(StatesGroup):
    id = State()


class BudgetUpdateState(StatesGroup):
    currency = State()
