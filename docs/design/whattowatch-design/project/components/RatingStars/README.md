"Your rating": five star buttons (1–5) with a hover preview and a status sentence.

- Props: `value` (1–5 or `null`), `onRate(value)`, `state` (`'loading'` · `'signed-out'`, which shows "Sign in to rate this movie"), `busy`, `error`.
- After saving, fire `wtw-rating-change` so For you reloads. Each star uses `aria-label="N stars"` and `aria-pressed`.
