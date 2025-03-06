class Logger():
    def __init__(self):
        self.messages = []

    def log(self, message):
        self.messages.append(message)

logger = Logger()

def log(message):
    logger.log(message)