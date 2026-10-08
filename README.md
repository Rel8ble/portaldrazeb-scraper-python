# Portál dražeb (portaldrazeb.cz) scraper in Python: Czech property, flat, house, land and car auctions as JSON/CSV

A short tutorial for pulling **Czech public (execution) auctions from portaldrazeb.cz** in Python with the [Czech Auctions Scraper - Portál dražeb](https://apify.com/rel8ble/portal-drazeb-scraper) actor on Apify. Portál dražeb is the official auction portal of the Czech Chamber of Executors and the largest list of execution auctions in Czechia, but it has no export and no public API. The actor reads the same JSON the site's listing pages load, over plain HTTP with no browser and no login, and returns one record per auction: title, Czech and English category, auction date, appraisal price (odhadní cena), minimum bid (nejnižší podání), minimum bid as a % of appraisal, deposit (jistota), region, district, city, address, GPS, photo URLs, official PDFs (auction decree, expert valuation) and the executor's office. Filter by list (upcoming, ongoing, finished with final price, overbids), category, location, price, date and keywords.

> Disclosure: I built this actor; it's a paid tool on Apify ($3.00 per 1,000 results). The code in this repo is MIT-licensed.

## How it works

The listing pages on portaldrazeb.cz are a Vue app backed by a JSON endpoint (`PUT /drazby/{list}.json`) that needs a CSRF token issued with the page. The actor loads each list page once for the token and cookie, pages through the JSON in blocks of 200, normalises prices, addresses, coordinates, photos and documents, applies your filters and saves one result per matching auction. The whole portal (~800 upcoming auctions) takes about a minute.

## Quick start (Python)

```bash
pip install apify-client
```

```python
from apify_client import ApifyClient

client = ApifyClient("<YOUR_APIFY_TOKEN>")

run = client.actor("rel8ble/portal-drazeb-scraper").call(run_input={
    "listings": ["upcoming"],
    "categories": ["flat", "house"],
    "locations": ["Praha", "Brno"],
    "minPrice": 1000000,
    "maxResults": 20,
})

for a in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(a["startAt"][:10], a["categoryEn"], a["city"],
          f'{a["minimumBid"]:,} CZK ({a["minimumBidPctOfEstimate"]}% of appraisal)',
          a["url"])
```

Get your token at https://console.apify.com/settings/integrations.

## Full example

[`example.py`](example.py) does two things:

1. Pulls upcoming flat and house auctions in the regions or cities you name and writes `auctions.csv` sorted by the biggest discount to appraisal (date, category, city, address, appraisal, minimum bid, % of appraisal, deposit, online or not, expert report link, auction URL).
2. Pulls recently finished real-estate auctions and prints how final prices compared with the minimum bid and the appraisal.

```bash
pip install -r requirements.txt
export APIFY_TOKEN=<YOUR_APIFY_TOKEN>
python example.py Praha Brno
```

## Node.js

```js
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: '<YOUR_APIFY_TOKEN>' });
const run = await client.actor('rel8ble/portal-drazeb-scraper').call({
    listings: ['upcoming', 'finished'],
    categories: ['flat'],
    locations: ['Praha'],
});
const { items } = await client.dataset(run.defaultDatasetId).listItems();
items.forEach((a) => console.log(a.status, a.startAt.slice(0, 10), a.minimumBid, a.currentPrice ?? '-', a.title));
```

## Input

| Field | Default | What it does |
|---|---|---|
| `listings` | `["upcoming"]` | `upcoming` (scheduled, the main list), `ongoing` (running now), `finished` (recently ended, with final price), `overbids` (in the overbid window) |
| `categories` | all | `realEstate`, `land`, `house`, `flat`, `recreational`, `apartmentBuilding`, `commercial`, `garage`, `otherRealEstate`, `movables`, `vehicles`, `electronics`, `furniture`, `art`, `otherMovables`, `intangible` |
| `locations` | all | Region, district, city or street text, e.g. `Praha`, `Brno`, `Jihomoravsky` (accents optional) |
| `minPrice` / `maxPrice` | - | Minimum-bid range in CZK |
| `startFrom` / `startTo` | - | Auction date range, `YYYY-MM-DD` |
| `keywords` | - | Words in the title or description, e.g. `3+1`, `garaz`, `Skoda` |
| `electronicOnly` | `false` | Only auctions you can bid on online through the portal |
| `maxResults` | 0 (no limit) | Cap on saved auctions; use 10-20 for a quick look |

Filters are applied before saving, so you only pay for auctions that match.

## Output sample

One item per auction. This is a real record from a test run (a finished flat auction in Prague, description shortened):

```json
{
    "listing": "finished",
    "auctionId": "YkrR0",
    "auctionNumber": "101EX01210/24-137",
    "url": "https://www.portaldrazeb.cz/drazba/101ex01210-24-137-ykrr0",
    "title": "Bytová jednotka Praha Kamýk",
    "category": "Byt",
    "categoryEn": "Flat / apartment",
    "itemType": "real",
    "auctionType": "execution",
    "electronic": true,
    "status": "finished",
    "startAt": "2026-09-10T08:00:00.000+00:00",
    "endAt": "2026-09-10T09:31:38.000+00:00",
    "publishedAt": "2026-07-31T13:58:37.000+00:00",
    "currency": "CZK",
    "estimatedPrice": 8625000,
    "minimumBid": 5750000,
    "minimumBidPctOfEstimate": 66.7,
    "bidIncrement": 10000,
    "currentPrice": 7050000,
    "cautionDeposit": 575000,
    "repeatedAuction": false,
    "region": "Hlavní město Praha",
    "district": "Praha",
    "city": "Praha",
    "address": "Hodkovická 767/7, Kamýk, Praha",
    "latitude": 50.0217302,
    "longitude": 14.4404411,
    "description": "Bytová jednotka č. 767/5 se nachází v budově č.p. 767 ve 4. NP a její dispozice je 3+1. ...",
    "images": [
        "https://www.portaldrazeb.cz/upload/auction-image/me1Za",
        "https://www.portaldrazeb.cz/upload/auction-image/B0R9p"
    ],
    "documents": [
        { "type": "auction_decree", "typeLabel": "Auction decree (dražební vyhláška)", "url": "https://www.portaldrazeb.cz/upload/auction-document/ee3n7" },
        { "type": "expert_report", "typeLabel": "Expert valuation report (znalecký posudek)", "url": "https://www.portaldrazeb.cz/upload/auction-document/z3PXW" },
        { "type": "resolution_award", "typeLabel": "Award resolution (usnesení o příklepu)", "url": "https://www.portaldrazeb.cz/upload/auction-document/pyk9e" }
    ],
    "auctioneerOffice": { "name": "Vlček Daniel Mgr.", "officeNumber": "101" },
    "scrapedAt": "2026-09-25T05:31:26.675Z"
}
```

`currentPrice` is the running price for ongoing auctions and the final price for finished ones; it's empty for upcoming auctions.

### Field fill rates (real test run, all 818 upcoming + finished auctions)

| Field | Fill rate |
|---|---|
| ID, file number, URL, title, category, status, start date, appraisal, minimum bid, description, documents | 100% |
| region, district, city | 97-98% |
| latitude / longitude | 96% |
| photos | 81% |
| auction end time, caution deposit | 70% |
| street address | 34% (many executors publish only the municipality) |
| bid increment | 20% (set for online auctions) |

## Price

**$3.00 per 1,000 results** (one result = one auction saved). Every upcoming auction in Czechia (~800) costs about $2.40; a daily alert for flats and houses in one city (5-15 new matches) is a few cents a day. Apify's free plan includes $5 of monthly platform credit, so you can try it without paying anything.

## Limits

- Portál dražeb only. Auctions published only on other Czech portals (voluntary-auction or insolvency sites) aren't included.
- Descriptions are in Czech, as the executor wrote them. Categories are translated to English.
- Street addresses are optional for executors; region, district, city and coordinates are nearly always there.
- Documents are links, not parsed text. File names are left out because they sometimes contain the debtor's name.
- The finished list is short-lived on the portal. Schedule daily runs if you want a history of final prices.
- The actor collects public listing data only. Bidding requires a verified account on the portal and is not part of this tool.

## Daily "new auctions" feed

Schedule the actor once a day with your filters and keep the `auctionId`s you've already seen (a CSV, a Google Sheet or an Apify key-value store). Anything with a new ID is new. Apify can push results to Slack, email, Make, Zapier or n8n through its integrations.

## Links

- Actor on Apify Store: https://apify.com/rel8ble/portal-drazeb-scraper
- Apify Python client docs: https://docs.apify.com/api/client/python/
- Apify Store: https://apify.com/store
