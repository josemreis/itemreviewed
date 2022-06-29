import json
import sys
import os

sys.path.append(os.path.abspath("../itemreviewed"))
from itemreviewed.claimreview_utils import *
from itemreviewed.constants import DATAFEED_URL

OUTPUT_PATH = "data/claimreview_feed.json"

def main(output_path: str = OUTPUT_PATH) -> None:
    """fetch Googles claimreview data feed, parse it, and store as json"""
    print(
        f"[+] Fetching and parsing the claimReview data in the datafeed: {DATAFEED_URL}"
    )
    parsed_feed = get_claimreview_datacommons_feed()
    relevant_data = []
    for feed_item in parsed_feed:
        parsed_feed_item = parse_claimreview(feed_item, translate_claim=False)
        if parsed_feed_item.get("items_reviewed"):
            relevant_data.append(parsed_feed_item)
    print(f"[+] Found {len(relevant_data)} claimReview items")
    with open(output_path, "w") as f:
        json.dump(relevant_data, f, indent=4, ensure_ascii=False)
    print(f"[+] You can find the data in {output_path}")


if __name__ == "__main__":
    main()
