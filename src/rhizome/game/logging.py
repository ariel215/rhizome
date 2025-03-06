import logging
import logging.handlers
from collections import deque

log_queue = deque()

gameHandler = logging.handlers.QueueHandler(log_queue)
logging.basicConfig(handlers=[gameHandler])