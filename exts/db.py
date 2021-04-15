from pymongo import MongoClient


class DB:
    def __init__(self):
        self.client = MongoClient()
        self.db = self.client.users_db
        self.users = self.db.users
        self.tracked = self.db.tracked

    def get_all_users(self):
        users = self.users.find({})
        return [user for user in users]

    def get_all_usernames(self):
        users = self.users.find({})
        return [user["username"] for user in users]

    def user_exists(self, username):
        user = self.users.find_one({'username': username})
        return True if user else False

    def get_untracked_usernames(self):
        users = self.users.find({'tracked': False})
        return [user["username"] for user in users]

    def get_user_cursor(self, user_id):
        user = self.users.find_one({'user_id': user_id})
        return user["cursor"] if user else None

    def update_cursor(self, user_id, new_cursor):
        self.users.find_one_and_update({'user_id': user_id},
                                       {'$set': {'cursor': new_cursor}})

    def extend_users_followings_list(self, user_id, new_followings_list):
        self.users.find_one_and_update({
            'user_id': user_id
        }, {
            '$addToSet': {'followings_list': {'$each': new_followings_list}}})

    def add_new_user(self, username, user_id, followings_list=[], cursor=-1):
        user = {
            'user_id': user_id,
            'username': username,
            'followings_list': followings_list,
            'cursor': cursor,
            'tracked': False
        }
        self.users.insert_one(user)

    def remove_user(self, username):
        self.users.delete_one({
            'username': username
        })

    def set_user_tracked(self, user_id):
        self.users.find_one_and_update({
            'user_id': user_id
        }, {
            '$set': {
                'tracked': True
            }
        })
