""" Core errors """

class CheckInError(Exception):
    def __init__(self, time, message="You are checked in already"):
        self.message = message
        self.time = time

class CheckOutError(Exception):
    def __init__(self, message="You must be checked before you can check out."):
        self.message = message
