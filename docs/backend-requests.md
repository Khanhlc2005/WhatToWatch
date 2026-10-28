# Backend requests from the UI redesign

Items the redesigned frontend works around or cannot ship until the backend changes. Source: `docs/design/whattowatch-design/project/README.md`.

| # | Endpoint | Current behaviour | Requested change | Blocks |
| --- | --- | --- | --- | --- |
| 1 | `POST /auth/introspect`, `GET /api/auth/session` | Returns only `valid`; no account email | Return the email (or add `GET /users/me`). Until then `pages/api/auth/session.ts` reads the JWT `sub` (the email) | Navbar account menu (works with the workaround) |
| 2 | `GET /movies/filter` | Compares `tmdbVoteAverage`, but cards show `imdbRating` (TMDB as fallback), so "IMDb ≥ 7.5" returns the wrong movies | Filter on the same score the cards show | Discover |
| 3 | `GET /chat/conversations/{id}` | `status` is returned for a new reply (`POST /chat`) but not stored on `ConversationMessage`, so a reopened conversation shows every assistant message as a normal answer | Store `status` on `ConversationMessage` and return it in the message list | Chat: per-status display after reopening a conversation (works for replies received in the current session) |
