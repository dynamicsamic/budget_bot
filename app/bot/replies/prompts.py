from app.custom_types import _BaseModel
from app.db.models import User

category_name_description = (
    "Название категории не должно быть короче 4-х или длинее 30-ти символов."
    "Можно использовать буквы и цифры, пробелы, знак нижнего подчеркивания, "
    "запятые и круглые скобки."
)

create_failure_contact_support = (
    "Что-то пошло не так при создании {instance_name}. Обратитесь в поддержку."
)

category_choose_action = "Кликните на нужную категорию, чтобы выбрать действие"

serverside_error_response = (
    "Непредвиденная ошибка на стороне бота. Уже работаем над ней. "
    "Попробуйте повторить операцию через пару часов."
)
deleted_object = (
    "Объект {obj_name} был успешн удален. "
    "Вы можете его восстановить, нажав на кнопку Отменить удаление."
)
confirm_category_deleted = (
    "Категория и была успешно удалена вместе с транзакциями."
)


def show_delete_category_warning(category_name: str, entry_count: int) -> str:
    return (
        f"Внимание! Количество транзакций в категории {category_name} "
        f"составляет: {entry_count}. При удалении категории все "
        "транзакции будут удалены. Если вы хотите сохранить транзакции, "
        "более подходящим решением будует поменять название или тип категории"
    )


update_category_invite_user = (
    "Желаете изменить категорию?"
    "Выберите параметр, который необходимо изменить."
)

update_category_confirm_new_name = (
    "Вы поменяли название категории на `{category_name}`."
    "Вы можете изменить остальные параметры категории "
    "или завершить редактирование."
)

update_category_confirm_new_type = (
    "Вы поменяли тип категории на `{category_type}`."
    "Вы можете изменить остальные параметры категории "
    "или завершить редактирование."
)


def show_update_summary(obj: _BaseModel) -> str:
    return (
        f"Редактирование объекта {obj._public_name} завершено. "
        f"Проверьте внесенные изменения: {obj.render()}"
    )


update_without_changes = "Обновление завершено без изменений"

budget_currency_description = (
    "Наименование валюты должно содержать от 3-х до 10-ти букв "
    "(в любом регистре). Цифры и иные символы не допускаются.\n"
    "Отдавайте предпочтение общепринятым сокращениям, например RUB или USD."
)
invalid_budget_currency_description = (
    "Неверный формат обозначения валюты!\n" f"{budget_currency_description}"
)

choose_signup_type = (
    "Добро пожаловать в меню регистрации. "
    "Нажмите на кнопку стандартной регистрации, чтобы "
    "зарегистрировать аккаунт со станадартными настройками. "
    "Выберите продвинутую регистрацию, если хотите изменить "
    "стандартные настройки."
)

advanced_signup_description = (
    "Вы выбрали продвинутую регистрацию. "
    "Чтобы настроить Ваш аккаунт, следуйте инструкциям."
)

choose_budget_currency = (
    "Пожалуйста, выберите валюту бюджета."
    "Для всех пользователей установлена валюта по умолчанию - RUB\n"
    "Нажмите кнопку `Принять` для завершения регистрации."
    "Нажмите кнопку `Изменить`, если желаете выбрать другую валюту."
)

signup_active_user = (
    "Ваш аккаунт активен, дополнительных действий не требуется. "
    "Вы можете продложить работу с ботом в главном меню."
)

signup_inactive_user = (
    "Ранее Вы уже пользовались Бюджетным ботом, "
    "но решили перестать им пользоваться."
    "Вы можете продолжить работу со своими бюджетами, "
    "нажав кнопку активации ниже."
)


def signup_user_show_currency_and_finish(budget_currency: str) -> str:
    return (
        f"Валюта Вашего бюджета - `{budget_currency}`."
        "Завершите регистрацию, нажав на кнопку Завершить."
    )


def user_signup_success(user: User) -> str:
    return (
        "Поздравляем! Вы успешно зарегистрированы в системе.\n"
        f"Ваши данные: {user.render()}"
        "Вы можете продложить работу с ботом в главном меню."
    )


user_profile_description = (
    "Меню управления профилем. "
    "Со временем здесь могут появиться новые функции"
)

user_activation_success = (
    "Ваш аккаунт снова активен.\n"
    "Вы можете продложить работу с ботом в главном меню."
)

user_delete_success = (
    "Ваш аккаунт успешно удален. Ваши данные будут доступны "
    "следующие 10 дней. Если вы измените свое решение, то "
    "сможете восстановить свой аккаунт в течение этого времени,"
    " воспользовавшись копкой ниже. Да прибудет с Вами сила."
)

start_message_anonymous = (
    "Вас приветсвует Бюджетный Менеджер!"
    "Для продолжения работы, создайте аккаунт. "
)

start_message_inactive = (
    "Вас приветсвует Бюджетный Менеджер!"
    "Чтобы возобновить работу, нажмите на кнопку `Активировать`."
)

start_message_active = (
    "С возвращением в Бюджетный Менеджер! Продолжите работу в главном меню."
)

cancel_operation_note = "Действие отменено"
main_menu_note = "Основное меню"
