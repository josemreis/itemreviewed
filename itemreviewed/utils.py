import random
import time
from typing import Callable, TypeVar

T = TypeVar("T")


def retry_with_backoff(
    function: Callable[[], T], retries: int = 3, backoff_base: int = 2
) -> T:
    """Retry a function with expontential backoff"""
    attempts = 0
    while True:
        try:
            return function()
        except Exception as e:
            if attempts == retries:
                raise e
            else:
                sleep = backoff_base**attempts + random.uniform(0, 1)
                print(f"error: '{e}', retrying in {round(sleep)} secs.")
                time.sleep(sleep)
                attempts += 1

