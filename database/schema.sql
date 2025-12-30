-- ============================================================================
-- AmStar Football Platform - Database Schema
-- ============================================================================
-- Core tables for managing Teams, Players, and their relationships
-- ============================================================================

-- Enum types for better type safety and consistency
CREATE TYPE player_position AS ENUM (
    'GOALKEEPER',
    'DEFENDER',
    'MIDFIELDER',
    'FORWARD'
);

CREATE TYPE team_role AS ENUM (
    'CAPTAIN',
    'MEMBER'
);

CREATE TYPE join_request_status AS ENUM (
    'PENDING',
    'APPROVED',
    'REJECTED'
);

CREATE TYPE card_type AS ENUM (
    'YELLOW',
    'RED'
);

-- ============================================================================
-- PLAYERS TABLE
-- ============================================================================
-- Stores core player information and aggregated statistics
CREATE TABLE players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE, -- Reference to auth/user system

    -- Basic Information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    date_of_birth DATE NOT NULL,
    phone VARCHAR(20),

    -- Football-specific attributes
    position player_position NOT NULL,
    preferred_foot VARCHAR(10) CHECK (preferred_foot IN ('LEFT', 'RIGHT', 'BOTH')),

    -- Rating System (0-100 scale)
    skill_rating DECIMAL(5,2) DEFAULT 50.00 CHECK (skill_rating >= 0 AND skill_rating <= 100),

    -- Aggregated Statistics (lifetime stats across all teams)
    total_matches_played INTEGER DEFAULT 0,
    total_goals INTEGER DEFAULT 0,
    total_assists INTEGER DEFAULT 0,
    total_yellow_cards INTEGER DEFAULT 0,
    total_red_cards INTEGER DEFAULT 0,
    total_clean_sheets INTEGER DEFAULT 0, -- For goalkeepers

    -- Metadata
    profile_picture_url TEXT,
    bio TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- ============================================================================
-- TEAMS TABLE
-- ============================================================================
-- Stores team information and performance metrics
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Basic Information
    name VARCHAR(100) NOT NULL UNIQUE,
    short_name VARCHAR(20),
    founded_date DATE,
    home_city VARCHAR(100),

    -- Visual Identity
    logo_url TEXT,
    team_color VARCHAR(7), -- Hex color code (#RRGGBB)

    -- Performance Metrics
    total_matches INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    total_draws INTEGER DEFAULT 0,
    total_losses INTEGER DEFAULT 0,
    total_goals_scored INTEGER DEFAULT 0,
    total_goals_conceded INTEGER DEFAULT 0,

    -- Team Rating (0-100 scale, calculated from player ratings and performance)
    team_rating DECIMAL(5,2) DEFAULT 50.00 CHECK (team_rating >= 0 AND team_rating <= 100),

    -- Settings
    max_players INTEGER DEFAULT 25,
    is_recruiting BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TEAM_MEMBERS TABLE
-- ============================================================================
-- Junction table managing the many-to-many relationship between players and teams
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,

    -- Role in team
    role team_role NOT NULL DEFAULT 'MEMBER',

    -- Player number and position in this specific team
    jersey_number INTEGER CHECK (jersey_number > 0 AND jersey_number <= 99),
    position_in_team player_position,

    -- Team-specific statistics
    matches_played INTEGER DEFAULT 0,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    clean_sheets INTEGER DEFAULT 0,

    -- Metadata
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,

    -- Constraints
    UNIQUE(team_id, player_id),
    UNIQUE(team_id, jersey_number) WHERE is_active = true,

    -- Ensure at least one captain per team (enforced by trigger)
    CHECK (left_at IS NULL OR is_active = false)
);

-- ============================================================================
-- TEAM_JOIN_REQUESTS TABLE
-- ============================================================================
-- Manages the request/approval flow for players joining teams
CREATE TABLE team_join_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,

    -- Request details
    status join_request_status DEFAULT 'PENDING',
    message TEXT, -- Optional message from player to captain

    -- Response details
    reviewed_by UUID REFERENCES players(id), -- Captain who reviewed the request
    review_message TEXT, -- Optional response from captain
    reviewed_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(team_id, player_id, status) WHERE status = 'PENDING',
    CHECK (status = 'PENDING' OR reviewed_by IS NOT NULL)
);

-- ============================================================================
-- MATCH_EVENTS TABLE
-- ============================================================================
-- Tracks individual events in matches for detailed statistics
CREATE TABLE match_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID NOT NULL, -- Reference to matches table (to be created)
    team_id UUID NOT NULL REFERENCES teams(id),
    player_id UUID NOT NULL REFERENCES players(id),

    -- Event details
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('GOAL', 'ASSIST', 'YELLOW_CARD', 'RED_CARD', 'CLEAN_SHEET')),
    minute INTEGER CHECK (minute >= 0 AND minute <= 120),
    description TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Ensure player belongs to the team
    CONSTRAINT fk_team_player FOREIGN KEY (team_id, player_id)
        REFERENCES team_members(team_id, player_id)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Players indexes
CREATE INDEX idx_players_user_id ON players(user_id);
CREATE INDEX idx_players_email ON players(email);
CREATE INDEX idx_players_skill_rating ON players(skill_rating DESC);
CREATE INDEX idx_players_active ON players(is_active);

-- Teams indexes
CREATE INDEX idx_teams_name ON teams(name);
CREATE INDEX idx_teams_rating ON teams(team_rating DESC);
CREATE INDEX idx_teams_recruiting ON teams(is_recruiting) WHERE is_recruiting = true;
CREATE INDEX idx_teams_active ON teams(is_active);

-- Team members indexes
CREATE INDEX idx_team_members_team ON team_members(team_id);
CREATE INDEX idx_team_members_player ON team_members(player_id);
CREATE INDEX idx_team_members_role ON team_members(role);
CREATE INDEX idx_team_members_active ON team_members(team_id, is_active);

-- Join requests indexes
CREATE INDEX idx_join_requests_team ON team_join_requests(team_id);
CREATE INDEX idx_join_requests_player ON team_join_requests(player_id);
CREATE INDEX idx_join_requests_status ON team_join_requests(status);
CREATE INDEX idx_join_requests_pending ON team_join_requests(team_id, status) WHERE status = 'PENDING';

-- Match events indexes
CREATE INDEX idx_match_events_match ON match_events(match_id);
CREATE INDEX idx_match_events_player ON match_events(player_id);
CREATE INDEX idx_match_events_team ON match_events(team_id);

-- ============================================================================
-- TRIGGERS AND FUNCTIONS
-- ============================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_players_updated_at BEFORE UPDATE ON players
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_join_requests_updated_at BEFORE UPDATE ON team_join_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to ensure at least one captain per active team
CREATE OR REPLACE FUNCTION enforce_team_captain()
RETURNS TRIGGER AS $$
BEGIN
    -- When removing a captain or making them inactive
    IF (TG_OP = 'UPDATE' AND OLD.role = 'CAPTAIN' AND
        (NEW.role != 'CAPTAIN' OR NEW.is_active = false)) OR
       (TG_OP = 'DELETE' AND OLD.role = 'CAPTAIN') THEN

        -- Check if this is the last captain
        IF NOT EXISTS (
            SELECT 1 FROM team_members
            WHERE team_id = OLD.team_id
            AND role = 'CAPTAIN'
            AND is_active = true
            AND id != OLD.id
        ) THEN
            RAISE EXCEPTION 'Cannot remove the last captain from team. Assign a new captain first.';
        END IF;
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ensure_team_has_captain
    BEFORE UPDATE OR DELETE ON team_members
    FOR EACH ROW EXECUTE FUNCTION enforce_team_captain();

-- Function to prevent duplicate active memberships
CREATE OR REPLACE FUNCTION prevent_duplicate_team_membership()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_active = true THEN
        IF EXISTS (
            SELECT 1 FROM team_members
            WHERE team_id = NEW.team_id
            AND player_id = NEW.player_id
            AND is_active = true
            AND id != COALESCE(NEW.id, gen_random_uuid())
        ) THEN
            RAISE EXCEPTION 'Player is already an active member of this team';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_duplicate_membership
    BEFORE INSERT OR UPDATE ON team_members
    FOR EACH ROW EXECUTE FUNCTION prevent_duplicate_team_membership();
