The Favourite and Watch later toggles for one movie: labelled in the modal and hero, icon-only on cards.

- Props: `favorite`, `watchLater`, `compact`, `signedIn` (when false, a click calls `onRequireSignIn` → `/login?next=`), `busy`, `error`, `onChange(kind, on)`.
- On states: Favourite = `velvet` fill + filled heart, "In favourites"; Watch later = `success` border + check, "Saved for later". Both use `aria-pressed`.
- Keep the `wtw-library-change` event so cards, the modal and library pages stay in sync.
