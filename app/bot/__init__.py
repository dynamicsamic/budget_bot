from aiogram import Bot, Dispatcher

from config import config

bot = Bot(token=config.bot_token.get_secret_value())
dp = Dispatcher()
