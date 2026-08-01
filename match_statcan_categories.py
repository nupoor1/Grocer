import csv

from rapidfuzz import process, fuzz

from db import get_connection

CANDIDATES_CSV = "statcan_candidates.csv"
TOP_N = 5


def load_search_terms():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT search_term FROM items ORDER BY search_term")
        terms = [row[0] for row in cur.fetchall()]
    conn.close()
    return terms


def load_statcan_categories():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT product_category FROM statcan_prices ORDER BY product_category")
        categories = [row[0] for row in cur.fetchall()]
    conn.close()
    return categories


def main():
    search_terms = load_search_terms()
    categories = load_statcan_categories()

    rows = []
    for term in search_terms:
        matches = process.extract(term, categories, scorer=fuzz.WRatio, limit=TOP_N)
        print(f"\n'{term}':")
        for category, score, _ in matches:
            print(f"    {score:5.1f}  {category}")
            rows.append({"search_term": term, "candidate_category": category, "score": round(score, 1), "chosen": ""})

    with open(CANDIDATES_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["search_term", "candidate_category", "score", "chosen"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} candidate rows ({len(search_terms)} search terms x top {TOP_N}) to {CANDIDATES_CSV}")


if __name__ == "__main__":
    main()
