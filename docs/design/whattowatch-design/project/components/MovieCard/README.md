The universal movie tile: poster, title, ticket meta, an optional recommendation reason, and compact library toggles.

- Props: `movie` (`{ id, title, poster, rating, year, favorite?, watchLater? }`), `reason` (shown under the meta, for "For you" picks), `rank` (1–10, draws the Top 10 rank numeral), `onOpen` (opens the detail modal and pushes `/movies/[id]?from=…`), `hideActions`, `signedIn`.
- Hovering or focusing the poster shows the flat `image-veil` with "View details ↗".
- Rows use a fixed 176px width; grids (search, library) let the card fill its column.
