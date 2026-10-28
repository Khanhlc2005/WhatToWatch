Watch history (`/me/history`), built on `/watch-history`: entries grouped by day, each with a time, poster, title and meta, and a remove button, plus "Clear history".

- Props: `groups` (`[{ label, items: [{ id, time, movie }] }]`), `total`.
- Remove one → `DELETE /watch-history/{id}`; Clear history → `DELETE /watch-history`. Always confirm before clearing, because it cannot be undone.
