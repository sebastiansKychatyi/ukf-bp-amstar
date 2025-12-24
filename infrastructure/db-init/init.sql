-- AmStar Database Initialization Script
-- This script ensures the database exists and is properly configured

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE amstar_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'amstar_db')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE amstar_db TO amstar;

-- Connect to amstar_db
\c amstar_db

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Log success
DO $$
BEGIN
  RAISE NOTICE 'AmStar database initialized successfully';
END $$;
