CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    full_name TEXT NOT NULL,
    resume_file_id TEXT,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'in_progress',
    ai_score INTEGER,
    ai_analysis_json TEXT
);

CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    question_key TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    answer_score INTEGER,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id)
);

CREATE INDEX IF NOT EXISTS idx_answers_candidate_id ON answers(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);