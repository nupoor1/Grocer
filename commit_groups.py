import csv
from collections import defaultdict

from db import get_connection

CANDIDATES_CSV = "candidate_groups.csv"


def load_reviewed_groups():
    groups = defaultdict(list)
    with open(CANDIDATES_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["approved"].strip().lower() == "y":
                groups[int(row["group_id"])].append(row)
    return {gid: rows for gid, rows in groups.items() if len(rows) >= 2}


def canonical_name(rows):
    return min((r["name"] for r in rows), key=len)


def main():
    groups = load_reviewed_groups()

    conn = get_connection()
    committed = 0
    with conn.cursor() as cur:
        for gid, rows in groups.items():
            cur.execute(
                "INSERT INTO product_groups (canonical_name) VALUES (%s) RETURNING id",
                (canonical_name(rows),),
            )
            group_id = cur.fetchone()[0]

            for row in rows:
                cur.execute(
                    """
                    INSERT INTO item_group_map (item_id, group_id)
                    VALUES (%s, %s)
                    ON CONFLICT (item_id) DO UPDATE SET group_id = EXCLUDED.group_id
                    """,
                    (int(row["item_id"]), group_id),
                )
            committed += 1

    conn.commit()
    conn.close()
    print(f"Committed {committed} product groups from {CANDIDATES_CSV}.")


if __name__ == "__main__":
    main()
