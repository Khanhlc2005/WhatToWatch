## UI

Screenshots of all 10 screens are in the **UI** section below this brand book; the full-size PNGs are in **Assets → UI**. The table shows what the current repo (`frontend/` and `backend/`, commit `66f6692`) already has for each screen and what is still missing.

Status key: **Done** = works today and only needs the new styling · **Frontend** = backend is ready, the screen or control is missing in `frontend/` · **Backend** = needs a backend change first.



| Screen / feature | Frontend | Backend | What is missing |
| --- | --- | --- | --- |
| Landing `/` | Done | n/a | New layout only |
| Sign in / Sign up | Done | Done | New layout only |
| Browse `/browse` | Done | Done | Top 10 rank numerals, Favourite/Watch later on the hero (frontend only) |
| Search `/search` | Done | Done | "Try Discover" link, "Ask Chatbot W2W" on no match (frontend only) |
| Discover `/discover` | Frontend | Done, with a fix | No page and no `/api/discover` proxy for `GET /movies/filter`. The filter compares `tmdbVoteAverage`, while every card shows `imdbRating` (TMDB as fallback), so "IMDb ≥ 7.5" returns the wrong movies |
| Movie detail modal | Done | Done | Genre chips (frontend only) |
| Add to list menu | Frontend | Backend | There is no endpoint that says which named lists hold a movie. `GET /watchlists/status` returns true when the movie is in *any* list, so Watch later shows "Saved" for movies that are only in a named list |
| Chatbot W2W `/chat` | Done | Done, with a fix | No per-status display, suggestion chips or timestamps (frontend). `status` is returned for a new reply but not stored on `ConversationMessage`, so reopened conversations lose it (backend) |
| Library: My lists `/library/lists` | Frontend | Backend | No page. `GET /watchlists/lists` also returns the hidden "Default Watchlist" (Watch later), and `DELETE /watchlists/{id}` can delete it. The `findByUserId` fallback returns `Optional<Watchlist>`, which fails once a user has two or more lists and no default list |
| My ratings `/me/ratings` | Frontend | Done | No page, no `/api` proxy for `GET /ratings/my-ratings`, and no `DELETE` in `pages/api/ratings/[movieId].ts`. The response has title and poster but no year or IMDb score for the meta line |
| Watch history `/me/history` | Frontend | Done | No page, no `/api` proxy, and the app never calls `POST /watch-history`, so history stays empty. The response returns the raw `posterPath`, not the full URL that `MovieSummaryResponse.posterUrl` gives |
| Account menu in Navbar | Frontend | Backend | `/api/auth/session` returns only `authenticated`, and `/auth/introspect` returns only `valid`. Showing the email needs `GET /users/me`, or the session route can read the JWT `sub` |
| Logo, favicon, poster placeholder, icons | Frontend | n/a | Replace `public/favicon.svg`, `public/assets/poster-placeholder.svg` and `react-icons` |

Concept: **Ticket Stub — the ticket and printed programme of an independent cinema.** WhatToWatch is built like a repertory cinema's box office. Metadata is set in mono like the print on a ticket, titles are set in serif like a programme, the torn-ticket perforation is the signature divider, and one marquee-bulb colour (`marquee`) marks the main action. Every surface is a flat colour. The system uses **no gradients** anywhere, including fades on images. It is dark only, desktop-first, and all copy is English.

## Content fundamentals

- Short and warm, like a friendly usher: "Find a great movie for tonight.", "Your next great story is waiting." Keep the app's existing copy where it exists; `features.md` lists it per screen.
- Address the user as "you" / "your list". The assistant calls itself **WhatToWatch**, never "AI" or "bot". The nav item stays "Chatbot W2W".
- Use sentence case for buttons and headings ("Watch later", "Create an account"). Uppercase is only for the `eyebrow` style ("YOUR COLLECTION", "FEATURED MOVIE") and for `meta` units ("142 MIN").
- No emoji. The glyphs `★ ♥ ✓ +` survive only as the `Icon` names `star`, `heart`, `check`, `plus`.
- Errors say what happened and what to do next: "Could not load your list.", "Sign in to rate this movie". Don't apologise at length.
- Write metadata the way a ticket prints it: `IMDb 8.7 · 1994 · 142 MIN`, with `·` between parts and units in uppercase.

## Visual foundations

**Colour**
- Page background `surface-000`; grouped regions `surface-100`; cards and raised blocks `surface-200`; hover and skeletons `surface-300`. Each step is one notch apart, so separate regions with `line`, not shadows.
- Text: `ink` for titles and content, `ink-muted` for descriptions, `ink-faint` only for mono metadata and placeholders (never on `surface-300`).
- `marquee` is the one colour for the main action: the primary button, selected stars and chips, and the active nav/tab bar. Use at most **one** marquee-filled button per view. Text on it is always `on-marquee`; yellow text on a surface is `marquee-text`.
- `velvet` is the secondary identity colour: the "For you" stamp, the avatar, and Favourite when on. Never use it for errors; errors are `danger` plus a sentence.
- `success` and `danger` always come with a word or an icon (check, "Could not…"). Never signal state by colour alone.
- To put text on an image, lay a flat `image-veil` over it and set the text in `ink`. Never use linear-gradient to fade an image. The scrim behind the modal is `scrim`.

**Type**
- Three families, loaded from Google Fonts: `display` (Newsreader, an optical-size serif), `sans` (Be Vietnam Pro, for UI), and `mono` (JetBrains Mono, for ticket metadata).
- Use `display-xl` scale once per screen: the landing headline or the hero title. Movie title in the modal: `display-l`. Page H1: `title-l`. Section headings: `title-m`, italic.
- Body copy `body`; lead paragraphs `body-l`; reasons and helper text `body-s`; buttons, tabs and labels `label`.
- Every number about a movie goes in `meta` (score, year, runtime, page, counts). Top 10 ranks use `rank`, always two digits.

**Space and layout**
- A 4px scale: `space-1` … `space-16`. Desktop gutter `space-12`; content max width 1440px; sections on Browse are `space-12` apart.
- A section heading is one line: italic `title-m`, then a `line` hairline, then a `meta` count.
- The hero is a **split layout**: a `surface-100` text panel on the left and the backdrop on the right with `radius-lg` corners. Detail pages, chat, discover and lists all use a sidebar (280–360px) plus a main column.
- Keep the code's breakpoints (480 / 640 / 768 / 1024 / 1280 / 1536). Desktop is the primary target; below 1024px, sidebars stack above content.

**Shape, borders, shadows**
- Radii: `radius-sm` for posters, buttons and inputs (near-square, like paper tickets); `radius-md` for cards, panels and bubbles; `radius-lg` for the modal and hero; `radius-pill` for chips, stars and icon buttons.
- The **perforation** (`Perforation`) is the signature mark. It appears in three places: the modal head/body split, the auth card stub, and the picks in a chat reply. Use at most one per block.
- Prefer borders to shadows. Only `shadow-overlay` exists, for the modal and the account menu.
- Selected list items get a 3px inner `marquee` edge. Never use a coloured left-border card, glass, glow or blur.

**Imagery**
- Posters are 2:3 with `radius-sm`; backdrops are 16:9. A missing image falls back to the flat NO POSTER placeholder (`assets/Images/poster-placeholder.svg`).
- The card hover shows `image-veil` plus "View details ↗".

**Motion**
- Short and mechanical, like a projector changing reels: 160ms for hover and press; 240ms to open the modal (fade plus a 12px rise); easing `cubic-bezier(.2,.7,.2,1)`.
- Rows scroll smoothly. No parallax and no auto-carousel. Under `prefers-reduced-motion`, keep only fades and stop the skeleton pulse.

**States**
- Hover: one surface step up. The primary button changes to `marquee-hover`.
- Focus-visible: a 2px solid `focus` ring with a 3px offset on every control (inputs use a 1px offset). It holds at least 3:1 on every surface.
- Disabled: opacity .45 and a `not-allowed` cursor. A busy button swaps its label ("Please wait…").
- Toggles use `aria-pressed`: Favourite on = `velvet` fill; Watch later on = `success` border plus a check; stars on = `marquee`.

## Iconography

- One stroked set (`Icon`): 24px grid, 1.5px stroke, round caps and joins, Lucide style. It replaces `react-icons` and the Unicode glyphs. In production, use `lucide-react` with the same names.
- Icons take `currentColor`. Size 18 inside buttons, 20 in the navbar, 22 for float buttons. Use the filled form only for an "on" state (heart, star) and for play.
- Logo: the ticket mark in `assets/Logos/wtw-mark.svg` (`marquee` ink, a ticket with side notches and a cut-out play triangle), plus the "WhatToWatch" wordmark set live in `display` by `Brand`. The favicon (`assets/Logos/favicon.svg`) replaces `public/favicon.svg`.

## Screens

The `Screens` cards (Landing, Browse, Chat, Discover) show how components compose into full pages. `features.md` lists every feature, state and route the redesign must keep, plus the new screens built on existing backend endpoints.
