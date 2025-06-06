-- =========================
-- statements table
-- =========================
CREATE TABLE IF NOT EXISTS statements (
    id SERIAL PRIMARY KEY,
    account_holder TEXT,
    account_name TEXT,
    start_date TEXT,
    end_date TEXT,
    opening_balance NUMERIC(15, 2),
    closing_balance NUMERIC(15, 2),
    credit_limit NUMERIC(15, 2),
    interest_charged NUMERIC(15, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_statement UNIQUE (account_holder, account_name, start_date, end_date)
);

-- =========================
-- transactions table
-- =========================
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    statement_id INTEGER NOT NULL REFERENCES statements(id) ON DELETE CASCADE,
    transaction_date TEXT,
    transaction_details TEXT,
    amount NUMERIC(15, 2),
    category TEXT,
    is_tax_deductible BOOLEAN DEFAULT FALSE,
    deductible_portion NUMERIC(5,2) DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

