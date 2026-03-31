-- ARIA Disaster Response — AlloyDB AI Schema
-- Run this once to initialise the database

-- Enable pgvector extension (AlloyDB AI supports this natively)
CREATE EXTENSION IF NOT EXISTS vector;

-- ─── Shelters ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS shelters (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    region          TEXT NOT NULL,
    country         TEXT NOT NULL,
    latitude        FLOAT NOT NULL,
    longitude       FLOAT NOT NULL,
    capacity        INTEGER DEFAULT 0,
    current_occupancy INTEGER DEFAULT 0,
    has_medical     BOOLEAN DEFAULT FALSE,
    has_food        BOOLEAN DEFAULT FALSE,
    has_water       BOOLEAN DEFAULT FALSE,
    disaster_types  TEXT[],                 -- e.g. ARRAY['flood','earthquake']
    contact_phone   TEXT,
    embedding       VECTOR(768),            -- AlloyDB AI semantic embedding
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- ─── Hospitals ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS hospitals (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    region          TEXT NOT NULL,
    country         TEXT NOT NULL,
    latitude        FLOAT NOT NULL,
    longitude       FLOAT NOT NULL,
    emergency_beds  INTEGER DEFAULT 0,
    contact_phone   TEXT,
    contact_email   TEXT,
    embedding       VECTOR(768),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- ─── Emergency Contacts ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS emergency_contacts (
    id              SERIAL PRIMARY KEY,
    agency          TEXT NOT NULL,          -- e.g. "NDRF", "Police", "Ambulance"
    region          TEXT NOT NULL,
    country         TEXT NOT NULL,
    disaster_types  TEXT[],
    phone           TEXT,
    email           TEXT,
    description     TEXT,
    embedding       VECTOR(768),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- ─── Indexes for vector similarity search ────────────────────────────────────
CREATE INDEX IF NOT EXISTS shelters_embedding_idx
    ON shelters USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS hospitals_embedding_idx
    ON hospitals USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS contacts_embedding_idx
    ON emergency_contacts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ─── Indexes for region-based fast lookup ────────────────────────────────────
CREATE INDEX IF NOT EXISTS shelters_region_idx ON shelters (region, country);
CREATE INDEX IF NOT EXISTS hospitals_region_idx ON hospitals (region, country);
CREATE INDEX IF NOT EXISTS contacts_region_idx ON emergency_contacts (region, country);
