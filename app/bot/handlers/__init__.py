from aiogram import Dispatcher
from aiogram.filters.command import Command

from .commands import cmd_get_report, cmd_start


def register_command_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_get_report, Command("report"))
