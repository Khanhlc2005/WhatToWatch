Previous / PAGE x / y / Next, used under search results and library grids.

- Props: `page` (1-based), `totalPages`, `onChange(page)`. Render it only when `totalPages > 1`.
- Search pages are 0-based in the URL today. Convert before passing `page`.
