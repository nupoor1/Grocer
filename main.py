from typing import Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel

from db import get_connection

app = FastAPI()


class Offer(BaseModel):
    merchant: str
    current_price: float
    original_price: Optional[float]
    is_deal: bool
    discount_pct: Optional[float]


class ProductResult(BaseModel):
    name: str
    grouped: bool
    offers: list[Offer]


SEARCH_QUERY = """
WITH latest AS (
    SELECT DISTINCT ON (item_id)
        item_id, current_price, original_price
    FROM price_observations
    ORDER BY item_id, observed_at DESC
)
SELECT
    i.id,
    i.name,
    m.name AS merchant_name,
    l.current_price,
    l.original_price,
    igm.group_id,
    pg.canonical_name
FROM items i
JOIN merchants m ON m.merchant_id = i.merchant_id
JOIN latest l ON l.item_id = i.id
LEFT JOIN item_group_map igm ON igm.item_id = i.id
LEFT JOIN product_groups pg ON pg.id = igm.group_id
WHERE i.name ILIKE %s
"""


@app.get("/search", response_model=list[ProductResult])
def search(q: str = Query(..., min_length=1)):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(SEARCH_QUERY, (f"%{q}%",))
        rows = cur.fetchall()
    conn.close()

    # bucket rows by group_id when present, otherwise each ungrouped item is its own bucket
    buckets = {}
    for item_id, name, merchant_name, current_price, original_price, group_id, canonical_name in rows:
        key = ("group", group_id) if group_id is not None else ("item", item_id)
        if key not in buckets:
            buckets[key] = {
                "name": canonical_name if group_id is not None else name,
                "grouped": group_id is not None,
                "offers": [],
            }

        is_deal = (
            current_price is not None
            and original_price is not None
            and current_price < original_price
        )
        discount_pct = (
            round((original_price - current_price) / original_price * 100, 1)
            if is_deal and original_price > 0
            else None
        )
        buckets[key]["offers"].append(
            Offer(
                merchant=merchant_name,
                current_price=current_price,
                original_price=original_price,
                is_deal=is_deal,
                discount_pct=discount_pct,
            )
        )

    results = []
    for bucket in buckets.values():
        bucket["offers"].sort(key=lambda o: o.current_price)
        results.append(ProductResult(**bucket))

    results.sort(key=lambda r: r.offers[0].current_price)
    return results
