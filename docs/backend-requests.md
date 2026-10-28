# Backend requests from the UI redesign

Items the redesigned frontend works around or cannot ship until the backend changes. Source: `docs/design/whattowatch-design/project/README.md`.

| # | Endpoint | Current behaviour | Requested change | Blocks |
| --- | --- | --- | --- | --- |
| 1 | `POST /auth/introspect`, `GET /api/auth/session` | Returns only `valid`; no account email | Return the email (or add `GET /users/me`). Until then `pages/api/auth/session.ts` reads the JWT `sub` (the email) | Navbar account menu (works with the workaround) |
| 2 | `GET /movies/filter` | Compares `tmdbVoteAverage`, but cards show `imdbRating` (TMDB as fallback), so "IMDb ≥ 7.5" returns the wrong movies | Filter on the same score the cards show | Discover |
| 3 | `GET /chat/conversations/{id}` | `status` is returned for a new reply (`POST /chat`) but not stored on `ConversationMessage`, so a reopened conversation shows every assistant message as a normal answer | Store `status` on `ConversationMessage` and return it in the message list | Chat: per-status display after reopening a conversation (works for replies received in the current session) |
| 4 | All DTOs with `createdAt` / `updatedAt` (chat, ratings, watch history, watchlists) | `LocalDateTime` is serialised without a zone, e.g. `2026-10-28T05:40:18.92` from a UTC server, so a browser in another timezone reads the wrong time | Serialise with an offset or `Z` (use `Instant` / `OffsetDateTime`). Until then `lib/apiTime.ts` reads zone-less values as UTC | Chat times, My ratings and Watch history dates |
| 5 | `GET /ratings/my-ratings` | `RatingResponse` has the title and poster but no release year and no IMDb score | Add `releaseDate` and `imdbRating` (the fields `MovieSummaryResponse` carries) | My ratings: the "IMDb 9.3 · 1994" meta line under each title is left out |
| 6 | `GET /watch-history` | `WatchHistoryResponse.posterPath` is the raw TMDB path, and there is no year, IMDb score or runtime | Return `posterUrl` like `MovieSummaryResponse` and add `releaseDate`, `imdbRating`, `runtimeMinutes` | Watch history: the frontend builds the poster URL itself and leaves the meta line out |
