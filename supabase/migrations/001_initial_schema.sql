-- =============================================================
-- Migration 001: Initial Schema
-- Target: Supabase PostgreSQL
-- =============================================================
-- This migration creates the full schema from scratch.
-- Run this in the Supabase SQL Editor or via the Supabase CLI.

-- ─── Users ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    income DOUBLE PRECISION DEFAULT 0.0,
    emergency_multiplier INTEGER DEFAULT 9,
    allowance DOUBLE PRECISION DEFAULT 500.0
);

-- ─── Expenses ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS expenses (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    name TEXT NOT NULL,
    type TEXT CHECK (type IN ('FIXED', 'PERIODIC')),
    value DOUBLE PRECISION NOT NULL,
    frequency_months INTEGER DEFAULT 1
);

-- ─── Goals ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS goals (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT DEFAULT 'Geral',
    target_value DOUBLE PRECISION NOT NULL,
    current_value DOUBLE PRECISION DEFAULT 0.0,
    priority INTEGER NOT NULL,
    link TEXT DEFAULT ''
);

-- ─── Seed Data ────────────────────────────────────────────────
INSERT INTO users (id, name, income, emergency_multiplier, allowance)
VALUES ('A', 'Docinho', 1415.0, 9, 500.0)
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (id, name, income, emergency_multiplier, allowance)
VALUES ('B', 'Gracinha', 1710.0, 9, 500.0)
ON CONFLICT (id) DO NOTHING;

-- ─── Row Level Security (RLS) ─────────────────────────────────
-- NOTE: For a public MVP without auth, RLS is disabled.
-- Enable and configure policies when you add Supabase Auth.
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;

-- Allow all operations for now (anon key)
CREATE POLICY "Allow all on users" ON users FOR ALL USING (true);
CREATE POLICY "Allow all on expenses" ON expenses FOR ALL USING (true);
CREATE POLICY "Allow all on goals" ON goals FOR ALL USING (true);
