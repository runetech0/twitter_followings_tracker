from telethon.tl.custom import Button
from telethon import TelegramClient
from models.global_vars import *
from exts.db import DB
from models.exceptions import UserNotFound
from exts.twitter import TwitterAPI


class EventHandlers:
    def __init__(self, bot: TelegramClient):
        self.bot = bot
        self.twitter_api = TwitterAPI()
        self.db = DB()

    async def start(self, event):
        btns = [
            [
                Button.text(ADD_USER_BTN),
                Button.text(REMOVE_USER_BTN)
            ],
            [
                Button.text(LIST_USER_BTN)
            ]
        ]
        await event.respond('Main Menu', buttons=btns)

    async def add_user(self, event):
        await event.delete()
        async with self.bot.conversation(event.message.peer_id) as self.conv:
            await self.conv.send_message('Please enter new twitter username?')
            resp = await self.conv.get_response()
            username = resp.text
            try:
                user = self.twitter_api.get_user_if_exists(username)
                self.db.add_new_user(
                    user._json["screen_name"], user._json["id"])
                await self.conv.send_message('New user added to database.\nIt will start getting tracked soon.')
                self.conv.cancel()
                return
            except UserNotFound:
                await self.conv.send_message('Username not found on the twitter.\nPlease check if username is correct.')
                self.conv.cancel()
                return

    async def list_user(self, event):
        await event.delete()
        usernames = self.db.get_all_usernames()
        message = 'List of Users\n'
        for username in usernames:
            message = f'{message}\n{username}'
        await event.respond(message)

    async def remove_user(self, event):
        await event.delete()
        async with self.bot.conversation(event.message.peer_id) as self.conv:
            await self.conv.send_message('Please enter new twitter username you want to remove?')
            resp = await self.conv.get_response()
            username = resp.text
            if not self.db.user_exists(username):
                await self.conv.send_message('This username does not exist on the bot.')
                return
            self.db.remove_user(username)
            await self.conv.send_message(f'{username} has been removed!')
            self.conv.cancel()
