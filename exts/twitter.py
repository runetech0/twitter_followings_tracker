import json
import tweepy
from random import randrange
from models.exceptions import UserNotFound
from models.global_vars import USER_NOT_FOUND_REASON


class TwitterAPI:
    def __init__(self):
        self.config = json.load(open('twitter_config.json'))
        self.authenticated_apps = []
        self.setup_apis()

    def get_random_api(self):
        while True:
            total = len(self.authenticated_apps)
            if total == 1:
                index = 0
            else:
                index = randrange(0, total-1)
            yield self.authenticated_apps[index]

    def get_user_if_exists(self, username):
        api = next(self.random_api)
        try:
            user = api.get_user(username)
        except tweepy.error.RateLimitError:
            return self.get_user_if_exists(username)
        except tweepy.error.TweepError as e:
            if e.reason == USER_NOT_FOUND_REASON:
                raise UserNotFound('No such username exists on twitter')
        return user

    def setup_apis(self):
        creds = list(self.config.get("TWITTER_APPS_CREDS"))
        for cred in creds:
            API_KEY = cred.get("APP_API_KEY")
            API_KEY_SECRET = cred.get("APP_API_KEY_SECRET")
            ACCESS_TOKEN = cred.get("APP_ACCESS_TOKEN")
            ACCESS_TOKEN_SECRET = cred.get("APP_ACCESS_TOKEN_SECRET")
            auth = tweepy.OAuthHandler(API_KEY, API_KEY_SECRET)
            auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
            api = tweepy.API(auth, wait_on_rate_limit=True,
                             wait_on_rate_limit_notify=True)
            self.authenticated_apps.append(api)
        self.random_api = self.get_random_api()
