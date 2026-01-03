CREATE TABLE IF NOT EXISTS cerita (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    url_thumbnail TEXT,
    url_text TEXT,
    sinopsis TEXT,
    genre TEXT[] NOT NULL,
    views INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cerita_genre
ON cerita
USING GIN (genre);
