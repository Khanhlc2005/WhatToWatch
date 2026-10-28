One chat message. The user's messages sit on the right on `surface-300`; WhatToWatch's sit on the left on `surface-200`, with numbered movie picks under a perforation.

- Props: `role` (`'user'` · `'assistant'`), `content`, `time`, `movies` (`[{ id, title, reason }]`, links to `/movies/[id]`), `status` (an assistant reply status from the API).
- Each API status has its own look: `answered` → the content plus picks; `no_match` → an `empty` note suggesting another genre, decade or mood; `insufficient_context` → an `info` note asking a follow-up question; `error` → a danger border plus an `error` note asking to resend.
