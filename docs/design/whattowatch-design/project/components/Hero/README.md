The Featured movie, shown as a split layout: a solid `surface-100` text panel on the left and the backdrop on the right. It replaces the old full-bleed image with a gradient fade.

- Props: `movie` (`{ title, rating, year, runtime, overview, backdrop?, poster }`; with no `backdrop`, it centres the poster in the art panel), `onOpen`, `signedIn`. With no movie, it shows "Discover your next story".
- Keep the selection logic: a random pick from the top-10 top-rated list that never repeats the last pick (`sessionStorage`).
- Use one `display-xl`-scale title per page; the hero owns it on Browse.
