The advanced filter panel for the new Discover page (`/discover`). It maps one to one onto `GET /movies/filter`.

- Props: `genres` (`[{ id, name }]` from `config/genres.ts`, movie list), `selectedGenres` (ids → `genreIds`), `yearFrom` / `yearTo`, `minRating` / `maxRating` (0–10), `minRuntime` / `maxRuntime` (minutes), `language` (ISO code), `onApply`.
- Layout: a 360px sticky panel on the left with a results grid + `Pagination` on the right. Mirror the active filters into the URL query so results can be shared.
- "Reset all" clears every field. The submit button counts the selected genres.
