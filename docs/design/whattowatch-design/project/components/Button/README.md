The app's buttons. `primary` is the one marquee action on a screen; everything else is `secondary`, `ghost` or `ghost-danger`.

- Props: `variant` (`primary` · `secondary` (default) · `ghost` · `ghost-danger`), `size` (`'sm'` for 36px, default 44px), `icon`, `iconRight`, `busy` + `busyLabel` (disables the button and swaps its label), `href` (renders an `<a>`), `pressed`, and any native button props.
- Use at most one `primary` per view. On the hero that is "View details"; on forms it is submit.
- Labels are sentence case and verb first. `arrow-up-right` marks a link that leaves the current screen ("Start exploring ↗").
