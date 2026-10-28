Movie metadata set in `meta` mono and joined by `·`, the way a ticket prints it: `IMDb 8.7 · 1994 · 142 MIN`.

- Props: `rating` (a number, or `null` for NOT RATED; leave it out to hide the score), `year`, `runtime` (minutes), `extra` (more uppercase strings), `highlight` (shows the score in `marquee-text`).
- Every number about a movie goes through this component. Never put scores or years in `body` text.
