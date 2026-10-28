The ticket mark plus the "WhatToWatch" wordmark set in `display`; links to `/browse` in the navbar and footer.

- Props: `href` (renders a link), `size` (`'md'` default, `'lg'` for landing and auth headers), `markOnly` (mark alone, e.g. a collapsed header).
- The mark is always `marquee` on a dark surface. Never recolour it, put it on a `marquee` fill, or stretch it.
- The landing header uses `size="lg"`; the navbar and footer use the default size.
- Asset files: `assets/Logos/wtw-mark.svg` (mark) and `assets/Logos/favicon.svg` (favicon, replaces `public/favicon.svg`).
