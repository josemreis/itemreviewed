import requests
from typing import Optional
from requests.exceptions import HTTPError
import time
import random
from googletrans import Translator
import translators as ts
from urllib.parse import unquote, urlparse
from unshortenit import UnshortenIt


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

def _translate(txt: str = "Wo bist du dann?") -> Optional[str]:
    """translate some text"""
    ## first we try with googletrans
    if txt and len(txt) > 0:
        try:
            # google
            translated = ts.google(txt, from_language="auto-detect", to_language="en")
            return translated
        except:
            ## try with the translators module
            try:
                # google
                translator = Translator()
                translated = translator.translate(txt, dest="en").text
            except:
                raise ValueError(f"Could not translate: {txt}")


def translate(
    txt: str = "Wo bist du dann?", retries=5, backoff_in_seconds=1
) -> Optional[str]:
    """wrapper to _translate with exponential backoff"""
    attempts = 0
    while True:
        try:
            return _translate(txt=txt)
        except Exception as e:
            if attempts == retries:
                raise e
            else:
                sleep = backoff_in_seconds**attempts + random.uniform(0, 1)
                print("Error during translation, sleeping for ", str(sleep) + "s")
                time.sleep(sleep)
                attempts += 1


# # load the language detector
# detector = gcld3.NNetLanguageIdentifier(min_num_bytes=5, max_num_bytes=1000)


# def detect_language(
#     txt: str = "Wo bist du dann?", prob_treshhold: int = 0.8
# ) -> Optional[str]:
#     """detect language using cdl3 engine"""
#     result = detector.FindLanguage(text=txt)
#     if result.probability >= prob_treshhold:
#         return result.language


def unshorten_url(url: str, debug: bool = False) -> str:
    """unshorten an url"""
    if any([_ for _ in LIST_OF_URL_SHORTNERS if _ + "/" in url]):
        try:
            resp = session.head(url, allow_redirects=True)
            uri = resp.url
            if url == uri:
                # takes longer...
                uri = unshortener.unshorten(url)
            if debug:
                print(f"[+] shortened: {url} -> original: {uri}")
            return resp.url
        except Exception as e:
            print(f"[-] Error could not unshorten {url}: {e}")
            return url
    else:
        return url


# def url_has_path(url: str, debug: bool = False) -> bool:
#     """detect if url has a path or a query string"""
#     out = False
#     url_parsed = urlparse(url)
#     url_path = url_parsed.path
#     url_qs = url_parsed.query
#     if url_path:
#         if url_path != "/":
#             out = True
#     if url_qs:
#         if len(url_qs) > 2:
#             out = True
#     if debug and out == False:
#         print(f"[!] {url} does not have a path")
#     return out