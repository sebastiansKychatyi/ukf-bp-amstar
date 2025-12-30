-- ============================================================================
-- AmStar Football Platform - Sample Data for Testing
-- ============================================================================
-- This file contains sample data to help you test the application
-- Run this AFTER running schema.sql
-- ============================================================================

-- Sample Players
INSERT INTO players (id, user_id, first_name, last_name, email, date_of_birth, position, preferred_foot, skill_rating, bio) VALUES
    ('11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'Jan', 'Novák', 'jan.novak@example.com', '1995-03-15', 'FORWARD', 'RIGHT', 72.50, 'Experienced striker with great positioning'),
    ('22222222-2222-2222-2222-222222222222', '22222222-2222-2222-2222-222222222222', 'Petr', 'Svoboda', 'petr.svoboda@example.com', '1998-07-22', 'MIDFIELDER', 'BOTH', 68.00, 'Creative midfielder, loves assists'),
    ('33333333-3333-3333-3333-333333333333', '33333333-3333-3333-3333-333333333333', 'Tomáš', 'Dvořák', 'tomas.dvorak@example.com', '1997-11-08', 'DEFENDER', 'LEFT', 65.50, 'Solid defender, great tackling'),
    ('44444444-4444-4444-4444-444444444444', '44444444-4444-4444-4444-444444444444', 'Lukáš', 'Černý', 'lukas.cerny@example.com', '1996-05-30', 'GOALKEEPER', 'RIGHT', 70.00, 'Reliable goalkeeper with quick reflexes'),
    ('55555555-5555-5555-5555-555555555555', '55555555-5555-5555-5555-555555555555', 'Martin', 'Procházka', 'martin.prochazka@example.com', '1999-01-12', 'FORWARD', 'LEFT', 64.00, 'Young talent, fast and agile'),
    ('66666666-6666-6666-6666-666666666666', '66666666-6666-6666-6666-666666666666', 'David', 'Kučera', 'david.kucera@example.com', '1994-09-25', 'MIDFIELDER', 'RIGHT', 71.50, 'Box-to-box midfielder'),
    ('77777777-7777-7777-7777-777777777777', '77777777-7777-7777-7777-777777777777', 'Jakub', 'Veselý', 'jakub.vesely@example.com', '1997-04-18', 'DEFENDER', 'RIGHT', 66.00, 'Fast defender, good at headers'),
    ('88888888-8888-8888-8888-888888888888', '88888888-8888-8888-8888-888888888888', 'Michal', 'Horák', 'michal.horak@example.com', '1998-12-03', 'FORWARD', 'RIGHT', 69.50, 'Clinical finisher');

-- Sample Teams
INSERT INTO teams (id, name, short_name, founded_date, home_city, team_color, total_matches, total_wins, total_draws, total_losses, total_goals_scored, total_goals_conceded, team_rating, description) VALUES
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Thunder FC', 'TFC', '2020-06-15', 'Prague', '#1E40AF', 25, 18, 4, 3, 62, 23, 72.50, 'Competitive amateur team based in Prague'),
    ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Lightning United', 'LTU', '2019-03-20', 'Brno', '#DC2626', 30, 15, 8, 7, 51, 38, 64.00, 'Friendly team looking for new members'),
    ('cccccccc-cccc-cccc-cccc-cccccccccccc', 'Storm Athletic', 'STA', '2021-01-10', 'Ostrava', '#059669', 20, 12, 5, 3, 45, 25, 68.50, 'Young and energetic squad');

-- Team Members (Thunder FC)
INSERT INTO team_members (team_id, player_id, role, jersey_number, position_in_team, matches_played, goals, assists, yellow_cards, red_cards, clean_sheets) VALUES
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '11111111-1111-1111-1111-111111111111', 'CAPTAIN', 10, 'FORWARD', 25, 28, 12, 3, 0, 0),
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '22222222-2222-2222-2222-222222222222', 'MEMBER', 8, 'MIDFIELDER', 25, 8, 18, 5, 0, 0),
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '33333333-3333-3333-3333-333333333333', 'MEMBER', 5, 'DEFENDER', 24, 2, 3, 6, 1, 8),
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '44444444-4444-4444-4444-444444444444', 'MEMBER', 1, 'GOALKEEPER', 25, 0, 0, 1, 0, 12);

-- Team Members (Lightning United)
INSERT INTO team_members (team_id, player_id, role, jersey_number, position_in_team, matches_played, goals, assists, yellow_cards, red_cards, clean_sheets) VALUES
    ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '55555555-5555-5555-5555-555555555555', 'CAPTAIN', 9, 'FORWARD', 30, 22, 8, 4, 0, 0),
    ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '66666666-6666-6666-6666-666666666666', 'MEMBER', 6, 'MIDFIELDER', 28, 12, 15, 7, 0, 0);

-- Team Members (Storm Athletic)
INSERT INTO team_members (team_id, player_id, role, jersey_number, position_in_team, matches_played, goals, assists, yellow_cards, red_cards, clean_sheets) VALUES
    ('cccccccc-cccc-cccc-cccc-cccccccccccc', '77777777-7777-7777-7777-777777777777', 'CAPTAIN', 4, 'DEFENDER', 20, 3, 2, 5, 0, 7),
    ('cccccccc-cccc-cccc-cccc-cccccccccccc', '88888888-8888-8888-8888-888888888888', 'MEMBER', 11, 'FORWARD', 20, 18, 6, 2, 0, 0);

-- Update player lifetime statistics to match team stats
UPDATE players SET
    total_matches_played = 25,
    total_goals = 28,
    total_assists = 12,
    total_yellow_cards = 3,
    total_red_cards = 0
WHERE id = '11111111-1111-1111-1111-111111111111';

UPDATE players SET
    total_matches_played = 25,
    total_goals = 8,
    total_assists = 18,
    total_yellow_cards = 5,
    total_red_cards = 0
WHERE id = '22222222-2222-2222-2222-222222222222';

UPDATE players SET
    total_matches_played = 24,
    total_goals = 2,
    total_assists = 3,
    total_yellow_cards = 6,
    total_red_cards = 1,
    total_clean_sheets = 8
WHERE id = '33333333-3333-3333-3333-333333333333';

UPDATE players SET
    total_matches_played = 25,
    total_goals = 0,
    total_assists = 0,
    total_yellow_cards = 1,
    total_red_cards = 0,
    total_clean_sheets = 12
WHERE id = '44444444-4444-4444-4444-444444444444';

UPDATE players SET
    total_matches_played = 30,
    total_goals = 22,
    total_assists = 8,
    total_yellow_cards = 4,
    total_red_cards = 0
WHERE id = '55555555-5555-5555-5555-555555555555';

UPDATE players SET
    total_matches_played = 28,
    total_goals = 12,
    total_assists = 15,
    total_yellow_cards = 7,
    total_red_cards = 0
WHERE id = '66666666-6666-6666-6666-666666666666';

UPDATE players SET
    total_matches_played = 20,
    total_goals = 3,
    total_assists = 2,
    total_yellow_cards = 5,
    total_red_cards = 0,
    total_clean_sheets = 7
WHERE id = '77777777-7777-7777-7777-777777777777';

UPDATE players SET
    total_matches_played = 20,
    total_goals = 18,
    total_assists = 6,
    total_yellow_cards = 2,
    total_red_cards = 0
WHERE id = '88888888-8888-8888-8888-888888888888';

-- Sample Join Requests (Pending)
INSERT INTO team_join_requests (team_id, player_id, status, message) VALUES
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '55555555-5555-5555-5555-555555555555', 'PENDING', 'I would love to join your team! I am a fast forward with good finishing skills.');

-- Sample Join Request (Approved)
INSERT INTO team_join_requests (team_id, player_id, status, message, reviewed_by, review_message, reviewed_at) VALUES
    ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '77777777-7777-7777-7777-777777777777', 'APPROVED', 'Looking for a competitive team', '55555555-5555-5555-5555-555555555555', 'Welcome! Training is on Tuesday and Thursday.', '2024-01-15 10:30:00');

-- Sample Join Request (Rejected)
INSERT INTO team_join_requests (team_id, player_id, status, message, reviewed_by, review_message, reviewed_at) VALUES
    ('cccccccc-cccc-cccc-cccc-cccccccccccc', '22222222-2222-2222-2222-222222222222', 'REJECTED', 'Want to play for a team in Ostrava', '77777777-7777-7777-7777-777777777777', 'Sorry, we are currently full. Try again next season!', '2024-01-10 14:20:00');

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Check all data was inserted correctly
-- Uncomment to run these queries

-- SELECT COUNT(*) as total_players FROM players;
-- SELECT COUNT(*) as total_teams FROM teams;
-- SELECT COUNT(*) as total_memberships FROM team_members;
-- SELECT COUNT(*) as total_requests FROM team_join_requests;

-- View team rosters
-- SELECT
--     t.name as team,
--     p.first_name || ' ' || p.last_name as player,
--     tm.role,
--     tm.jersey_number,
--     p.skill_rating
-- FROM teams t
-- JOIN team_members tm ON t.id = tm.team_id
-- JOIN players p ON tm.player_id = p.id
-- WHERE tm.is_active = true
-- ORDER BY t.name, tm.role DESC, tm.jersey_number;

-- View pending join requests
-- SELECT
--     t.name as team,
--     p.first_name || ' ' || p.last_name as player,
--     jr.message,
--     jr.created_at
-- FROM team_join_requests jr
-- JOIN teams t ON jr.team_id = t.id
-- JOIN players p ON jr.player_id = p.id
-- WHERE jr.status = 'PENDING'
-- ORDER BY jr.created_at DESC;
