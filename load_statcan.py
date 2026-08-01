import pandas as pd
from psycopg2.extras import execute_values

from db import get_connection

CSV_PATH = "statcan_data/18100245.csv"
GEOGRAPHIES = ["Ontario", "Canada"]

UPSERT_QUERY = """
INSERT INTO statcan_prices (product_category, geography, ref_month, avg_price)
VALUES %s
ON CONFLICT (product_category, geography, ref_month)
DO UPDATE SET avg_price = EXCLUDED.avg_price
"""


def main():
    df = pd.read_csv(CSV_PATH, usecols=["REF_DATE", "GEO", "Products", "VALUE"])
    df = df[df["GEO"].isin(GEOGRAPHIES)].copy()
    df["ref_month"] = pd.to_datetime(df["REF_DATE"], format="%Y-%m").dt.date

    rows = list(
        df[["Products", "GEO", "ref_month", "VALUE"]].itertuples(index=False, name=None)
    )

    conn = get_connection()
    with conn.cursor() as cur:
        execute_values(cur, UPSERT_QUERY, rows, page_size=1000)
    conn.commit()
    conn.close()

    print(f"Upserted {len(rows)} StatCan price rows ({', '.join(GEOGRAPHIES)}).")


if __name__ == "__main__":
    main()
