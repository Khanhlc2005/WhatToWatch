The "My ratings" ledger (`/me/ratings`), built on `GET /ratings/my-ratings`: one row per rated movie with its poster, title, meta, your stars, the date, and change and remove buttons.

- Props: `items` (`[{ id, rating, date, movie }]`). Change opens the detail modal at Your rating. Remove calls `DELETE /ratings/movie/{id}` and fires `wtw-rating-change`.
- Empty state: "No ratings yet". It explains that rating 3 movies unlocks For you.
