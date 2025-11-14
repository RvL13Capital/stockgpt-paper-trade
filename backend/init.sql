-- Initialize StockGPT Database
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS trading;
CREATE SCHEMA IF NOT EXISTS auth;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA trading TO stockgpt_user;
GRANT ALL PRIVILEGES ON SCHEMA auth TO stockgpt_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA trading TO stockgpt_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth TO stockgpt_user;

-- Set default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA trading GRANT ALL ON TABLES TO stockgpt_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT ALL ON TABLES TO stockgpt_user;