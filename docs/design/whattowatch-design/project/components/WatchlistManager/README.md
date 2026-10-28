The Library page with named lists, built on `/watchlists/lists`. The sidebar holds Favourite and Watch later (system lists) plus your own lists; the main area shows the selected list's grid.

- Props: `lists` (`[{ id, name, count, system?, movies[] }]`), `selected`, `creating`.
- Your own lists can be renamed (`PUT /watchlists/{id}`) and deleted (`DELETE /watchlists/{id}`). New list → `POST /watchlists`. System lists keep their routes (`/library/favorites`, `/library/watchlist`).
- Adding a movie to a named list happens from the detail modal (follow-up: a "Add to list" menu beside Watch later).
