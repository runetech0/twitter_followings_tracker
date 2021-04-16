from telethon.sync import TelegramClient, events
import json
import asyncio
from tg.event_handlers import EventHandlers
from models.global_vars import *
import multiprocessing as mp
import logging
import os
from exts.tracker import Tracker

logger = logging.getLogger()
logger.setLevel(logging.INFO)
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)
formator = logging.Formatter(
    '[%(asctime)s] - [%(name)s] - %(levelname)s - %(message)s')
consoleHandler.setFormatter(formator)
if not os.path.exists('./logs'):
    os.mkdir('logs')
fileHandler = logging.FileHandler('logs/app.log')
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(formator)
logger.addHandler(fileHandler)
logger.addHandler(consoleHandler)


config = json.load(open('telegram_config.json'))

API_ID = config.get('TELEGRAM_API_ID')
API_HASH = config.get('TELEGRAM_API_HASH')
BOT_TOKEN = config.get('TELEGRAM_BOT_TOKEN')

bot = TelegramClient('bot', API_ID, API_HASH)
event_handlers = EventHandlers(bot)

messages_queue = mp.Queue()

tracker = Tracker(messages_queue)
mp.Process(target=tracker.start).start()


async def setup_event_handlers():
    logger.info('Setting up event handlers .. ')
    admin = config.get("ADMIN_USERNAME")
    bot.add_event_handler(event_handlers.add_user,
                          events.NewMessage(pattern=ADD_USER_BTN, chats=[admin]))
    bot.add_event_handler(
        event_handlers.remove_user, events.NewMessage(pattern=REMOVE_USER_BTN, chats=[admin]))
    bot.add_event_handler(event_handlers.list_user,
                          events.NewMessage(pattern=LIST_USER_BTN, chats=[admin]))
    bot.add_event_handler(event_handlers.start,
                          events.NewMessage(pattern='/start', chats=[admin]))


async def wait_until_ready():
    if not bot.is_connected() or not await bot.is_user_authorized():
        await asyncio.sleep(1)


async def on_ready():
    await wait_until_ready()
    await setup_event_handlers()
    logger.info('Bot is ready!')


async def queue_handler():
    await wait_until_ready()
    admin = config.get("ADMIN_USERNAME")
    while True:
        logger.info('Queue handler is ready!')
        while messages_queue.empty():
            await asyncio.sleep(1)
        message = messages_queue.get(block=False)
        await bot.send_message(admin, message)


bot.start(bot_token=BOT_TOKEN)
bot.loop.create_task(on_ready())
bot.loop.create_task(queue_handler())
bot.run_until_disconnected()
