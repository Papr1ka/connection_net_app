import requests
from exceptions import CommonPasswordError, ServerError, AccessError, ShortPasswordError, UserExistsError

#URL = "http://127.0.0.1:8000/api/v1/"
URL = "https://connection-net.herokuapp.com/api/v1/"

class Connector():
    def __init__(self) -> None:
        self.autorized = False
    
    
    def requiredAuthorization(func):
        def wrapper(self, *args, **kwargs):
            if not self.autorized:
                raise AccessError("Required Authorization")
            return func(self, *args, **kwargs)
        return wrapper
            
    @requiredAuthorization
    def getcontacts(self) -> dict:
        url = URL + 'chatList'
        r = requests.get(url=url, headers=self.headers)
        return r.json()
    
    
    def autorize(self, username: str, password: str) -> str:
        
        if not isinstance(username, str):
            raise ValueError("Expected username:str")
        if not isinstance(password, str):
            raise ValueError("Expected password:str")

        url = URL + 'auth/token/login'
        data = {
            'username': username,
            'password': password
        }
        r = requests.post(url=url, json=data)
        if r.status_code == 200:
            self.token = r.json()['auth_token']
            self.autorized = True
            self.headers = {'Authorization': f'Token {self.token}'}
            return self.token
        raise AccessError(r.text)
    
    @requiredAuthorization
    def getMe(self) -> dict:
        url = URL + 'auth/users/me'
        r = requests.get(url=url, headers=self.headers)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 204:
            raise ServerError(f'Server exception 204: {r.text}')
        elif r.status_code == 400:
            raise ServerError(f'Server exception 400: {r.text}')
        raise AccessError(r.text)

    @requiredAuthorization
    def getuserlist(self) -> dict:
        url = URL + 'userList'
        r = requests.get(url=url, headers=self.headers)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 204:
            raise ServerError(f'Server exception 204: {r.text}')
        elif r.status_code == 400:
            raise ServerError(f'Server exception 400: {r.text}')
        raise AccessError(r.text)
    
    @requiredAuthorization
    def getmessagelist(self, chat_id: str, part: str) -> dict:
        if not isinstance(chat_id, str):
            raise ValueError("Expected chat_id:str")
        if not isinstance(part, str):
            raise ValueError("Expected part:str")
        
        url = URL + 'messages'
        
        data = {
            'chat_id': chat_id,
            'part': part
        }
        
        r = requests.get(url=url, headers=self.headers, json=data)
        if r.status_code == 200:
            result = r.json()
            error = result.get("error", None)
            if error:
                raise ValueError(error)
            return r.json()
        raise AccessError(r.text)

    @requiredAuthorization
    def sendmessage(self, chat_id: str, text):
        if not isinstance(chat_id, str):
            raise ValueError("Expected chat_id:str")

        url = URL + 'messages'
        data = {
            'chat_id': chat_id,
            'text': text
        }
        
        r = requests.post(url=url, headers=self.headers, data=data)
        if r.status_code == 200:
            result = r.json()
            error = result.get("error", None)
            if error:
                raise ValueError(error)
            return r.json()
        raise AccessError(r.text)

    @requiredAuthorization
    def createchat(self, user_id: str):
        if not isinstance(user_id, str):
            raise ValueError("Expected user_id:str")

        url = URL + 'chat'
        data = {
            'users': [user_id],
        }
        
        r = requests.post(url=url, headers=self.headers, data=data)
        if r.status_code == 200:
            result = r.json()
            error = result.get("error", None)
            if error:
                raise ValueError(error)
            return r.json()
        raise AccessError(r.text)
    
    def register(self, username: str, password: str) -> str:
        
        if not isinstance(username, str):
            raise ValueError("Expected username:str")
        if not isinstance(password, str):
            raise ValueError("Expected password:str")

        url = URL + 'auth/users/'
        data = {
            'username': username,
            'password': password
        }
        r = requests.post(url=url, json=data)
        if r.status_code == 201:
            return self.autorize(username=username, password=password)
        elif r.status_code == 400:
            js = r.json()
            if js.get('username', None):
                if js['username'][0] == "A user with that username already exists.":
                    raise UserExistsError(r.text)
            elif js.get('password', None):
                if js['password'][0] == "This password is too short. It must contain at least 8 characters.":
                    raise ShortPasswordError(r.text)
                elif js['password'][0] == "This password is too common.":
                    raise CommonPasswordError(r.text)
            raise AccessError(r.text)
        raise AccessError(r.text)
