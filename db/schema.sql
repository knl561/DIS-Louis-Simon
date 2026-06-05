-- ============================================================
--  Movie Explorer — database schema
--  Faithful to the E/R model:
--    User, Movie, Genre, MovieGenre, Review, Rating, WatchlistEntry
-- ============================================================

-- Drop in dependency order so the script is re-runnable.
DROP VIEW  IF EXISTS movie_overview        CASCADE;
DROP TABLE IF EXISTS watchlist_entries     CASCADE;
DROP TABLE IF EXISTS ratings               CASCADE;
DROP TABLE IF EXISTS reviews               CASCADE;
DROP TABLE IF EXISTS movie_genres          CASCADE;
DROP TABLE IF EXISTS genres                CASCADE;
DROP TABLE IF EXISTS movies                CASCADE;
DROP TABLE IF EXISTS users                 CASCADE;

-- ------------------------------------------------------------
--  Entities
-- ------------------------------------------------------------

-- User( user_id, name, email )
CREATE TABLE users (
    user_id  SERIAL PRIMARY KEY,
    name     TEXT NOT NULL,
    email    TEXT NOT NULL UNIQUE
);

-- Movie( movie_id, title, year, description, avg_rating )
-- avg_rating is a derived value; it is maintained automatically
-- by a trigger (see below) whenever ratings change.
CREATE TABLE movies (
    movie_id    SERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    year        INTEGER CHECK (year BETWEEN 1888 AND 2100),
    description TEXT,
    avg_rating  NUMERIC(3,1) NOT NULL DEFAULT 0
);

-- Genre( genre_id, name )
CREATE TABLE genres (
    genre_id SERIAL PRIMARY KEY,
    name     TEXT NOT NULL UNIQUE
);

-- ------------------------------------------------------------
--  Relationships
-- ------------------------------------------------------------

-- MovieGenre( movie_id, genre_id ) — many-to-many between Movie and Genre
CREATE TABLE movie_genres (
    movie_id INTEGER NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    genre_id INTEGER NOT NULL REFERENCES genres(genre_id) ON DELETE CASCADE,
    PRIMARY KEY (movie_id, genre_id)
);

-- Review( review_id, user_id, movie_id, text, created_at )
CREATE TABLE reviews (
    review_id  SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(user_id)  ON DELETE CASCADE,
    movie_id   INTEGER NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    text       TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Rating( rating_id, user_id, movie_id, score )
-- One rating per (user, movie); re-rating UPDATEs the existing row.
CREATE TABLE ratings (
    rating_id SERIAL PRIMARY KEY,
    user_id   INTEGER NOT NULL REFERENCES users(user_id)  ON DELETE CASCADE,
    movie_id  INTEGER NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    score     INTEGER NOT NULL CHECK (score BETWEEN 1 AND 10),
    UNIQUE (user_id, movie_id)
);

-- WatchlistEntry( user_id, movie_id, added_at )
CREATE TABLE watchlist_entries (
    user_id  INTEGER NOT NULL REFERENCES users(user_id)  ON DELETE CASCADE,
    movie_id INTEGER NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    added_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, movie_id)
);

-- ============================================================
--  BONUS: stored function + trigger
--  Keeps movies.avg_rating in sync with the ratings table.
-- ============================================================
CREATE OR REPLACE FUNCTION recompute_avg_rating()
RETURNS TRIGGER AS $$
DECLARE
    target_movie INTEGER;
BEGIN
    -- On DELETE the changed row is in OLD, otherwise in NEW.
    IF (TG_OP = 'DELETE') THEN
        target_movie := OLD.movie_id;
    ELSE
        target_movie := NEW.movie_id;
    END IF;

    UPDATE movies
       SET avg_rating = COALESCE(
               (SELECT ROUND(AVG(score)::numeric, 1)
                  FROM ratings
                 WHERE movie_id = target_movie), 0)
     WHERE movie_id = target_movie;

    RETURN NULL;  -- AFTER trigger: return value is ignored
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_ratings_avg
AFTER INSERT OR UPDATE OR DELETE ON ratings
FOR EACH ROW EXECUTE FUNCTION recompute_avg_rating();

-- ============================================================
--  BONUS: view
--  One row per movie with its genres, review count and rating count.
--  Used by the browse / search / filter page.
-- ============================================================
CREATE OR REPLACE VIEW movie_overview AS
SELECT
    m.movie_id,
    m.title,
    m.year,
    m.description,
    m.avg_rating,
    COUNT(DISTINCT rv.review_id)                                  AS review_count,
    COUNT(DISTINCT rt.rating_id)                                  AS rating_count,
    COALESCE(STRING_AGG(DISTINCT g.name, ', ' ORDER BY g.name),'') AS genres
FROM movies m
LEFT JOIN reviews      rv ON rv.movie_id = m.movie_id
LEFT JOIN ratings      rt ON rt.movie_id = m.movie_id
LEFT JOIN movie_genres mg ON mg.movie_id = m.movie_id
LEFT JOIN genres       g  ON g.genre_id  = mg.genre_id
GROUP BY m.movie_id;
