from aiogram.fsm.state import State, StatesGroup


class BudgetState(StatesGroup):
    currency = State()
