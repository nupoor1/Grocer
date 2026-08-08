from datetime import date, datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from db import get_connection
from quantity import extract_quantity

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


class Offer(BaseModel):
    item_id: int
    merchant: str
    current_price: float
    original_price: Optional[float]
    is_deal: bool
    discount_pct: Optional[float]
    vs_own_history_pct: Optional[float]
    vs_statcan_pct: Optional[float]
    composite_score: Optional[float]
    image_url: Optional[str]
    price_per_unit: Optional[float]
    unit_label: Optional[str]
    source: str
    sale_story: Optional[str]
    valid_from: Optional[date]
    valid_to: Optional[date]


class ProductResult(BaseModel):
    name: str
    grouped: bool
    group_id: Optional[int]
    offers: list[Offer]


class DealObservation(BaseModel):
    item_id: int
    group_id: Optional[int]
    item_name: str
    merchant: str
    current_price: float
    original_price: Optional[float]
    is_deal: bool
    discount_pct: Optional[float]
    vs_own_history_pct: Optional[float]
    vs_statcan_pct: Optional[float]
    composite_score: Optional[float]
    image_url: Optional[str]
    store_count: int
    price_per_unit: Optional[float]
    unit_label: Optional[str]
    source: str
    sale_story: Optional[str]
    valid_from: Optional[date]
    valid_to: Optional[date]


class Category(BaseModel):
    search_term: str
    item_count: int


class HistoryPoint(BaseModel):
    merchant: str
    observed_at: datetime
    current_price: float
    source: str


SIGNALS_CTE = """
WITH latest AS (
    SELECT DISTINCT ON (item_id)
        item_id, current_price, original_price, source, sale_story, valid_from, valid_to
    FROM price_observations
    WHERE source = 'ecom'
       OR (source = 'flyer' AND CURRENT_DATE BETWEEN valid_from AND valid_to)
    ORDER BY item_id, observed_at DESC
),
recent_30d AS (
    SELECT item_id, current_price
    FROM price_observations
    WHERE observed_at >= NOW() - INTERVAL '30 days'
      AND current_price IS NOT NULL
),
ranked_30d AS (
    SELECT
        item_id, current_price,
        ROW_NUMBER() OVER (PARTITION BY item_id ORDER BY current_price) AS rn,
        COUNT(*) OVER (PARTITION BY item_id) AS cnt
    FROM recent_30d
),
median_30d AS (
    SELECT item_id, AVG(current_price) AS median_price
    FROM ranked_30d
    WHERE rn IN (FLOOR((cnt + 1) / 2.0), CEIL((cnt + 1) / 2.0))
    GROUP BY item_id
),
statcan_baseline AS (
    SELECT DISTINCT ON (product_category)
        product_category, avg_price
    FROM statcan_prices
    WHERE geography = 'Ontario'
    ORDER BY product_category, ref_month DESC
),
group_counts AS (
    SELECT group_id, COUNT(*) AS cnt
    FROM item_group_map
    GROUP BY group_id
)
"""

SIGNAL_COLUMNS = """
    i.id, i.name, m.name AS merchant_name,
    l.current_price, l.original_price,
    md.median_price, sb.avg_price AS statcan_avg,
    igm.group_id, pg.canonical_name, i.image_url,
    COALESCE(gc.cnt, 1) AS store_count,
    l.source, l.sale_story, l.valid_from, l.valid_to
"""

SIGNAL_JOINS = """
JOIN merchants m ON m.merchant_id = i.merchant_id
JOIN latest l ON l.item_id = i.id
LEFT JOIN median_30d md ON md.item_id = i.id
LEFT JOIN item_group_map igm ON igm.item_id = i.id
LEFT JOIN product_groups pg ON pg.id = igm.group_id
LEFT JOIN product_group_statcan_map pgsm ON pgsm.group_id = igm.group_id
LEFT JOIN statcan_baseline sb ON sb.product_category = pgsm.statcan_category
LEFT JOIN group_counts gc ON gc.group_id = igm.group_id
"""

MATCHING_ITEMS_QUERY = (
    SIGNALS_CTE
    + f"SELECT {SIGNAL_COLUMNS} FROM items i {SIGNAL_JOINS} WHERE i.name ILIKE %s"
)

GROUP_MEMBERS_QUERY = (
    SIGNALS_CTE
    + f"""
SELECT {SIGNAL_COLUMNS}
FROM item_group_map igm_filter
JOIN items i ON i.id = igm_filter.item_id
{SIGNAL_JOINS}
WHERE igm_filter.group_id = ANY(%s)
"""
)

ALL_ITEMS_QUERY = SIGNALS_CTE + f"SELECT {SIGNAL_COLUMNS} FROM items i {SIGNAL_JOINS}"


def compute_signals(current_price, original_price, median_30d, statcan_avg):
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
    vs_own_history_pct = (
        round((median_30d - current_price) / median_30d * 100, 1)
        if median_30d is not None and median_30d > 0
        else None
    )
    vs_statcan_pct = (
        round((statcan_avg - current_price) / statcan_avg * 100, 1)
        if statcan_avg is not None and statcan_avg > 0
        else None
    )

    available = [s for s in (discount_pct, vs_own_history_pct, vs_statcan_pct) if s is not None]
    composite_score = round(sum(available) / len(available), 1) if available else None

    return is_deal, discount_pct, vs_own_history_pct, vs_statcan_pct, composite_score


def compute_price_per_unit(name, current_price):
    if current_price is None:
        return None, None
    quantity = extract_quantity(name)
    if quantity is None:
        return None, None
    value, dimension = quantity
    if value <= 0:
        return None, None
    per_100 = round(float(current_price) / value * 100, 3)
    return per_100, ("100g" if dimension == "mass" else "100mL")


def rows_to_products(rows):
    buckets = {}
    for (item_id, name, merchant_name, current_price, original_price, median_30d, statcan_avg,
         group_id, canonical_name, image_url, store_count,
         source, sale_story, valid_from, valid_to) in rows:
        key = ("group", group_id) if group_id is not None else ("item", item_id)
        if key not in buckets:
            buckets[key] = {
                "name": canonical_name if group_id is not None else name,
                "grouped": group_id is not None,
                "group_id": group_id,
                "offers": [],
            }

        is_deal, discount_pct, vs_own_history_pct, vs_statcan_pct, composite_score = compute_signals(
            current_price, original_price, median_30d, statcan_avg
        )
        price_per_unit, unit_label = compute_price_per_unit(name, current_price)
        buckets[key]["offers"].append(
            Offer(
                item_id=item_id,
                merchant=merchant_name,
                current_price=current_price,
                original_price=original_price,
                is_deal=is_deal,
                discount_pct=discount_pct,
                vs_own_history_pct=vs_own_history_pct,
                vs_statcan_pct=vs_statcan_pct,
                composite_score=composite_score,
                image_url=image_url,
                price_per_unit=price_per_unit,
                unit_label=unit_label,
                source=source,
                sale_story=sale_story,
                valid_from=valid_from,
                valid_to=valid_to,
            )
        )

    results = []
    for bucket in buckets.values():
        bucket["offers"].sort(key=lambda o: o.current_price)
        results.append(ProductResult(**bucket))
    return results


@app.get("/api/search", response_model=list[ProductResult])
def search(q: str = Query(..., min_length=1)):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(MATCHING_ITEMS_QUERY, (f"%{q}%",))
        rows = cur.fetchall()

        matched_group_ids = {row[7] for row in rows if row[7] is not None}
        if matched_group_ids:
            cur.execute(GROUP_MEMBERS_QUERY, (list(matched_group_ids),))
            rows += cur.fetchall()
    conn.close()

    rows = list({row[0]: row for row in rows}.values())

    results = rows_to_products(rows)
    results.sort(key=lambda r: r.offers[0].current_price)
    return results


PRODUCT_BY_ITEM_QUERY = SIGNALS_CTE + f"SELECT {SIGNAL_COLUMNS} FROM items i {SIGNAL_JOINS} WHERE i.id = %s"


@app.get("/api/product", response_model=ProductResult)
def product(group_id: Optional[int] = None, item_id: Optional[int] = None):
    if (group_id is None) == (item_id is None):
        raise HTTPException(400, "Provide exactly one of group_id or item_id")

    conn = get_connection()
    with conn.cursor() as cur:
        if group_id is not None:
            cur.execute(GROUP_MEMBERS_QUERY, ([group_id],))
        else:
            cur.execute(PRODUCT_BY_ITEM_QUERY, (item_id,))
        rows = cur.fetchall()
    conn.close()

    products = rows_to_products(rows)
    if not products:
        raise HTTPException(404, "Product not found")
    return products[0]


@app.get("/api/deals", response_model=list[DealObservation])
def best_deals(limit: int = Query(20, ge=1, le=100)):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(ALL_ITEMS_QUERY)
        rows = cur.fetchall()
    conn.close()

    deals = []
    for (item_id, name, merchant_name, current_price, original_price, median_30d, statcan_avg,
         group_id, canonical_name, image_url, store_count,
         source, sale_story, valid_from, valid_to) in rows:
        is_deal, discount_pct, vs_own_history_pct, vs_statcan_pct, composite_score = compute_signals(
            current_price, original_price, median_30d, statcan_avg
        )
        price_per_unit, unit_label = compute_price_per_unit(name, current_price)
        deals.append(
            DealObservation(
                item_id=item_id,
                group_id=group_id,
                item_name=canonical_name if group_id is not None else name,
                merchant=merchant_name,
                current_price=current_price,
                original_price=original_price,
                is_deal=is_deal,
                discount_pct=discount_pct,
                vs_own_history_pct=vs_own_history_pct,
                vs_statcan_pct=vs_statcan_pct,
                composite_score=composite_score,
                image_url=image_url,
                store_count=store_count,
                price_per_unit=price_per_unit,
                unit_label=unit_label,
                source=source,
                sale_story=sale_story,
                valid_from=valid_from,
                valid_to=valid_to,
            )
        )

    deals.sort(key=lambda d: d.composite_score if d.composite_score is not None else float("-inf"), reverse=True)
    return deals[:limit]


HISTORY_BY_GROUP_QUERY = """
SELECT m.name, po.observed_at, po.current_price, po.source
FROM item_group_map igm
JOIN items i ON i.id = igm.item_id
JOIN merchants m ON m.merchant_id = i.merchant_id
JOIN price_observations po ON po.item_id = i.id
WHERE igm.group_id = %s AND po.current_price IS NOT NULL
ORDER BY po.observed_at
"""

HISTORY_BY_ITEM_QUERY = """
SELECT m.name, po.observed_at, po.current_price, po.source
FROM items i
JOIN merchants m ON m.merchant_id = i.merchant_id
JOIN price_observations po ON po.item_id = i.id
WHERE i.id = %s AND po.current_price IS NOT NULL
ORDER BY po.observed_at
"""


@app.get("/api/history", response_model=list[HistoryPoint])
def history(group_id: Optional[int] = None, item_id: Optional[int] = None):
    if (group_id is None) == (item_id is None):
        raise HTTPException(400, "Provide exactly one of group_id or item_id")

    query, param = (HISTORY_BY_GROUP_QUERY, group_id) if group_id is not None else (HISTORY_BY_ITEM_QUERY, item_id)

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(query, (param,))
        rows = cur.fetchall()
    conn.close()

    return [
        HistoryPoint(merchant=merchant, observed_at=observed_at, current_price=current_price, source=source)
        for merchant, observed_at, current_price, source in rows
    ]


CATEGORIES_QUERY = """
SELECT search_term, COUNT(*)
FROM items
WHERE search_term IS NOT NULL
GROUP BY search_term
ORDER BY search_term
"""


@app.get("/api/categories", response_model=list[Category])
def categories():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(CATEGORIES_QUERY)
        rows = cur.fetchall()
    conn.close()
    return [Category(search_term=term, item_count=count) for term, count in rows]


FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
