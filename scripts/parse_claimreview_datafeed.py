import json
from itemreviewed.claimreview_utils import get_claimreview_datacommons_feed

OUTPUT_PATH = "data/claim_reviewfeed.json"

def main(output_path:str = OUTPUT_PATH) -> None:
    """ fetch Googles claimreview data feed, parse it, and store as json """