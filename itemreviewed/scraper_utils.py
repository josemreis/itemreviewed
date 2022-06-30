import requests
from io import StringIO
from typing import Optional, Union
from requests.exceptions import HTTPError
import time
import random
import domain.utils as du
from googletrans import Translator
import translators as ts
from urllib.parse import unquote, urlparse
from unshortenit import UnshortenIt
from lxml import etree
from newsplease import NewsPlease
from .url_utils import validate_url
from .utils import retry_with_backoff

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"
}


def _scrape(
    url: str,
    headers: dict = DEFAULT_HEADERS,
    max_retries: int = 5,
    back_off_factor: float = 2,
    status_no_retry: list = [401, 403, 404, 404, 405, 406],
) -> Optional[requests.models.Response]:
    """GET request with exponetial back-off plus random milisecond"""
    attempts = 0
    response = None
    while attempts < max_retries:
        attempts += 1
        sleep_time = back_off_factor**attempts + random.uniform(0, 1)
        try:
            response = requests.get(url=url, timeout=5, headers=headers)
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


def scrape(
    url: str, lxml_parse: bool = False, **kwargs
) -> Union[requests.models.Response, etree._ElementTree]:
    """wraper around _scraper with optional lxml source code parsing"""
    response = _scrape(url=url, **kwargs)
    if lxml_parse:
        return parse_page(response.text)
    else:
        return response


def parse_page(raw_html: str) -> etree._ElementTree:
    """DOM parser"""
    parser = etree.HTMLParser()
    return etree.parse(StringIO(raw_html), parser)


def get_xpath(elem: etree._Element) -> str:
    """Get the xpath from an element"""
    return elem.getroottree().getpath(elem)


def position_in_dom(elem: etree._Element, count_ascendent: bool = True) -> int:
    """count the number of nodes until you reach the body element"""
    if count_ascendent:
        counter_iterator = elem.iterancestors()
    else:
        counter_iterator = elem.iterdescendants()
    i = 0
    for _ in counter_iterator:
        i += 1
    return i


def parse_link_text(link_elem: etree._ElementTree, **kwargs) -> Optional[str]:
    """Given a url in a page, fetch its element and collect its text, the text from the parent node and its tail, and concatenate"""
    parent_elem = link_elem.getparent()
    text_dict = {
        "parent_element_text": parent_elem.text,
        "link_element_text": link_elem.text,
        "link_element_tail_text": link_elem.tail,
    }
    # concatenate it
    text = ""
    for _, text_part in text_dict.items():
        if text_part:
            text += text_part
    if len(text):
        text_dict["text_combine"] = text
        return text_dict


def link_rank(dom: etree._Element, target_url: str) -> Optional[int]:
    """What is the rank position of the url in the text"""
    urls = []
    for anchor_tag in dom.xpath("//body//p//*[@href]"):
        a_url = anchor_tag.get("href")
        if a_url and validate_url(a_url):
            urls.append(a_url)
    if urls:
        return urls.index(target_url)


def process_link_element(dom: etree._ElementTree, url: str, factcheck_url: str,) -> Optional[dict]:
    """
    Fetch the element containing a specific url along with the following metadata:
        * text (from the parent node, of the href, and suffix, as well as combined)
    """
    link_elem = dom.xpath(f"*//[href = '{url}']")
    if link_elem:
        return {
            "itemreviewed": url,
            "link_element_other_attributes": {
                k: v for k, v in link_elem.items() if k != "href"
            },
            "link_rank": link_rank(dom, url),
            "number_of_ascestors": position_in_dom(link_elem, count_ascendent=True),
            "number_of_descendants": position_in_dom(link_elem, count_ascendent=False),
            "is_internal_link": du.get_etld1(factcheck_url) == du.get_etld1(url)
        }


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


def get_element(dom, xpath_query: str) -> etree._Element:
    """Fetch a web element using a xpath query"""
    return dom.xpath(xpath_query)


def get_xpath(elem: etree._Element) -> str:
    """Get the xpath from an element"""
    return elem.getroottree().getpath(elem)


# # load the language detector
# detector = gcld3.NNetLanguageIdentifier(min_num_bytes=5, max_num_bytes=1000)


# def detect_language(
#     txt: str = "Wo bist du dann?", prob_treshhold: int = 0.8
# ) -> Optional[str]:
#     """detect language using cdl3 engine"""
#     result = detector.FindLanguage(text=txt)
#     if result.probability >= prob_treshhold:
#         return result.language


# def unshorten_url(url: str, debug: bool = False) -> str:
#     """unshorten an url"""
#     if any([_ for _ in LIST_OF_URL_SHORTNERS if _ + "/" in url]):
#         try:
#             resp = session.head(url, allow_redirects=True)
#             uri = resp.url
#             if url == uri:
#                 # takes longer...
#                 uri = unshortener.unshorten(url)
#             if debug:
#                 print(f"[+] shortened: {url} -> original: {uri}")
#             return resp.url
#         except Exception as e:
#             print(f"[-] Error could not unshorten {url}: {e}")
#             return url
#     else:
#         return url


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
