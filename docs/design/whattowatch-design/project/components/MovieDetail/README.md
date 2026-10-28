The movie detail modal (also served at `/movies/[id]`). It holds the trailer or backdrop, title and meta, library toggles, your rating, overview, facts, and Similar language and era.

- Props: `movie` (`{ title, rating, year, runtime, overview, genres[], cast, backdrop?, myRating?, favorite?, watchLater? }`), `trailer` (`'image'` before load · `'playing'` youtube-nocookie embed, autoplay muted · `'none'` 404 · `'error'`), `similar` (movies), `signedIn`, `onClose` (✕ or a click on the scrim; returns to `from` or `/browse`), `inline` (preview only).
- `lists` (the user's named lists, with `checked` for the ones that already hold this movie) adds the `AddToList` button beside the library toggles. `listsOpen` opens its popover; it is used only in this preview.
- With no trailer, show the info note plus the "Search for a trailer on YouTube" link. While playing, show "The trailer starts muted…".
- The perforation separates the ticket head (title, actions) from the stub (details).
