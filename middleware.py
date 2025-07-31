import asyncio
from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from datetime import datetime
from db.database import User
from api.tokens_api import OAUTH_API
from basic_router import start
import requests
import json

class UserAndTokenCheck(BaseMiddleware):
    def __init__(self):
        self.last_token = None
        self.last_time = None
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        if not self.last_token or (datetime.today() - self.last_time).seconds // 3600 > 1:
            body = {
                'yandexPassportOauthToken': OAUTH_API
            }
            headers = {
                "Content-Type": "application/json"
            }
            response = requests.post("https://iam.api.cloud.yandex.net/iam/v1/tokens", json=body, headers=headers)
            token = json.loads(response.text)['iamToken']
            self.last_token = token
            self.last_time = datetime.today()
        user_id = data["event_from_user"].id
        user = User.get_or_none(User.telegram_id == user_id)
        if user:
            data['user_in'] = user_id
            state = data["state"]
            state_data = await state.get_data()
            if not state_data.get('language'):
                await state.update_data(language='английский')
            if not state_data.get('dictation_difficulty'):
                await state.update_data(dictation_difficulty='обычный')
            return await handler(event, data)
        else:
            try:
                return await start(event.message, data)
            except Exception:
                return event.answer("Нажмите /start для начала работы с ботом")
    
user_and_token_checker = UserAndTokenCheck()
