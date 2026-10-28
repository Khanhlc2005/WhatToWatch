"Add to list": a button beside Favourite and Watch later in the detail modal that opens a small popover of the user's named lists, with a checkbox for each one.

- Props: `lists` (`[{ id, name, count, checked }]`, from `/watchlists/lists` plus the movie's membership), `open`, `creating` (shows the new-list field), `signedIn` (when false, a click calls `onRequireSignIn` → `/login?next=`), `busy`, `error`, `onToggle(id, on)`, `onCreate(name)`.
- Ticking a box calls `POST /watchlists/{id}/movies/{movieId}`; unticking calls `DELETE` on the same path. "New list" creates the list (`POST /watchlists`) and adds the movie to it in one step.
- The button's label shows how many lists the movie is in ("In 2 lists"). It turns `marquee-text` with a marquee border once the movie is in any list.
- Favourite and Watch later stay separate toggles; they are never repeated inside this menu.
- Close the popover with ✕, Escape, or a click outside. Changes apply instantly, so there is no Save button.
