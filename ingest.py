import time
from datetime import datetime

import requests

from db import get_connection

FLIPP_URL = "https://backflipp.wishabi.com/flipp/items/search"
HEADERS = {"User-Agent": "Mozilla/5.0"}
POSTAL_CODE = "M5V 3L9"

BASKET = [
    "milk", "eggs", "bread", "chicken breast", "bananas", "rice",
    "butter", "cheese", "apples", "potatoes", "onions",
    "pasta", "cereal", "orange juice", "yogurt", "tomatoes", "carrots",
    "lettuce", "ground coffee", "olive oil", "flour", "sugar",
    "canned beans", "frozen vegetables",
]


def fetch_search(term, postal_code):
    params = {"q": term, "postal_code": postal_code}
    resp = requests.get(FLIPP_URL, params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()


def parse_iso_date(value):
    """Flyer validity is an ISO datetime ("2026-07-30T04:00:00+00:00"); the schema
    only needs the date portion."""
    if not value:
        return None
    return datetime.fromisoformat(value).date()


def upsert_merchant(cur, merchant_id, name):
    cur.execute(
        """
        INSERT INTO merchants (merchant_id, name)
        VALUES (%s, %s)
        ON CONFLICT (merchant_id) DO UPDATE SET name = EXCLUDED.name
        """,
        (merchant_id, name),
    )


def upsert_item(cur, sku, name, brand_id, search_term, image_url, merchant_id, postal_code):
    cur.execute(
        """
        INSERT INTO items (sku, name, brand_id, search_term, image_url, merchant_id, postal_code)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (sku, merchant_id, postal_code)
        DO UPDATE SET name = EXCLUDED.name, brand_id = EXCLUDED.brand_id,
            search_term = EXCLUDED.search_term, image_url = EXCLUDED.image_url
        RETURNING id
        """,
        (sku, name, brand_id, search_term, image_url, merchant_id, postal_code),
    )
    return cur.fetchone()[0]


def insert_price_observation(
    cur, item_id, merchant_id, postal_code, current_price, original_price,
    source, sale_story=None, valid_from=None, valid_to=None,
):
    cur.execute(
        """
        INSERT INTO price_observations
            (item_id, merchant_id, postal_code, current_price, original_price,
             source, sale_story, valid_from, valid_to)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (item_id, merchant_id, postal_code, current_price, original_price,
         source, sale_story, valid_from, valid_to),
    )


def ingest_ecom_entry(cur, entry, term, postal_code):
    merchant_id = entry.get("merchant_id")
    merchant_name = entry.get("merchant")
    name = entry.get("name")
    sku = entry.get("sku")
    if merchant_id is None or not name or not sku:
        return False

    brand_ids = entry.get("brand_ids") or []
    brand_id = str(brand_ids[0]) if brand_ids else None
    image_url = entry.get("image_url")

    upsert_merchant(cur, merchant_id, merchant_name)
    item_id = upsert_item(cur, sku, name, brand_id, term, image_url, merchant_id, postal_code)
    insert_price_observation(
        cur, item_id, merchant_id, postal_code,
        entry.get("current_price"), entry.get("original_price"),
        source="ecom",
    )
    return True


def ingest_flyer_entry(cur, entry, term, postal_code):
    # items[] has no "sku" -- "id" (== flyer_item_id) is the closest unique
    # identifier, but it's scoped to a single flyer run rather than a persistent
    # product, so the same physical product gets a new item row each flyer cycle.
    merchant_id = entry.get("merchant_id")
    merchant_name = entry.get("merchant_name")
    name = entry.get("name")
    sku = entry.get("id")
    current_price = entry.get("current_price")
    # Some flyer entries are loyalty-points or percentage-off promos with no dollar
    # price at all (e.g. "SAVE 10%", "Get PC Optimum 10,000 pts") -- unusable for
    # price comparison, so skip rather than store an unpriced row.
    if merchant_id is None or not name or sku is None or current_price is None:
        return False
    sku = str(sku)

    brand_ids = entry.get("brand_ids") or []
    brand_id = str(brand_ids[0]) if brand_ids else None
    image_url = entry.get("clean_image_url")

    upsert_merchant(cur, merchant_id, merchant_name)
    item_id = upsert_item(cur, sku, name, brand_id, term, image_url, merchant_id, postal_code)
    insert_price_observation(
        cur, item_id, merchant_id, postal_code,
        current_price, entry.get("original_price"),
        source="flyer",
        sale_story=entry.get("sale_story"),
        valid_from=parse_iso_date(entry.get("valid_from")),
        valid_to=parse_iso_date(entry.get("valid_to")),
    )
    return True


def main():
    conn = get_connection()
    summary = {}

    for term in BASKET:
        try:
            data = fetch_search(term, POSTAL_CODE)
        except requests.RequestException as e:
            print(f"{term}: request failed ({e})")
            summary[term] = {"ecom": 0, "flyer": 0}
            continue

        ecom_count = 0
        flyer_count = 0
        with conn.cursor() as cur:
            for entry in data.get("ecom_items", []):
                if ingest_ecom_entry(cur, entry, term, POSTAL_CODE):
                    ecom_count += 1
            for entry in data.get("items", []):
                if ingest_flyer_entry(cur, entry, term, POSTAL_CODE):
                    flyer_count += 1

        conn.commit()
        summary[term] = {"ecom": ecom_count, "flyer": flyer_count}
        print(f"{term}: {ecom_count} ecom rows, {flyer_count} flyer rows")
        time.sleep(0.5)

    conn.close()

    print("\n--- summary ---")
    total_ecom = total_flyer = 0
    for term, counts in summary.items():
        print(f"{term:20s} ecom={counts['ecom']:<5d} flyer={counts['flyer']:<5d}")
        total_ecom += counts["ecom"]
        total_flyer += counts["flyer"]
    print(f"{'TOTAL':20s} ecom={total_ecom:<5d} flyer={total_flyer:<5d}")


if __name__ == "__main__":
    main()
