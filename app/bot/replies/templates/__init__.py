from typing import Any

from aiogram.types import (
    ForceReply,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)


class Template:
    """Container type wrapper for args passed to aiogram Message methods.

    Intended to be used in `message.answer` or `callback.message.answer`
    or `message.reply` and such.

    Supports unpacking (`**template`), iterating (`for i,j in template`)
    and indexing (`template[key]`)
    """

    def __init__(
        self,
        text: str,
        reply_markup: (
            InlineKeyboardMarkup
            | ReplyKeyboardMarkup
            | ReplyKeyboardRemove
            | ForceReply
            | None
        ) = None,
        **kwargs: Any,
    ):
        self._properties = kwargs
        self._properties.update(text=text, reply_markup=reply_markup)

    def __contains__(self, key: str) -> bool:
        return key in self._properties

    def __getitem__(self, key) -> Any:
        return self._properties.get(key)

    def __iter__(self):
        return iter(self._properties.items())

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._properties})"

    def __setitem__(self, key: str, value: Any) -> None:
        self._properties[key] = value

    def keys(self):
        return self._properties.keys()
