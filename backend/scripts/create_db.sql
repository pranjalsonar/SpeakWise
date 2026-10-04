-- ============================================================
-- SpeakWise — database & application role bootstrap
--
-- Run once as a PostgreSQL superuser (safe to re-run):
--   psql -U postgres -h localhost -f scripts/create_db.sql
--
-- Tables are NOT created here; they are managed by Alembic:
--   alembic upgrade head
-- ============================================================

-- 1. Application login role
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'speakwise_app') THEN
        CREATE ROLE speakwise_app WITH LOGIN PASSWORD 'speakwise@1234';
    END IF;
END
$$;

-- 2. Application database, owned by the app role
SELECT 'CREATE DATABASE speakwise_db OWNER speakwise_app ENCODING ''UTF8'''
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'speakwise_db')
\gexec

-- 3. Give the app role full control of the public schema
\connect speakwise_db
ALTER SCHEMA public OWNER TO speakwise_app;
