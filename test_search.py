import requests

from db import get_connection

BASE_URL = "http://127.0.0.1:8000"

TEST_QUERIES = ["Bach Crab Apple", "Villaggio", "Tim Hortons", "Bob's Red Mill", "flour", "coffee"]


def independent_min_price(group_id):
    """Recompute the cheapest offer directly from the DB, bypassing main.py entirely,
    so this is a true independent check, not just re-testing the same code path."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH latest AS (
                SELECT DISTINCT ON (item_id) item_id, current_price
                FROM price_observations
                WHERE source = 'ecom'
                   OR (source = 'flyer' AND CURRENT_DATE BETWEEN valid_from AND valid_to)
                ORDER BY item_id, observed_at DESC
            )
            SELECT MIN(l.current_price)
            FROM item_group_map igm
            JOIN latest l ON l.item_id = igm.item_id
            WHERE igm.group_id = %s
            """,
            (group_id,),
        )
        result = cur.fetchone()[0]
    conn.close()
    return float(result) if result is not None else None


def main():
    failures = 0
    checks = 0

    for query in TEST_QUERIES:
        resp = requests.get(f"{BASE_URL}/search", params={"q": query})
        resp.raise_for_status()
        results = resp.json()

        # check 1: within each product, offers must be non-decreasing by price
        for product in results:
            prices = [o["current_price"] for o in product["offers"]]
            checks += 1
            if prices != sorted(prices):
                print(f"FAIL offers not sorted within '{product['name']}': {prices}")
                failures += 1

        # check 2: the list of products itself must be non-decreasing by cheapest offer
        cheapest_per_product = [p["offers"][0]["current_price"] for p in results]
        checks += 1
        if cheapest_per_product != sorted(cheapest_per_product):
            print(f"FAIL products not sorted cheapest-first for query '{query}'")
            failures += 1

        # check 3: independently verify the top result's cheapest price against raw SQL,
        # for any grouped product in this query's results
        for product in results:
            if not product["grouped"]:
                continue
            expected = independent_min_price(product["group_id"])
            actual = product["offers"][0]["current_price"]
            checks += 1
            if expected is not None and abs(expected - actual) > 0.001:
                print(f"FAIL cheapest mismatch for '{product['name']}': API says {actual}, DB says {expected}")
                failures += 1

        print(f"'{query}': {len(results)} products, top result = {results[0]['name']} @ ${results[0]['offers'][0]['current_price']}" if results else f"'{query}': no results")

    print(f"\n{checks - failures}/{checks} checks passed")


if __name__ == "__main__":
    main()
