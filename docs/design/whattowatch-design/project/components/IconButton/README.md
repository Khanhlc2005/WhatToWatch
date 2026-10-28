A round button that shows only an icon: closing the modal, row arrows, delete, rename.

- Props: `icon`, `label` (required; becomes both `aria-label` and `title`), `variant` (`float` for a bordered button over content, `danger` for a delete action that turns red on hover), `size` (`'lg'`).
- Row arrows render only when the row can scroll that way, as `MovieRow` does today.
