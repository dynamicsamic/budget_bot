from aiogram import types


async def cmd_start(message: types.Message):
    await message.answer("Hello user!")
