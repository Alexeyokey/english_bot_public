from aiogram import Bot, Dispatcher
from api.tokens_api import API_TOKEN


bot = Bot(token=API_TOKEN)
dp = Dispatcher()