# google fact check tools claimreview data dump
DATAFEED_URL = "https://storage.googleapis.com/datacommons-feeds/claimreview/latest/data.json"
# tentative paths to the itemreviewed url value in glob syntax (for dpa utils)
PATHS_TO_ITEM_REVIEWED_URL = [
    "*ppearance/*/url",
    "*ppearance/url",
]