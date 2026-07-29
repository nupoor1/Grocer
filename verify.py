from db import get_connection

conn = get_connection()
with conn.cursor() as cur:
    cur.execute(
        """
        SELECT m.name, COUNT(*) AS item_count
        FROM items i
        JOIN merchants m ON m.merchant_id = i.merchant_id
        GROUP BY m.name
        ORDER BY item_count DESC
        """
    )
    print(f"{'merchant':30s} {'items':>6s}")
    for name, count in cur.fetchall():
        print(f"{name:30s} {count:6d}")

    cur.execute("SELECT COUNT(*) FROM items")
    print(f"\ntotal distinct items: {cur.fetchone()[0]}")

    cur.execute("SELECT COUNT(*) FROM price_observations")
    print(f"total price observations: {cur.fetchone()[0]}")

conn.close()
