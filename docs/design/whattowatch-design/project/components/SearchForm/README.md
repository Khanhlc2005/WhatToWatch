The large search bar on `/search`, with the "Movie title" label, a 100-character limit, and a Search button.

- Props: `value` (from `?q=`), `onSearch(query)` (push `/search?q=…`).
- Results render below with `TicketMeta`'s `extra` ("24 RESULTS FOR “GODFATHER”"), a grid of `MovieCard`s, and `Pagination`. Show the `StatusNote` for empty, searching, error and no matches.
