import requests
from typing import Optional
from requests.exceptions import HTTPError
import time
import random


def scrape(
    url: str,
    max_retries: int = 5,
    back_off_factor: float = 2,
    status_no_retry: list =[401, 403, 404, 404, 405, 406],
) -> Optional[bytes]:
    """GET request with exponetial back-off plus random milisecond"""
    attempts = 0
    response = None
    while attempts < max_retries:
        attempts += 1
        sleep_time = back_off_factor**attempts + random.uniform(0, 1)
        try:
            response = requests.get(url=url, timeout=5)
            if response.status_code in status_no_retry:
                attempts = max_retries
            response.raise_for_status()
            break
        except HTTPError as http_err:
            time.sleep(sleep_time)
            raise ValueError(
                f"HTTP Error {http_err}. Retrying in roughly {str(round(sleep_time,3))} secs."
            )
        except Exception as err:
            raise ValueError(f"Another non HTTP Request error occurred: {err}.")
    if response:
        response.raw.chunked = True  # Fix issue 1
        response.encoding = "utf-8"  # Fix issue 2
        return response



