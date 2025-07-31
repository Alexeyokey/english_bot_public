from aiogram import Router, F, types
from aiogram.filters.command import Command
import asyncio
from aiogram.fsm.context import FSMContext
from db.database import User
from Constants import HELP_MESSAGE

router = Router()

@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    user_in = message.from_user.id
    user = User.get_or_none(User.telegram_id == user_in)
    if user:
        await message.answer(f"Здравствуйте {message.from_user.full_name}!\nРады видеть вас снова!\nНажмите /help, чтобы вспомнить, что я могу", reply_markup=types.ReplyKeyboardRemove())
    else:
        user = User.create(name=message.from_user.full_name, telegram_id=user_in)
        user.save()
        await message.answer(f"Здравствуйте {message.from_user.full_name}!\nВидимо вы новенький!\nНажмите /help, чтобы вспомнить, что я могу", reply_markup=types.ReplyKeyboardRemove())


@router.message(Command("help"))
async def print_help_massage(message: types.Message):
    await message.answer(f"Вот, что я умею:\n{HELP_MESSAGE}")