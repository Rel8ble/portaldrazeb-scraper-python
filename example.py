"""Czech auctions from portaldrazeb.cz with the rel8ble/portal-drazeb-scraper actor.

1. Upcoming flat and house auctions in the given regions/cities -> auctions.csv,
   sorted by the biggest discount of the minimum bid to the appraisal price.
2. Recently finished real-estate auctions -> how final prices compared with the
   minimum bid and the appraisal.

Usage:
    pip install -r requirements.txt
    export APIFY_TOKEN=<YOUR_APIFY_TOKEN>
    python example.py Praha Brno
"""

import csv
import os
import sys
from statistics import median

from apify_client import ApifyClient

ACTOR = "rel8ble/portal-drazeb-scraper"


def run_actor(client: ApifyClient, run_input: dict) -> list[dict]:
    run = client.actor(ACTOR).call(run_input=run_input)
    if run is None or run.get("status") != "SUCCEEDED":
        raise SystemExit(f"Run did not succeed: {run}")
    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


def doc_url(auction: dict, doc_type: str) -> str:
    for d in auction.get("documents") or []:
        if d.get("type") == doc_type:
            return d.get("url", "")
    return ""


def upcoming_to_csv(client: ApifyClient, locations: list[str]) -> None:
    auctions = run_actor(client, {
        "listings": ["upcoming"],
        "categories": ["flat", "house"],
        "locations": locations,
    })
    # Biggest discount first: a minimum bid at 50% of appraisal sorts before 66.7%.
    auctions.sort(key=lambda a: (a.get("minimumBidPctOfEstimate") or 100, a.get("startAt") or ""))

    with open("auctions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "date", "category", "city", "address", "appraisal_czk", "minimum_bid_czk",
            "pct_of_appraisal", "deposit_czk", "online", "expert_report", "url",
        ])
        for a in auctions:
            w.writerow([
                (a.get("startAt") or "")[:10],
                a.get("categoryEn"),
                a.get("city"),
                a.get("address"),
                a.get("estimatedPrice"),
                a.get("minimumBid"),
                a.get("minimumBidPctOfEstimate"),
                a.get("cautionDeposit"),
                "yes" if a.get("electronic") else "no",
                doc_url(a, "expert_report"),
                a.get("url"),
            ])

    print(f"{len(auctions)} upcoming flat/house auctions in {', '.join(locations)} -> auctions.csv")
    for a in auctions[:10]:
        print(
            f'  {(a.get("startAt") or "")[:10]}  {str(a.get("city") or ""):<16} '
            f'{a.get("minimumBid") or 0:>12,} CZK  '
            f'({a.get("minimumBidPctOfEstimate")}% of {a.get("estimatedPrice") or 0:,})  '
            f'{a.get("title")}'
        )


def finished_summary(client: ApifyClient) -> None:
    finished = [
        a for a in run_actor(client, {"listings": ["finished"], "categories": ["realEstate"]})
        if a.get("currentPrice") and a.get("minimumBid") and a.get("estimatedPrice")
    ]
    if not finished:
        print("No finished real-estate auctions with a final price right now.")
        return

    over_min = [a["currentPrice"] / a["minimumBid"] - 1 for a in finished]
    of_est = [a["currentPrice"] / a["estimatedPrice"] for a in finished]
    at_min = sum(1 for a in finished if a["currentPrice"] == a["minimumBid"])

    print(f"\n{len(finished)} recently finished real-estate auctions with a final price")
    print(f"  sold at the minimum bid (no competing bids): {at_min} ({at_min / len(finished):.0%})")
    print(f"  median final price vs minimum bid: +{median(over_min):.0%}")
    print(f"  median final price as % of appraisal: {median(of_est):.0%}")
    top = max(finished, key=lambda a: a["currentPrice"] / a["minimumBid"])
    print(
        f'  most contested: {top["title"]} ({top.get("city")}) '
        f'{top["minimumBid"]:,} -> {top["currentPrice"]:,} CZK  {top["url"]}'
    )


def main() -> None:
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        raise SystemExit("Set APIFY_TOKEN (https://console.apify.com/settings/integrations)")
    locations = sys.argv[1:] or ["Praha"]
    client = ApifyClient(token)
    upcoming_to_csv(client, locations)
    finished_summary(client)


if __name__ == "__main__":
    main()
