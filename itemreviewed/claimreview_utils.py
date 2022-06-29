from lib2to3.pgen2.token import OP
from typing import Optional
import requests
import json
import domain_utils as du
import dpath.util
import extruct
from lxml import html
from .constants import DATAFEED_URL, PATHS_TO_ITEM_REVIEWED_URL
from .scraper_utils import scrape, translate


def _get_claimreview_datacommons_feed(
    datafeed_url: str = DATAFEED_URL,
) -> list:
    """Get the claimReview data feed produced by google fct"""
    response = scrape(datafeed_url)
    response.raise_for_status()
    feed_all = json.loads(response.content)
    return feed_all.get("dataFeedElement")


def get_claimreview_datacommons_feed(**kwargs) -> list:
    """
    Wrapper around _get_claim_review_datacommons_feed() for filtering out the ones without fact-check url and without itemReviewed key
    """
    ## fetch the data feed
    data_feed = _get_claimreview_datacommons_feed(**kwargs)
    relevant_items = []
    ## keep only feed items not already present in our database
    for feed_elem in data_feed:
        if feed_elem.get("item"):
            for item_dict in feed_elem.get("item"):
                if item_dict.get("url") and item_dict.get("itemReviewed"):
                    relevant_items.append(item_dict)
    return relevant_items


def get_itemreviewed_urls(item_reviewed_dict: dict, factcheck_url: str) -> list:
    """fetch the urls from a itemReviewed dict"""
    factcheck_domain = du.get_etld1(factcheck_url)
    url_matches = set()
    for _dpath in PATHS_TO_ITEM_REVIEWED_URL:
        urls_matched = dpath.util.values(item_reviewed_dict, _dpath)
        if urls_matched:
            for url_identified in urls_matched:
                if du.get_etld1(url_identified) != factcheck_domain:
                    url_matches.add(url_identified)
    return list(url_matches)


def parse_claimreview(claimreview_dict: str, translate_claim: bool = False) -> list:
    """
    Fetch the datafeed, parse to item level, and extract the following fields:
        * factcheck_url: item["url"]
        * claim_reviewed: item["claimReviewed"]
        * review_rating: item["reviewRating"]
        * date_published: item["datePublished"]
        * itemreviewed_urls: get_itemreviewed(item["itemReviewed"])
    """
    claimreview_parsed = {}
    # get the factcheck url
    claimreview_parsed["factcheck_url"] = claimreview_dict.get("url")
    # claim reviwed
    claimreview_parsed["claim_reviewed"] = claimreview_dict.get("claimReviewed")
    if translate_claim:
        if claimreview_parsed.get("claim_reviewed"):
            try:
                claim_translated = translate(claimreview_parsed.get("claim_reviewed"))
            except Exception as err:
                claim_translated = None
                print(
                    "[!] Error while translating a claim: {}.\n{}.\n Skiping it.".format(
                        claimreview_parsed.get("claim_reviewed"), err
                    )
                )
            claimreview_parsed["claim_translated"] = claim_translated
    # review rating dict
    claimreview_parsed["review_rating"] = claimreview_dict.get("reviewRating")
    # date published
    claimreview_parsed["factcheck_date_published"] = claimreview_dict.get(
        "datePublished"
    )
    # items reviewed
    items_reviewed = get_itemreviewed_urls(
        item_reviewed_dict=claimreview_dict.get("itemReviewed"),
        factcheck_url=claimreview_parsed.get("factcheck_url"),
    )
    if not items_reviewed:
        claimreview_parsed["items_reviewed"] = None
    else:
        claimreview_parsed["items_reviewed"] = items_reviewed
    return claimreview_parsed


def has_claimreview(response: requests.models.Response) -> bool:
    """Given a HTTP response, check wether or not a page uses claim_review schema"""
    ## parse the content
    content = html.fromstring(response.content)
    ## check whether the script tag with the claimReview exists
    claim_review_script = content.xpath(
        '//script[@type="application/ld+json" and contains(text(), "itemReviewed")]'
    )
    return len(claim_review_script) > 0


def get_claimreview_json_ld(
    response: requests.models.Response, url: str
) -> Optional[list]:
    """Fetch JSON-LD structured data containing claim review."""
    ## parse the json linked data metadata
    metadata = extruct.extract(
        response.content,
        base_url=url,
        syntaxes=["json-ld"],
        uniform=True,
    )["json-ld"]
    if metadata:
        if isinstance(metadata, list):
            return metadata[0]
        else:
            return metadata


def parse_claim_review_from_url(url: str) -> Optional[dict]:
    """scrape the source code of a website and parse claimReview json+ld"""
    response = scrape(url)
    # check if the claimReview json+ld script tag is present
    if has_claimreview(response):
        # fetch it
        claimreview_raw = get_claimreview_json_ld(response=response, url=url)
        # parse it
        claimreview_parsed = parse_claimreview(claimreview_raw)
        return claimreview_parsed
