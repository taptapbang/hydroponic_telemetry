-- src/schema_setup.sql

-- list of growth phases
CREATE TYPE crop_stage AS ENUM (
    'germinating',
    'seedling',
    'vegetative',
    'flowering',
    'fruiting',
    'harvested',
    'failed'
);

-- Crops table, uses ENUM
CREATE TABLE crops (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    planted_date DATE NOT NULL,
    harvested_date DATE,
    status crop_stage DEFAULT 'germinating'
);

-- Sensor readings table, zulu timestamps
CREATE TABLE sensor_readings (
    id SERIAL PRIMARY KEY,
    crop_id INTEGER REFERENCES crops(id),
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    temperature FLOAT,
    ph FLOAT,
    ec FLOAT
);

-- CV snapshots table
CREATE TABLE snapshots (
    id SERIAL PRIMARY KEY,
    crop_id INTEGER REFERENCES crops(id),
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    image_path VARCHAR(255) NOT NULL,
    notes TEXT
);

-- setup dashboard indices
CREATE INDEX idx_readings_crop_time ON sensor_readings(crop_id, timestamp DESC);
CREATE INDEX idx_snapshots_crop_time ON snapshots(crop_id, timestamp DESC);
