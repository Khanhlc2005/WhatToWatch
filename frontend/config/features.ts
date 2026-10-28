// Features that wait for a backend fix (docs/backend-requests.md). Flip each one once its fix is live.

// /discover: the link in the navbar and on the Search page.
export const DISCOVER_ENABLED = true;
// GET /movies/filter filters on the score the cards show (IMDb, TMDB fallback).
export const RATING_FILTER_ENABLED = true;
// The seed data (data/mysql/movies_data.sql) fills only `movies`; `genres` and `movie_genres` stay empty,
// so any genre filter returns no movies.
export const GENRE_FILTER_ENABLED = false;
// "Add to list" in the detail modal: Watch later would show "Saved" for movies that are only in a named list.
export const ADD_TO_LIST_ENABLED = false;
