-- Run after importing movies_data.sql into the legacy `movie` table and
-- after the backend has created the current `movies` table.
-- The import only runs when `movies` is empty, so existing app data is preserved.
INSERT INTO movies (
    id, title, original_title, overview, tagline, release_date,
    runtime_minutes, status, poster_path, backdrop_path, trailer_key,
    trailer_site, tmdb_vote_average, imdb_id, imdb_rating,
    imdb_vote_count, tmdb_id, original_language, adult,
    created_at, updated_at
)
SELECT
    id, title, original_title, overview, tagline, release_date,
    runtime, status, poster_path, backdrop_path, trailer_key,
    trailer_site, NULLIF(vote_average, 0), imdb_id, imdb_rating,
    imdb_votes, tmdb_id, original_language, adult,
    NOW(6), NOW(6)
FROM movie
WHERE NOT EXISTS (SELECT 1 FROM movies LIMIT 1);
