-- ============================================================
-- Database Schema for AmStar Amateur Football Platform
-- PostgreSQL Database Initialization Script
-- ============================================================
-- This schema defines the core tables for organizing amateur
-- football matches and managing teams.
-- ============================================================

-- Drop existing tables if they exist (for clean initialization)
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS teams CASCADE;

-- ============================================================
-- TABLE: teams
-- ============================================================
-- Stores information about amateur football teams
-- Each team can have multiple players (users) and a captain
-- ============================================================

CREATE TABLE teams (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Basic team information
    name VARCHAR(100) NOT NULL UNIQUE,
    city VARCHAR(100),

    -- Team metadata
    description TEXT,
    founded_year INTEGER CHECK (founded_year >= 1800 AND founded_year <= 2100),
    logo_url VARCHAR(255),

    -- Rating system for matchmaking
    rating_score INTEGER DEFAULT 1000 CHECK (rating_score >= 0 AND rating_score <= 5000),

    -- Audit timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance optimization
CREATE INDEX idx_teams_name ON teams(name);
CREATE INDEX idx_teams_city ON teams(city);
CREATE INDEX idx_teams_rating_score ON teams(rating_score DESC);


-- ============================================================
-- TABLE: users
-- ============================================================
-- Stores user accounts (players) in the system
-- Users can be team members, captains, or independent players
-- ============================================================

CREATE TABLE users (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Authentication credentials
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,

    -- User profile information
    full_name VARCHAR(150),
    phone_number VARCHAR(20),

    -- User role in the system
    -- Possible values: 'player', 'captain', 'admin', 'organizer'
    role VARCHAR(20) NOT NULL DEFAULT 'player'
        CHECK (role IN ('player', 'captain', 'admin', 'organizer')),

    -- Team affiliation (Foreign Key)
    -- NULL if user is not affiliated with any team
    team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,

    -- Account status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,

    -- Audit timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Create indexes for performance optimization
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_team_id ON users(team_id);
CREATE INDEX idx_users_role ON users(role);


-- ============================================================
-- FOREIGN KEY RELATIONSHIPS
-- ============================================================
-- users.team_id references teams.id
--   - When a team is deleted, user's team_id is set to NULL
--   - This allows users to exist independently of teams
-- ============================================================


-- ============================================================
-- FUNCTION: Update timestamp automatically
-- ============================================================
-- This function updates the 'updated_at' column automatically
-- whenever a row is modified
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers to automatically update 'updated_at' column
CREATE TRIGGER update_teams_updated_at
    BEFORE UPDATE ON teams
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================================
-- Insert sample teams
INSERT INTO teams (name, city, founded_year, rating_score, description) VALUES
    ('FC Barcelona Amateur', 'Barcelona', 2018, 1850, 'Amateur football team from Barcelona'),
    ('Madrid Warriors', 'Madrid', 2019, 1720, 'Competitive amateur team from Madrid'),
    ('Valencia United', 'Valencia', 2020, 1650, 'Local amateur football club'),
    ('Sevilla Stars', 'Sevilla', 2021, 1580, 'Rising amateur team from Sevilla');

-- Insert sample users (password: 'password123' - hashed with bcrypt)
-- Note: In production, use proper password hashing
INSERT INTO users (email, password_hash, full_name, role, team_id) VALUES
    ('captain1@fcbarcelona.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEg7Iq', 'Juan García', 'captain', 1),
    ('player1@madrid.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEg7Iq', 'Carlos López', 'player', 2),
    ('captain2@valencia.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEg7Iq', 'Miguel Rodríguez', 'captain', 3),
    ('admin@amstar.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEg7Iq', 'Admin User', 'admin', NULL);


-- ============================================================
-- END OF SCHEMA
-- ============================================================
