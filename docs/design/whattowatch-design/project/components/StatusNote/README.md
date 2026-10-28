A one-line state message for loading, info, invitations, errors, successes and empty lists. Every async block on every screen uses it.

- Props: `tone` (`loading` · `info` · `invite` · `error` · `success` · `empty`), `title` (optional bold first line), `action` (a link or small button on the right), `block` (dashed box for an empty page), `children` (the sentence).
- `error` renders with `role="alert"`; every other tone uses `role="status"`.
- Keep the app's existing sentences ("Could not load your list.", "Searching movies…"). State what happened and the next step.
