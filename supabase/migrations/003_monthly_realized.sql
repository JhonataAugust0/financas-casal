-- =============================================================
-- Migration 003: Monthly Realized + Goal Contributions
-- Target: Supabase PostgreSQL
-- =============================================================
-- Tracks actual spending vs budget and actual goal contributions.

-- ─── Monthly Realized (Orçado vs. Realizado) ──────────────────
CREATE TABLE IF NOT EXISTS monthly_realized (
    id BIGSERIAL PRIMARY KEY,
    expense_id BIGINT REFERENCES expenses(id) ON DELETE CASCADE,
    month_year TEXT NOT NULL,
    budgeted_value DOUBLE PRECISION NOT NULL,
    actual_value DOUBLE PRECISION NOT NULL,
    UNIQUE(expense_id, month_year)
);

-- ─── Goal Contributions (Aportes Reais) ───────────────────────
CREATE TABLE IF NOT EXISTS goal_contributions (
    id BIGSERIAL PRIMARY KEY,
    goal_id BIGINT REFERENCES goals(id) ON DELETE CASCADE,
    month_year TEXT NOT NULL,
    planned_amount DOUBLE PRECISION DEFAULT 0.0,
    actual_amount DOUBLE PRECISION NOT NULL,
    UNIQUE(goal_id, month_year)
);

-- ─── Row Level Security (RLS) ─────────────────────────────────
ALTER TABLE monthly_realized ENABLE ROW LEVEL SECURITY;
ALTER TABLE goal_contributions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all on monthly_realized" ON monthly_realized FOR ALL USING (true);
CREATE POLICY "Allow all on goal_contributions" ON goal_contributions FOR ALL USING (true);
