class BudgetBotDataBaseException(Exception):
    pass


class InvalidOrderByValue(BudgetBotDataBaseException):
    pass


class InvalidFilter(BudgetBotDataBaseException):
    pass


class InvalidDatefield(BudgetBotDataBaseException):
    pass
