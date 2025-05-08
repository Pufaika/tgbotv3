from aiogram import Bot, Dispatcher, executor
from config import BOT_TOKEN
from database import init_db
from user_panel import register_user_handlers
from admin_panel import register_admin_handlers

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

register_user_handlers(dp)
register_admin_handlers(dp)

if __name__ == "__main__":
    init_db()
    executor.start_polling(dp, skip_updates=True)
