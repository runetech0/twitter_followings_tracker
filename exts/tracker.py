import json
import asyncio
import tweepy
from exts.db import DB
from random import randrange
import logging


class Tracker:
    def __init__(self, queue):
        self.config = json.load(open('twitter_config.json'))
        self.queue = queue
        self.loop = asyncio.new_event_loop()
        self.log = logging.getLogger(' Tracker ').info
        self.count = 200

    def start(self):
        self.db = DB()
        self.loop.run_until_complete(self.main())

    async def main(self):
        self.log('Setting up Apps ...')
        await self.setup_apis()
        self.log("Followings tracker is ready!")
        while True:
            all_users = self.db.get_all_users()
            if len(all_users) == 0:
                await asyncio.sleep(10)
                continue
            for user in all_users:
                if not user['tracked']:
                    await self.track_user(user)
                    continue
                new_followings = await self.check_for_new_followings(user)
                for user_id in new_followings:
                    message = await self.create_message_for_tg(user_id, user["username"])
                    self.queue.put(message)
            await asyncio.sleep(self.get_wait_time(len(all_users)))

    def get_wait_time(self, number_of_users):
        if number_of_users <= 5:
            return 300
        elif number_of_users > 5 and number_of_users <= 10:
            return 200
        elif number_of_users > 10:
            return 100

    async def create_message_for_tg(self, following_id, follower_username):
        api = next(self.random_api)
        user = api.get_user(user_id=following_id)
        username = user._json["screen_name"]
        profile_url = f'https://twitter.com/{username}'
        follower_profile_url = f'https://twitter.com/{follower_username}'
        message = f'[{follower_username}]({follower_profile_url}) just started to follow [{username}]({profile_url}).'
        return message

    async def check_for_new_followings(self, user):
        cur = user["cursor"]
        api = next(self.random_api)
        try:
            results = api.friends(user["username"],
                                  cursor=cur, count=self.count)
            await asyncio.sleep(1)
        except tweepy.error.RateLimitError:
            self.log('Hit rate limit on API, switching to next App.')
            await asyncio.sleep(300)
            return await self.check_for_new_followings(user)
        except tweepy.error.TweepError:
            self.log('Tweepy Error in check for new followings')
            await asyncio.sleep(300)
            return await self.check_for_new_followings(user)
        friends = results[0]
        followings_list = list()
        for friend in friends:
            followings_list.append(friend._json["id"])

        def filter_followings(user_id):
            if user_id in user["followings_list"]:
                return False
            return True

        if results[1][1] != 0:
            new_cur = results[1][1]
            self.db.update_cursor(user["user_id"], new_cur)
        new_followings = list(filter(filter_followings, followings_list))
        if len(new_followings) != 0:
            self.db.extend_users_followings_list(
                user["user_id"], new_followings)
        return new_followings

    def get_random_api(self):
        while True:
            total = len(self.authenticated_apps)
            if total == 1:
                index = 0
            else:
                index = randrange(0, total-1)
            yield self.authenticated_apps[index]

    async def track_user(self, user):
        username = user["username"]
        cur = -1
        followings_list = list()
        api = next(self.random_api)
        while True:
            try:
                results = api.friends(username,
                                      cursor=cur, count=self.count)
                await asyncio.sleep(1)
            except tweepy.error.RateLimitError:
                self.log(
                    'Hit rate limit on API, switching to next App.', exc_info=True)
                await asyncio.sleep(300)
                api = next(self.random_api)
                continue
            except tweepy.error.TweepError:
                self.log('Tweepy error in track_user', exc_info=True)
                await asyncio.sleep(300)
                continue
            friends = results[0]
            for friend in friends:
                followings_list.append(friend._json["id"])
            if results[1][1] == 0:
                break
            cur = results[1][1]
        self.db.update_cursor(user["user_id"], cur)
        self.db.extend_users_followings_list(user["user_id"], followings_list)
        self.db.set_user_tracked(user["user_id"])

    async def setup_apis(self):
        creds = list(self.config.get("TWITTER_APPS_CREDS"))
        self.authenticated_apps = []
        for cred in creds:
            API_KEY = cred.get("APP_API_KEY")
            API_KEY_SECRET = cred.get("APP_API_KEY_SECRET")
            ACCESS_TOKEN = cred.get("APP_ACCESS_TOKEN")
            ACCESS_TOKEN_SECRET = cred.get("APP_ACCESS_TOKEN_SECRET")
            auth = tweepy.OAuthHandler(API_KEY, API_KEY_SECRET)
            auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
            api = tweepy.API(auth)
            self.authenticated_apps.append(api)
        self.random_api = self.get_random_api()
