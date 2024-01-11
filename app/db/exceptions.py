from typing import Any, Tuple

from aiogram.types import ReplyKeyboardMarkup
from sqlalchemy.exc import SQLAlchemyError

from app.bot.keyboards import handler_error_markup

from .custom_types import _BaseModel


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


class ImproperlyConfigured(BudgetBotDataBaseException):
    pass


class ModelInstanceNotFound(BudgetBotDataBaseException):
    pass


class EmptyModelKwargs(BudgetBotDataBaseException):
    pass


class InvalidModelArgValue(BudgetBotDataBaseException):
    def __init__(self, *args, model: _BaseModel, invalid_arg: Any) -> None:
        super().__init__(*args)
        self.model = model
        self.invalid_arg = invalid_arg

    def __repr__(self) -> str:
        return (
            "Недопустимый аргумент для модели: "
            f"{self.model.get_tablename()}: `{self.invalid_arg}`."
        )


class InvalidModelArgType(BudgetBotDataBaseException):
    def __init__(
        self,
        *args,
        model: _BaseModel,
        arg_name: str,
        expected_type: Any,
        invalid_type: Any,
    ) -> None:
        super().__init__(*args)
        self.model = model
        self.arg_name = arg_name
        self.expected_type = expected_type
        self.invalid_type = invalid_type

    def __repr__(self) -> str:
        return (
            f"Недопустимый тип для аргумента `{self.arg_name}` модели "
            f"{self.model.get_tablename()}: "
            f"получен {self.invalid_type} вместо {self.expected_type}."
        )


def build_error_message(
    user_tg_id: int,
    error: Exception,
    intro: str,
    afterword: str,
) -> Tuple[str, ReplyKeyboardMarkup | None]:
    msg = "{intro}: {err_description}. {afterword}"
    reply_markup = None

    if isinstance(error, InvalidModelArgType):
        err_description = "Передан неверный тип данных"
    elif isinstance(error, InvalidModelArgValue):
        err_description = "Название атрибута содержит ошибку"
    elif isinstance(error, SQLAlchemyError):
        err_description = (
            "Ошибка работы с базой данных. Возможно, вы пытаетесь"
            "внести данные, которые уже есть в базе, или вводимые "
            "данные имеют несовместимый формат"
        )
    else:
        err_description = (
            "Непревиденная ошибка. Отчет об ошибке был направлен в поддержку"
        )
        afterword = "Попробуйте воспользоваться ботом позже."
        reply_markup = handler_error_markup(user_tg_id, error)

    msg.format(
        intro=intro, err_description=err_description, afterword=afterword
    )
    return (
        msg,
        reply_markup,
    )
