import csv
from collections import defaultdict

import numpy as np
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering

from db import get_connection
from quantity import extract_quantity, quantity_compatible

CANDIDATES_CSV = "candidate_groups.csv"

FUZZY_PREFILTER_THRESHOLD = 40   # lenient: only rules out obvious non-matches
COSINE_MATCH_THRESHOLD = 0.75    # the real decision boundary — tune this
QUANTITY_TOLERANCE = 0.05        # 623g vs 624g should still count as "the same size"

MODEL_NAME = "all-MiniLM-L6-v2"


def load_items():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT i.id, i.name, i.merchant_id, m.name, i.search_term
            FROM items i
            JOIN merchants m ON m.merchant_id = i.merchant_id
            """
        )
        rows = cur.fetchall()
    conn.close()

    by_term = defaultdict(list)
    for item_id, name, merchant_id, merchant_name, search_term in rows:
        by_term[search_term].append(
            {"id": item_id, "name": name, "merchant_id": merchant_id, "merchant_name": merchant_name}
        )
    return by_term


def cluster_block(items, model):
    n = len(items)
    names = [it["name"] for it in items]
    quantities = [extract_quantity(name) for name in names]
    # rapidfuzz.fuzz.token_sort_ratio is case-sensitive (identical strings differing
    # only in case score ~42, not 100) -- flyer names are often ALL CAPS while ecom
    # names are mixed case, so this stage needs a case-folded view to compare fairly.
    # The embedding stage doesn't need this: all-MiniLM-L6-v2 is an uncased model
    # (cosine similarity 1.0 for the same text in different cases).
    names_for_fuzzy = [name.lower() for name in names]

    # Stage 1: rapidfuzz text pre-filter + quantity gate -> boolean candidate mask
    candidate = np.zeros((n, n), dtype=bool)
    for i in range(n):
        for j in range(i + 1, n):
            score = fuzz.token_sort_ratio(names_for_fuzzy[i], names_for_fuzzy[j])
            if score >= FUZZY_PREFILTER_THRESHOLD and quantity_compatible(quantities[i], quantities[j], QUANTITY_TOLERANCE):
                candidate[i, j] = candidate[j, i] = True

    # Stage 2: embeddings + cosine similarity, only meaningful where stage 1 passed
    embeddings = model.encode(names, normalize_embeddings=True)
    cosine_sim = embeddings @ embeddings.T

    # Build a distance matrix: 1 - similarity where both stages agree it's a match,
    # otherwise "infinitely far apart" (max distance) so they never cluster together.
    distance = np.ones((n, n))
    np.fill_diagonal(distance, 0.0)
    for i in range(n):
        for j in range(i + 1, n):
            if candidate[i, j] and cosine_sim[i, j] >= COSINE_MATCH_THRESHOLD:
                d = 1 - cosine_sim[i, j]
                distance[i, j] = distance[j, i] = d

    if n == 1:
        labels = [0]
    else:
        clustering = AgglomerativeClustering(
            n_clusters=None,
            metric="precomputed",
            linkage="complete",
            distance_threshold=1 - COSINE_MATCH_THRESHOLD,
        )
        labels = clustering.fit_predict(distance)

    groups = defaultdict(list)
    for item, label in zip(items, labels):
        groups[label].append(item)
    return list(groups.values())


def main():
    print(f"Loading model {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    by_term = load_items()
    total_multi_merchant_groups = 0
    csv_rows = []
    next_group_id = 1

    for term, items in by_term.items():
        groups = cluster_block(items, model)
        multi_merchant_groups = [
            g for g in groups if len({it["merchant_id"] for it in g}) > 1
        ]
        if not multi_merchant_groups:
            continue

        print(f"\n=== {term} ({len(items)} items, {len(multi_merchant_groups)} cross-merchant groups) ===")
        for g in multi_merchant_groups:
            total_multi_merchant_groups += 1
            print("  group:")
            for it in g:
                print(f"    [{it['merchant_name']:20s}] {it['name']}")
                csv_rows.append(
                    {
                        "group_id": next_group_id,
                        "item_id": it["id"],
                        "merchant_name": it["merchant_name"],
                        "name": it["name"],
                        "search_term": term,
                        "approved": "y",
                    }
                )
            next_group_id += 1

    print(f"\nTotal cross-merchant candidate groups: {total_multi_merchant_groups}")

    with open(CANDIDATES_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["group_id", "item_id", "merchant_name", "name", "search_term", "approved"]
        )
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"Wrote {len(csv_rows)} candidate rows to {CANDIDATES_CSV} for review.")


if __name__ == "__main__":
    main()
