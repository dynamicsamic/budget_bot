class BudgetBotDataBaseException(Exception):
    pass


class InvalidOrderByValue(BudgetBotDataBaseException):
    pass


class InvalidDBSession(BudgetBotDataBaseException):
    pass


class InvalidFilter(BudgetBotDataBaseException):
    pass


class InvalidDateField(BudgetBotDataBaseException):
    pass


class InvalidSumField(BudgetBotDataBaseException):
    pass


class InvalidCashflowield(BudgetBotDataBaseException):
    pass


class ModelInstanceCreateError(BudgetBotDataBaseException):
    pass
