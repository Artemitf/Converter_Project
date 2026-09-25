import asyncio
import logging
from datetime import datetime, timedelta
import aiohttp

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_TOKEN = '7965415769:AAEjicbA1QPiSTYsIsanHKgUwwbKOxGySqI'
WORKER_URL = 'https://tg-proxy.parhartemtemp1.workers.dev'  # Ваш Cloudflare Worker
BYBIT_API_URL = 'https://api.bybit.com/v5/market/tickers'
DATABASE_NAME = 'currency_bot.db'

# Подключаем прокси через Cloudflare Worker с помощью TelegramAPIServer
session = AiohttpSession(
    api=TelegramAPIServer.from_base(WORKER_URL)
)

# Инициализация бота с сессией
bot = Bot(token=API_TOKEN, session=session)

# Инициализация диспетчера и хранилища
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

from handlers import *
from database import init_db
from api import check_notifications

# Регистрация обработчиков команд
dp.message.register(cmd_start, Command("start"))
dp.message.register(cmd_help, Command("help"))

# Регистрация обработчиков кнопок
dp.message.register(main_menu, F.text == "🔄 Главный экран")
dp.message.register(back_to_main, F.text == "↩️ На главный")

dp.message.register(start_converter, F.text == "💰 Конвертер")
dp.message.register(converter_back_to_main, ConverterStates.waiting_for_currency1, F.text == "↩️ На главный")
dp.message.register(process_currency1, ConverterStates.waiting_for_currency1)
dp.message.register(converter_amount_back_to_main, ConverterStates.waiting_for_amount, F.text == "↩️ На главный")
dp.message.register(process_amount, ConverterStates.waiting_for_amount)
dp.message.register(converter_currency2_back_to_main, ConverterStates.waiting_for_currency2, F.text == "↩️ На главный")
dp.message.register(process_currency2, ConverterStates.waiting_for_currency2)

dp.message.register(show_favorites, F.text == "⭐ Избранное")
dp.message.register(edit_favorites_start, F.text == "Изменить список")
dp.message.register(edit_fav_back_to_main, FavoriteStates.waiting_for_edit_choice, F.text == "↩️ На главный")
dp.message.register(process_edit_choice, FavoriteStates.waiting_for_edit_choice)
dp.message.register(fav_currency1_back_to_main, FavoriteStates.waiting_for_fav_currency1, F.text == "↩️ На главный")
dp.message.register(process_fav_currency1, FavoriteStates.waiting_for_fav_currency1)
dp.message.register(fav_currency2_back_to_main, FavoriteStates.waiting_for_fav_currency2, F.text == "↩️ На главный")
dp.message.register(process_fav_currency2, FavoriteStates.waiting_for_fav_currency2)

dp.message.register(notifications_menu, F.text == "🔔 Уведомления")
dp.message.register(create_notification_start, F.text == "➕ Создать уведомление")
dp.message.register(notification_asset_back_to_main, NotificationStates.waiting_for_asset, F.text == "↩️ На главный")
dp.message.register(process_notification_asset, NotificationStates.waiting_for_asset)
dp.message.register(notification_percent_back_to_main, NotificationStates.waiting_for_percent, F.text == "↩️ На главный")
dp.message.register(process_notification_percent, NotificationStates.waiting_for_percent)
dp.message.register(delete_notification_start, F.text == "🗑️ Удалить уведомление")
dp.message.register(delete_notification_back_to_main, NotificationStates.waiting_for_delete_asset, F.text == "↩️ На главный")
dp.message.register(process_delete_notification, NotificationStates.waiting_for_delete_asset)

dp.message.register(unknown_command)

async def main():
    await init_db()
    
    asyncio.create_task(check_notifications(bot))
    
    logger.info("Бот запущен через Cloudflare Worker")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())