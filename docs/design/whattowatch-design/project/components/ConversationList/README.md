The chat sidebar: "New conversation", a Recent heading, and the saved conversations, each with a delete button.

- Props: `items` (`[{ id, title, when }]`), `selected`, `busy` (disables everything while a reply is in flight), `onNew`, `onSelect(id)`, `onDelete(id)`.
- The selected item gets `aria-current` and a 3px `marquee` inner edge. With no items, it shows "No conversations yet."
