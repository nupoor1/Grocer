from collections import defaultdict

from db import get_connection

QUERY = """
SELECT pg.id, pg.canonical_name, m.name, i.name
FROM product_groups pg
JOIN item_group_map igm ON igm.group_id = pg.id
JOIN items i ON i.id = igm.item_id
JOIN merchants m ON m.merchant_id = i.merchant_id
ORDER BY pg.id
"""

if __name__ == "__main__":
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(QUERY)
        rows = cur.fetchall()
    conn.close()

    groups = defaultdict(list)
    for group_id, canonical_name, merchant_name, item_name in rows:
        groups[(group_id, canonical_name)].append((merchant_name, item_name))

    for (group_id, canonical_name), members in groups.items():
        print(f"\n[{group_id}] {canonical_name}")
        for merchant_name, item_name in members:
            print(f"    {merchant_name:20s} {item_name}")

    print(f"\n{len(groups)} groups total")
