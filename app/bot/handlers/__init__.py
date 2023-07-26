from aiogram import Dispatcher
from aiogram.filters.command import Command

from .budget import cmd_get_report
from .common import cmd_start


def register_common_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command("start"))


def register_budget_handlers(dp: Dispatcher):
    dp.message.register(cmd_get_report, Command("report"))
