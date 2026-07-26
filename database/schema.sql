-- JanMitra AI — reference SQL schema (SQLAlchemy generates this automatically
-- via Base.metadata.create_all(), this file documents it for review / ER diagram use)
-- Target: PostgreSQL (e.g. Neon). SQLite also works via DATABASE_URL for local dev,
-- but SERIAL/TIMESTAMP syntax below is Postgres-specific.

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    unique_id VARCHAR(15) UNIQUE NOT NULL,      -- auto-generated, e.g. PDS482913
    full_name VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other')),
    pincode VARCHAR(6) NOT NULL,
    mobile VARCHAR(10) UNIQUE,
    password_hash TEXT NOT NULL,
    is_guest BOOLEAN DEFAULT FALSE,
    role VARCHAR DEFAULT 'citizen',             -- citizen | admin (needed for admin-only endpoints)
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE schemes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    category VARCHAR,
    state VARCHAR DEFAULT 'All India',
    min_age INTEGER,
    max_age INTEGER,
    gender VARCHAR DEFAULT 'All',
    max_income INTEGER,
    occupation VARCHAR,
    disability_required BOOLEAN DEFAULT 0,
    description TEXT,
    benefits TEXT,
    required_documents JSON,
    application_steps JSON,
    official_source VARCHAR,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR NOT NULL,
    source_type VARCHAR DEFAULT 'policy_pdf',
    file_path VARCHAR,
    chunk_count INTEGER DEFAULT 0,
    uploaded_by INTEGER REFERENCES users(id),
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR DEFAULT 'processed'
);

CREATE TABLE faqs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question VARCHAR NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR,
    language VARCHAR DEFAULT 'en',
    source VARCHAR
);

CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    session_id VARCHAR,
    role VARCHAR,
    message TEXT,
    sources JSON,
    confidence FLOAT,
    language VARCHAR DEFAULT 'en',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    chat_id INTEGER REFERENCES chat_history(id),
    rating INTEGER,
    comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type VARCHAR,
    payload JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_session ON chat_history(session_id);
CREATE INDEX idx_users_mobile ON users(mobile);
CREATE INDEX idx_users_unique_id ON users(unique_id);
