from db import get_connection

QUERY = """
WITH latest AS (
    SELECT DISTINCT ON (item_id)
        item_id, merchant_id, current_price, original_price, observed_at
    FROM price_observations
    ORDER BY item_id, observed_at DESC
)
SELECT
    i.name,
    m.name,
    l.current_price,
    l.original_price,
    ROUND((l.original_price - l.current_price) / l.original_price * 100, 1) AS discount_pct
FROM latest l
JOIN items i ON i.id = l.item_id
JOIN merchants m ON m.merchant_id = l.merchant_id
WHERE l.original_price IS NOT NULL
  AND l.original_price > 0
  AND l.current_price IS NOT NULL
  AND l.current_price < l.original_price
ORDER BY discount_pct DESC
"""

if __name__ == "__main__":
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(QUERY)
        rows = cur.fetchall()
    conn.close()

    print(f"{'item':45s} {'merchant':15s} {'now':>7s} {'was':>7s} {'off':>6s}")
    for name, merchant, current, original, pct in rows:
        print(f"{name[:45]:45s} {merchant:15s} {current:7.2f} {original:7.2f} {pct:5.1f}%")

    print(f"\n{len(rows)} items currently on sale (out of items with any price observation)")
