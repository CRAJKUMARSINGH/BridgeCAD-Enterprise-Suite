-- =============================================================================
-- BridgeCAD Enterprise Suite — PostgreSQL Schema (init.sql)
-- Applied by: docker-compose.prod.yml → db service initdb.d
-- Also runnable manually: psql -U bridgecad -d bridgecad -f migrations/init.sql
-- =============================================================================
-- SQLAlchemy ORM models in bridgecad_infra/db.py match this schema.
-- SQLite (dev) is created automatically; this file targets Postgres only.
-- =============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- trigram text search
CREATE EXTENSION IF NOT EXISTS "btree_gin";       -- GIN index on composite types

-- =============================================================================
-- projects
-- =============================================================================
CREATE TABLE IF NOT EXISTS projects (
    id              SERIAL          PRIMARY KEY,
    project_code    VARCHAR(30)     NOT NULL UNIQUE,
    project_title   VARCHAR(150),
    bridge_name     VARCHAR(120),
    chainage_km     NUMERIC(10,6),
    state_code      VARCHAR(10),
    client          VARCHAR(50),
    phase           VARCHAR(50),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- Trigram index for fast project search by title/name
CREATE INDEX IF NOT EXISTS idx_projects_title_trgm
    ON projects USING GIN (project_title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_projects_bridge_name_trgm
    ON projects USING GIN (bridge_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_projects_state_phase
    ON projects (state_code, phase);

-- Auto-update updated_at on row change
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_projects_updated_at ON projects;
CREATE TRIGGER trg_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- =============================================================================
-- bridges
-- =============================================================================
CREATE TABLE IF NOT EXISTS bridges (
    id                  SERIAL          PRIMARY KEY,
    project_id          INTEGER         NOT NULL
                            REFERENCES projects(id) ON DELETE CASCADE,
    bridge_type         VARCHAR(50),
    span_count          SMALLINT,
    total_length_m      NUMERIC(10,3),
    overall_width_m     NUMERIC(8,3),
    foundation_type     VARCHAR(50),
    qa_score            SMALLINT        CHECK (qa_score BETWEEN 0 AND 100),
    parameters_json     JSONB,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bridges_project_id
    ON bridges (project_id);
CREATE INDEX IF NOT EXISTS idx_bridges_type_qa
    ON bridges (bridge_type, qa_score);
CREATE INDEX IF NOT EXISTS idx_bridges_params_gin
    ON bridges USING GIN (parameters_json);

-- =============================================================================
-- generation_history
-- =============================================================================
CREATE TABLE IF NOT EXISTS generation_history (
    id              SERIAL          PRIMARY KEY,
    project_id      INTEGER         NOT NULL
                        REFERENCES projects(id) ON DELETE CASCADE,
    bridge_id       INTEGER
                        REFERENCES bridges(id) ON DELETE SET NULL,
    action          VARCHAR(50)     NOT NULL,   -- draw | validate | export | bill | qa
    status          VARCHAR(20)     NOT NULL,   -- success | failed | running
    output_path     TEXT,
    qa_score        SMALLINT,
    duration_ms     INTEGER,
    error_message   TEXT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gen_history_project_id
    ON generation_history (project_id);
CREATE INDEX IF NOT EXISTS idx_gen_history_action_status
    ON generation_history (action, status);
CREATE INDEX IF NOT EXISTS idx_gen_history_created_at
    ON generation_history (created_at DESC);

-- =============================================================================
-- api_keys  (optional — when AUTH_API_KEYS_ENABLED=true)
-- =============================================================================
CREATE TABLE IF NOT EXISTS api_keys (
    id              SERIAL          PRIMARY KEY,
    key_hash        VARCHAR(64)     NOT NULL UNIQUE, -- SHA-256 of raw key
    role            VARCHAR(20)     NOT NULL DEFAULT 'viewer'
                        CHECK (role IN ('admin','engineer','viewer')),
    label           VARCHAR(100),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    last_used_at    TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    revoked         BOOLEAN         NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys (key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_active
    ON api_keys (revoked, expires_at)
    WHERE revoked = FALSE;

-- =============================================================================
-- export_jobs  (async job queue tracking)
-- =============================================================================
CREATE TABLE IF NOT EXISTS export_jobs (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      INTEGER
                        REFERENCES projects(id) ON DELETE CASCADE,
    job_type        VARCHAR(30)     NOT NULL,   -- full_export | draw_only | bill_only
    status          VARCHAR(20)     NOT NULL DEFAULT 'queued',
                        -- queued | running | success | failed | cancelled
    input_path      TEXT,
    output_zip_path TEXT,
    qa_score        SMALLINT,
    error_message   TEXT,
    requested_by    VARCHAR(50),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_export_jobs_project
    ON export_jobs (project_id, status);
CREATE INDEX IF NOT EXISTS idx_export_jobs_status_created
    ON export_jobs (status, created_at DESC);

-- =============================================================================
-- plugin_registry  (tracks installed/enabled plugins per project)
-- =============================================================================
CREATE TABLE IF NOT EXISTS plugin_registry (
    id              SERIAL          PRIMARY KEY,
    plugin_id       VARCHAR(50)     NOT NULL,
    plugin_version  VARCHAR(20),
    enabled         BOOLEAN         NOT NULL DEFAULT TRUE,
    installed_at    TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    manifest_json   JSONB,
    UNIQUE (plugin_id)
);

-- Seed built-in plugins
INSERT INTO plugin_registry (plugin_id, plugin_version, enabled, manifest_json)
VALUES
    ('rcc_tbeam',   '1.0.0', TRUE, '{"bridge_types":["RCC_TBEAM"],"span_range_m":[6,30]}'::jsonb),
    ('psc_igirder', '1.0.0', TRUE, '{"bridge_types":["PSC_IGIRDER"],"span_range_m":[20,45]}'::jsonb),
    ('box_culvert', '1.0.0', TRUE, '{"bridge_types":["BOX_CULVERT"],"span_range_m":[2,8]}'::jsonb)
ON CONFLICT (plugin_id) DO NOTHING;

-- =============================================================================
-- Schema version tracking
-- =============================================================================
CREATE TABLE IF NOT EXISTS schema_versions (
    version         VARCHAR(20)     PRIMARY KEY,
    applied_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    description     TEXT
);

INSERT INTO schema_versions (version, description)
VALUES ('0.1.0-rc1', 'Initial schema: projects, bridges, generation_history, api_keys, export_jobs, plugin_registry')
ON CONFLICT (version) DO NOTHING;

-- =============================================================================
-- Grants (for application role 'bridgecad_app' if using role-based access)
-- =============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'bridgecad_app') THEN
        CREATE ROLE bridgecad_app LOGIN PASSWORD 'change-in-prod';
    END IF;
END;
$$;

GRANT SELECT, INSERT, UPDATE, DELETE
    ON TABLE projects, bridges, generation_history, api_keys, export_jobs, plugin_registry
    TO bridgecad_app;
GRANT USAGE, SELECT
    ON ALL SEQUENCES IN SCHEMA public
    TO bridgecad_app;
GRANT SELECT
    ON TABLE schema_versions
    TO bridgecad_app;

-- Done
\echo 'BridgeCAD schema v0.1.0-rc1 applied successfully.'
