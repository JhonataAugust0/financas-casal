-- schema.sql (updated — reflects the full schema used by the application)

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    income REAL DEFAULT 0.0,
    emergency_multiplier INTEGER DEFAULT 9,
    allowance REAL DEFAULT 500.0
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    name TEXT NOT NULL,
    type TEXT CHECK(type IN ('FIXED', 'PERIODIC')),
    value REAL NOT NULL,
    frequency_months INTEGER DEFAULT 1,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT DEFAULT 'Geral',
    target_value REAL NOT NULL,
    current_value REAL DEFAULT 0.0,
    priority INTEGER NOT NULL,
    link TEXT DEFAULT ''
);

-- Seed data: initial couple
INSERT OR IGNORE INTO users (id, name, income, emergency_multiplier, allowance) VALUES ('A', 'Docinho', 1415.0, 9, 500.0);
INSERT OR IGNORE INTO users (id, name, income, emergency_multiplier, allowance) VALUES ('B', 'Gracinha', 1710.0, 9, 500.0);