from pymongo import MongoClient
import uuid
from datetime import datetime
import re
import os
import bcrypt


class Database:
    def __init__(self):
        connection = MongoClient(os.environ['MONGO_URI'])['COL']
        self.users = connection['users']
        self.reports = connection['reports']
        self.locations = connection['locations']
        self.admin = connection['admin']
        self.portal_reports = connection['portal_reports']
        
    def userExist(self, email=None, ID=None):
        if email is not None:
            return self.users.find_one({'email': email}) is not None
        elif ID is not None:
            return self.users.find_one({'_id': ID}) is not None
        else:
            return False
    
    def getUser(self, email=None, ID=None):
        if email is not None:
            return self.users.find_one({'email': email})
        elif ID is not None:
            return self.users.find_one({'_id': ID})
        else:
            return None
    
    def registerUser(self, email, password, name, role='user'):
        if (
            self.userExist(email=email)
            or not self.userExist(email=email)
            and re.match(
                r'^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$', email
            )
            is None
        ):
            return False
        salt = bcrypt.gensalt()
        password = bcrypt.hashpw(password.encode('utf-8'), salt)
        self.users.insert_one({
            '_id': str(uuid.uuid4()),
            'email': email,
            'password': password,
            'name': name,
            'role': role,
            'created': datetime.now(),
            'car-reports': [],
            'portal-reports': [],
        })
        return True
    
    def authenticate(self, email, password):
        user = self.getUser(email=email)
        if user is not None and bcrypt.checkpw(
            password.encode('utf-8'), user['password']
        ):
            return user
        return False
        
    def getUserReports(self, user_id):
        user = self.getUser(ID=user_id)
        return [] if user is None else user['car-reports']
        
    def getUserPortalReports(self, user_id):
        user = self.getUser(ID=user_id)
        return [] if user is None else user['portal-reports']
    
    def reportFromPortal(self, user_id, title, content):
        user = self.getUser(ID=user_id)
        if user is None:
            return False
        id_ = str(uuid.uuid4())
        self.portal_reports.insert_one({
            '_id': id_,
            'user': user_id,
            'title': title,
            'content': content,
            'created': datetime.now(),
        })
        self.users.update_one({'_id': user_id}, {'$push': {'portal-reports': id_}})
        return True