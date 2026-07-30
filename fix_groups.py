"""One-off manual correction for 3 groups that survived CSV review with
variant-word false positives (whole wheat vs white bread, flavor mismatches,
all-purpose vs 1-to-1 flour). Run once; not part of the regular pipeline."""

from db import get_connection

# items to pull OUT of their group entirely (become ungrouped singletons again)
UNGROUP_ITEM_IDS = [
    211,  # Walmart Villaggio Artesano White -- different line than the London Drugs match
    217,  # Walmart Villaggio Whole Wheat -- wrong bread type for group 7 (White)
    278,  # Healthy Planet Ezekiel Cinnamon Raisin -- flavor mismatch for group 8 (Whole Grain)
    290,  # Healthy Planet Ezekiel Flax -- flavor mismatch
    291,  # Healthy Planet Ezekiel Sesame -- flavor mismatch
]

# group 64 was merging two distinct flour formulations at the same size; split
# the "1 to 1" pair out into a new group, leave "All Purpose" pair in group 64
SPLIT_OUT_ITEM_IDS = [2180, 2198]  # Walmart + Healthy Planet "1 To 1" flour
SPLIT_NEW_CANONICAL_NAME = "Bob's Red Mill Gluten Free 1 To 1 Baking Flour 624g"
GROUP_64_NEW_CANONICAL_NAME = "Bob's Red Mill All Purpose Baking Flour Gluten Free 624g"


def main():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM item_group_map WHERE item_id = ANY(%s)", (UNGROUP_ITEM_IDS,)
        )
        print(f"Ungrouped {cur.rowcount} items from groups 7 and 8.")

        cur.execute(
            "INSERT INTO product_groups (canonical_name) VALUES (%s) RETURNING id",
            (SPLIT_NEW_CANONICAL_NAME,),
        )
        new_group_id = cur.fetchone()[0]
        cur.execute(
            "UPDATE item_group_map SET group_id = %s WHERE item_id = ANY(%s)",
            (new_group_id, SPLIT_OUT_ITEM_IDS),
        )
        print(f"Split '1 to 1' flour pair into new group {new_group_id}.")

        cur.execute(
            "UPDATE product_groups SET canonical_name = %s WHERE id = 64",
            (GROUP_64_NEW_CANONICAL_NAME,),
        )
        # groups 7 and 8 lost the member their canonical_name was originally picked from
        cur.execute(
            "UPDATE product_groups SET canonical_name = %s WHERE id = 7",
            ("Villaggio Bread - Italian Style in White Size 510g",),
        )
        cur.execute(
            "UPDATE product_groups SET canonical_name = %s WHERE id = 8",
            ("Food For Life Bread Ezekiel 4:9 Whole Grain 680g - Organic and Vegan",),
        )

    conn.commit()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
