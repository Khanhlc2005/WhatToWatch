Underline tabs that switch between sibling pages, such as the Library lists.

- Props: `items` (`[{ id, label, href, count? }]`), `active`, `label` (the nav's `aria-label`), `onChange` (optional; client-side switching).
- They render as links, so every tab keeps its own URL (`/library/favorites`, `/library/watchlist`, `/library/lists`).
