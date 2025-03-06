import io
from queue import Queue
from rhizome.game.logging import logger, log

def test_queue_handler():
    log("hello")
    assert len(logger.messages) == 1