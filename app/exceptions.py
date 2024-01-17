from typing import Any, Tuple

from aiogram.types import ReplyKeyboardMarkup
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import MappedColumn

from app.bot.keyboards import handler_error_markup
from app.custom_types import _BaseModel


class BudgetBotException(Exception):
    pass


class DataBaseException(BudgetBotException):
    pass


class BotException(BudgetBotException):
    pass


class UnknownDataBaseException(DataBaseException):
    pass


class RepositoryValidationError(DataBaseException):
    pass


class ModelInstanceNotFound(DataBaseException):
    pass


class ModelInstanceDuplicateAttempt(DataBaseException):
    def __init__(
        self,
        *args,
        user_tg_id: int,
        model_name: str,
        duplicate_arg_name: str,
        duplicate_arg_value: Any,
    ) -> None:
        super().__init__(*args)
        self.user_tg_id = user_tg_id
        self.model_name = model_name
        self.duplicate_arg_name = duplicate_arg_name
        self.duplicate_arg_value = duplicate_arg_value

    @property
    def error_message(self) -> str:
        return (
            f"Объект {self.model_name} с полем {self.duplicate_arg_name} "
            f"и значением {self.duplicate_arg_value} уже существует."
        )

    def __str__(self) -> str:
        return self.error_message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.error_message})"


class EmptyModelKwargs(DataBaseException):
    pass


class InvalidModelAttribute(DataBaseException):
    def __init__(self, *args, model: _BaseModel, invalid_attr: str) -> None:
        super().__init__(*args)
        self.model = model
        self.invalid_attr = invalid_attr

    def __str__(self) -> str:
        return (
            f"У объекта {self.model._public_name} "
            f"отсутствует атрибут {self.invalid_attr}"
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(Model {self.model.get_tablename()} "
            f"does not have `{self.invalid_attr}` attribute.)"
        )


class InvalidModelArgType(DataBaseException):
    def __init__(
        self,
        *args,
        model: _BaseModel,
        field: MappedColumn,
        expected_type: Any,
        invalid_type: Any,
    ) -> None:
        super().__init__(*args)
        self.model = model
        self.field = field
        self.expected_type = expected_type
        self.invalid_type = invalid_type

    def __str__(self) -> str:
        return (
            f"В атрибут {self.field.doc} объекта {self.model._public_name} "
            "передан неверный тип значения."
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(Model {self.model.get_tablename()} "
            f"attribute `{self.field.name}` recieved {self.invalid_type} "
            f"instead of {self.expected_type}.)"
        )


class InvalidCallbackData(BotException):
    pass


class InvalidCategoryName(BotException):
    pass


def build_error_message(
    user_tg_id: int,
    error: Exception,
    intro: str,
    afterword: str,
) -> Tuple[str, ReplyKeyboardMarkup | None]:
    reply_markup = None

    if isinstance(error, InvalidModelArgType):
        err_description = "Передан неверный тип данных"
    elif isinstance(error, InvalidModelAttribute):
        err_description = "Название атрибута содержит ошибку"
    elif isinstance(error, SQLAlchemyError):
        err_description = (
            "Ошибка работы с базой данных. Возможно, вы пытаетесь"
            "внести данные, которые уже есть в базе, или вводимые "
            "данные имеют несовместимый формат"
        )
    else:
        err_description = (
            "Непревиденная ошибка. Нажмите на кнопку `Сообщить о проблеме`, "
            "чтобы направить отчет в поддержку."
        )
        afterword = "Попробуйте воспользоваться ботом позже."
        reply_markup = handler_error_markup(user_tg_id, repr(error))

    return (
        f"{intro}: {err_description}. {afterword}",
        reply_markup,
    )
