-- =============================================================
-- Migration 004: Monthly Snapshots (Evolução Patrimonial)
-- Target: Supabase PostgreSQL
-- =============================================================
-- Stores historical snapshots of total couple wealth month-by-month.

CREATE TABLE IF NOT EXISTS monthly_snapshots (
    id BIGSERIAL PRIMARY KEY,
    month_year TEXT NOT NULL UNIQUE,
    reserve_value DOUBLE PRECISION DEFAULT 0.0,
    goals_value DOUBLE PRECISION DEFAULT 0.0,
    total_wealth DOUBLE PRECISION DEFAULT 0.0
);

-- Row Level Security (RLS)
ALTER TABLE monthly_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all on monthly_snapshots" ON monthly_snapshots FOR ALL USING (true);
