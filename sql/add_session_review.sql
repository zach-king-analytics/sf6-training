-- Session review schema — run once against the games DB
-- These tables capture the human-reviewed loss analysis written in session markdown files.

-- One row per training session
CREATE TABLE IF NOT EXISTS sf.session_log (
    session_id      SERIAL PRIMARY KEY,
    session_date    DATE        NOT NULL,
    player_cfn      TEXT        NOT NULL,
    character       TEXT,
    session_type    TEXT        NOT NULL DEFAULT 'ranked',
    start_mr        INT,
    end_mr          INT,
    focus           TEXT,
    energy_pre      TEXT,
    energy_post     TEXT,
    mental_state    TEXT,
    total_wins      INT,
    total_losses    INT,
    session_notes   TEXT,
    source_file     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (session_date, player_cfn)
);

-- One row per individual loss reviewed within a session
CREATE TABLE IF NOT EXISTS sf.session_loss (
    loss_id             SERIAL PRIMARY KEY,
    session_id          INT         NOT NULL REFERENCES sf.session_log (session_id) ON DELETE CASCADE,
    loss_number         INT         NOT NULL,  -- 1-based ordinal within the session
    opponent_cfn        TEXT,
    opponent_character  TEXT,
    player_character    TEXT,                  -- denormalized from session frontmatter
    rounds              TEXT,                  -- e.g. "0-2", "1-2"
    replay_watched      BOOLEAN     NOT NULL DEFAULT FALSE,
    loss_category       TEXT,                  -- knowledge_gap | execution | mental | conditioning
    loss_subcategory    TEXT,                  -- neutral | oki | punish_miss | wake-up_option | drive_gauge | general
    what_beat_me        TEXT,
    execution_gap       TEXT,
    actionable_drill    TEXT,
    actionable_concept  TEXT,
    actionable_matchup  TEXT,
    replay_notes        TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (session_id, loss_number)
);

-- Index for downstream matchup analysis
CREATE INDEX IF NOT EXISTS idx_session_loss_opp_char ON sf.session_loss (opponent_character);
CREATE INDEX IF NOT EXISTS idx_session_loss_category ON sf.session_loss (loss_category);
CREATE INDEX IF NOT EXISTS idx_session_log_date      ON sf.session_log (session_date DESC);

-- View: denormalized losses with session context for easy querying
CREATE OR REPLACE VIEW sf.v_loss_review AS
SELECT
    sl.session_date,
    sl.player_cfn,
    sl.character          AS player_character,
    sl.session_type,
    sl.start_mr,
    sl.end_mr,
    sl.focus,
    sl.mental_state,
    lo.loss_number,
    lo.opponent_cfn,
    lo.opponent_character,
    lo.rounds,
    lo.replay_watched,
    lo.loss_category,
    lo.loss_subcategory,
    lo.what_beat_me,
    lo.execution_gap,
    lo.actionable_drill,
    lo.actionable_concept,
    lo.actionable_matchup,
    lo.replay_notes
FROM sf.session_log sl
JOIN sf.session_loss lo ON lo.session_id = sl.session_id
ORDER BY sl.session_date DESC, lo.loss_number;
