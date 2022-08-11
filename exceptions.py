class ServerError(Exception):
    pass

class AccessError(Exception):
    pass

class UserExistsError(Exception):
    pass

class CommonPasswordError(Exception):
    pass

class ShortPasswordError(Exception):
    pass