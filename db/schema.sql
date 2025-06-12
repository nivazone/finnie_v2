-- =========================
-- accounts table
-- =========================
CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    account_holder TEXT,
    account_name TEXT,
    account_number TEXT,
    CONSTRAINT unique_accounts UNIQUE (account_holder, account_number)
);

-- =========================
-- transactions table
-- =========================
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    transaction_date TEXT,
    transaction_details TEXT,
    amount NUMERIC(15, 2),
    category TEXT,
    is_tax_deductible BOOLEAN DEFAULT FALSE,
    deductible_portion NUMERIC(5,2) DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

