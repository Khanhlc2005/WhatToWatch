// Features that wait for a backend fix (docs/backend-requests.md). Flip each one once its fix is live.

// /discover: the link stays out of the navbar and the Search page until the rating filter works.
export const DISCOVER_ENABLED = false;
// GET /movies/filter compares tmdbVoteAverage while every card shows imdbRating, so "IMDb ≥ 7.5" returns the wrong movies.
export const RATING_FILTER_ENABLED = false;
// The seed data (data/mysql/movies_data.sql) fills only `movies`; `genres` and `movie_genres` stay empty,
// so any genre filter returns no movies.
export const GENRE_FILTER_ENABLED = false;
// "Add to list" in the detail modal: Watch later would show "Saved" for movies that are only in a named list.
export const ADD_TO_LIST_ENABLED = false;
