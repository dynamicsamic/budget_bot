import asyncio
import logging

from app.bot import bot, dp
from app.bot.handlers import register_command_handlers

logging.basicConfig(level=logging.INFO)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    register_command_handlers(dp)
    asyncio.run(main())
