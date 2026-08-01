CREATE TABLE IF NOT EXISTS merchants (
    merchant_id INT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    sku TEXT NOT NULL,
    name TEXT NOT NULL,
    brand_id TEXT,
    search_term TEXT,
    merchant_id INT NOT NULL REFERENCES merchants(merchant_id),
    postal_code TEXT NOT NULL,
    UNIQUE (sku, merchant_id, postal_code)
);

CREATE INDEX IF NOT EXISTS idx_items_merchant_id ON items(merchant_id);
CREATE INDEX IF NOT EXISTS idx_items_search_term ON items(search_term);
CREATE INDEX IF NOT EXISTS idx_items_postal_code ON items(postal_code);

CREATE TABLE IF NOT EXISTS price_observations (
    id SERIAL PRIMARY KEY,
    item_id INT NOT NULL REFERENCES items(id),
    merchant_id INT NOT NULL REFERENCES merchants(merchant_id),
    postal_code TEXT NOT NULL,
    current_price NUMERIC(10, 2),
    original_price NUMERIC(10, 2),
    source TEXT NOT NULL,
    sale_story TEXT,
    valid_from DATE,
    valid_to DATE,
    observed_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_price_observations_item_id ON price_observations(item_id);
CREATE INDEX IF NOT EXISTS idx_price_observations_merchant_id ON price_observations(merchant_id);
CREATE INDEX IF NOT EXISTS idx_price_observations_postal_code ON price_observations(postal_code);

CREATE TABLE IF NOT EXISTS product_groups (
    id SERIAL PRIMARY KEY,
    canonical_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS item_group_map (
    item_id INT PRIMARY KEY REFERENCES items(id),
    group_id INT NOT NULL REFERENCES product_groups(id)
);

CREATE INDEX IF NOT EXISTS idx_item_group_map_group_id ON item_group_map(group_id);

CREATE TABLE IF NOT EXISTS statcan_prices (
    id SERIAL PRIMARY KEY,
    product_category TEXT NOT NULL,
    geography TEXT NOT NULL,
    ref_month DATE NOT NULL,
    avg_price NUMERIC(10, 2) NOT NULL,
    UNIQUE (product_category, geography, ref_month)
);

CREATE INDEX IF NOT EXISTS idx_statcan_prices_category_geo ON statcan_prices(product_category, geography);

CREATE TABLE IF NOT EXISTS product_group_statcan_map (
    group_id INT PRIMARY KEY REFERENCES product_groups(id),
    statcan_category TEXT NOT NULL
);
