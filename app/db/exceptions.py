class BudgetBotDataBaseException(Exception):
    pass


class InvalidOrderByValue(BudgetBotDataBaseException):
    pass


class InvalidFilter(BudgetBotDataBaseException):
    pass


class InvalidDateField(BudgetBotDataBaseException):
    pass


class InvalidSumField(BudgetBotDataBaseException):
    pass
