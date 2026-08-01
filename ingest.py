import time

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


def fetch_ecom_items(term, postal_code):
    params = {"q": term, "postal_code": postal_code}
    resp = requests.get(FLIPP_URL, params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json().get("ecom_items", [])


def upsert_merchant(cur, merchant_id, name):
    cur.execute(
        """
        INSERT INTO merchants (merchant_id, name)
        VALUES (%s, %s)
        ON CONFLICT (merchant_id) DO UPDATE SET name = EXCLUDED.name
        """,
        (merchant_id, name),
    )


def upsert_item(cur, sku, name, brand_id, search_term, merchant_id, postal_code):
    cur.execute(
        """
        INSERT INTO items (sku, name, brand_id, search_term, merchant_id, postal_code)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (sku, merchant_id, postal_code)
        DO UPDATE SET name = EXCLUDED.name, brand_id = EXCLUDED.brand_id, search_term = EXCLUDED.search_term
        RETURNING id
        """,
        (sku, name, brand_id, search_term, merchant_id, postal_code),
    )
    return cur.fetchone()[0]


def insert_price_observation(cur, item_id, merchant_id, postal_code, current_price, original_price):
    cur.execute(
        """
        INSERT INTO price_observations
            (item_id, merchant_id, postal_code, current_price, original_price, source)
        VALUES (%s, %s, %s, %s, %s, 'ecom')
        """,
        (item_id, merchant_id, postal_code, current_price, original_price),
    )


def main():
    conn = get_connection()
    summary = {}

    for term in BASKET:
        try:
            ecom_items = fetch_ecom_items(term, POSTAL_CODE)
        except requests.RequestException as e:
            print(f"{term}: request failed ({e})")
            summary[term] = 0
            continue

        count = 0
        with conn.cursor() as cur:
            for entry in ecom_items:
                merchant_id = entry.get("merchant_id")
                merchant_name = entry.get("merchant")
                name = entry.get("name")
                sku = entry.get("sku")
                if merchant_id is None or not name or not sku:
                    continue

                brand_ids = entry.get("brand_ids") or []
                brand_id = str(brand_ids[0]) if brand_ids else None

                upsert_merchant(cur, merchant_id, merchant_name)
                item_id = upsert_item(cur, sku, name, brand_id, term, merchant_id, POSTAL_CODE)
                insert_price_observation(
                    cur,
                    item_id,
                    merchant_id,
                    POSTAL_CODE,
                    entry.get("current_price"),
                    entry.get("original_price"),
                )
                count += 1

        conn.commit()
        summary[term] = count
        print(f"{term}: {count} rows")
        time.sleep(0.5)

    conn.close()

    print("\n--- summary ---")
    total = 0
    for term, count in summary.items():
        print(f"{term:20s} {count}")
        total += count
    print(f"{'TOTAL':20s} {total}")


if __name__ == "__main__":
    main()
