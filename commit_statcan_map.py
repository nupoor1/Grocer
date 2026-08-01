import csv

from db import get_connection

CANDIDATES_CSV = "statcan_candidates.csv"


def load_chosen_mapping():
    mapping = {}
    with open(CANDIDATES_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["search_term"] and row["chosen"].strip().lower() == "y":
                mapping[row["search_term"]] = row["candidate_category"]
    return mapping


def main():
    mapping = load_chosen_mapping()

    conn = get_connection()
    committed = 0
    with conn.cursor() as cur:
        for search_term, category in mapping.items():
            cur.execute(
                """
                SELECT DISTINCT igm.group_id
                FROM item_group_map igm
                JOIN items i ON i.id = igm.item_id
                WHERE i.search_term = %s
                """,
                (search_term,),
            )
            group_ids = [row[0] for row in cur.fetchall()]

            for group_id in group_ids:
                cur.execute(
                    """
                    INSERT INTO product_group_statcan_map (group_id, statcan_category)
                    VALUES (%s, %s)
                    ON CONFLICT (group_id) DO UPDATE SET statcan_category = EXCLUDED.statcan_category
                    """,
                    (group_id, category),
                )
                committed += 1

            print(f"{search_term:20s} -> {category:35s} ({len(group_ids)} groups)")

    conn.commit()
    conn.close()
    print(f"\nCommitted {committed} product_group_statcan_map rows across {len(mapping)} search terms.")


if __name__ == "__main__":
    main()
