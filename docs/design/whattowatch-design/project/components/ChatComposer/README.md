The message box: optional suggestion chips, a single-line input (max 2000 characters), and Send.

- Props: `suggestions` (shown on an empty conversation; a click fills the input), `sending` (locks the box and shows "Finding movies and writing a reply…"), `loading`, `error` (keep the draft and show the error), `onSend(text)`.
- 401 responses redirect to `/login?next=%2Fchat`.
