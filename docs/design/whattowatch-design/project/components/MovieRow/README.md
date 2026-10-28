A horizontally scrolling row of `MovieCard`s, with ‹ › buttons that appear only when the row can scroll that way. Each click scrolls about 85% of the row's width.

- Props: `movies`, `title`, `id`, `stamp`, `count`, `note` (a `StatusNote` between the heading and the cards), `reasons` (one per movie), `ranked` (Top 10 numerals).
- Covers For you, Top rated, New releases, and Similar language and era in the modal.
- For you states: loading → `SkeletonRow`; `sign_in` → `invite` note + top IMDb picks; `cold_start` → `info` note ("Rate at least 3 movies…"); `ready` → reasons; `unavailable` / `error` → `error` note.
