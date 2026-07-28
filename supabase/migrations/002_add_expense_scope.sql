-- Migration 002: Add expense scope column
-- Target: Supabase PostgreSQL

ALTER TABLE expenses ADD COLUMN IF NOT EXISTS scope TEXT DEFAULT 'SHARED';
