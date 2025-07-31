import asyncio
from main_router import router as main_router
from document_router import router as doc_router
from learning_router import router as learn_router
from middleware import user_and_token_checker
from basic_router import router as basic_router
from loader import bot, dp
import time

async def main() -> None:
    dp.include_routers(basic_router, doc_router, learn_router, main_router)

    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    # And the run events dispatching
    await bot.delete_webhook(drop_pending_updates=True)
    dp.update.outer_middleware(user_and_token_checker)
    while True:
        await dp.start_polling(bot)
        time.sleep(100)


if __name__ == "__main__":
   asyncio.run(main())