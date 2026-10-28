# Features to keep

This inventory comes from `frontend/` (Next.js 11, React 17, SCSS modules) and `backend/` (Spring Boot). Every redesigned screen must cover all the states below. Routes and API paths stay the same. The component that covers each item is shown in brackets.

## Global

- **Navbar** [Navbar]: the Brand links to `/browse`. Links: Home, Search, Discover (new), Chatbot W2W, Library. The active state follows the route, including `/library/[kind]` and hashes. The bar is transparent at the top and turns solid once scrolled.
- **Account** [Navbar]: checks `/api/auth/session` and shows either "Sign in" (→ `/login`) or the account menu: My ratings, Watch history, My lists, Sign out. Sign out calls logout, fires `wtw-auth-change`, then goes to `/`.
- **Footer** [Footer]: Brand, "Discover your next great story.", © year.
- **Sync events** between blocks: `wtw-auth-change`, `wtw-library-change` (detail = movieId), `wtw-rating-change`.
- **Broken images** fall back to `/assets/poster-placeholder.svg` everywhere [Poster].

## Landing `/` [LandingScreen]

- Header: Brand + "Sign in ↗". Eyebrow, a two-line H1 ("Find a great movie. / Enjoy it tonight."), the lead, the CTAs "Start exploring" (→ `/login`) and "Create an account" (→ `/register`), and a footer strip.

## Sign in / Sign up `/login`, `/register` [AuthForm]

- An intro column (eyebrow, two-line H1 "A new story every night.", lead) plus the form card.
- Fields: Email, Password (min 8), Confirm password (register only). The client-side error is "The passwords do not match."; server errors show with `role=alert`.
- `?registered=1` shows "Account created. Please sign in." Submit shows the busy label "Please wait…". The switch links keep `next`.
- Redirect safely to `?next=` (internal paths only).

## Browse `/browse` [BrowseScreen]

- **Hero** [Hero]: a random pick from the top-10 top-rated list that never repeats the last pick (`sessionStorage`). It shows the eyebrow, title, IMDb score, year, synopsis, "View details" (opens the modal), and "TOP 10 / WHAT TO WATCH". It also handles movies that have a poster but no backdrop.
- Intro (eyebrow, H1, lead) plus **quick links** to `#for-you`, `#top-rated`, `#newest` [Chip].
- **For you** [MovieRow + StatusNote] has six states:
  - loading;
  - `sign_in`: random top IMDb picks, plus an invite to sign in and rate 3 movies;
  - `cold_start`: top IMDb picks, plus "rate at least 3";
  - `ready`: picks with a reason each;
  - `unavailable`;
  - `error`.

  It reloads when a rating or the sign-in state changes.
- **Top rated** (with Top 10 ranks) and **New releases** [MovieRow]: heading with "N movies", a skeleton row [SkeletonRow], error, and empty states.
- Rows scroll sideways; the ‹ › buttons show only when the row can scroll that way, and each click scrolls about 85% of the row.

## Movie card [MovieCard]

- The poster opens the modal and pushes `/movies/[id]?from=…`; hovering shows "View details ↗".
- Title (truncated, with a `title` tooltip), IMDb score or "Not rated", year, an optional reason, and the compact Favourite / Watch later toggles [LibraryActions].

## Movie detail modal / `/movies/[id]` [MovieDetail]

- Opens from cards, the hero, chat links, or a direct URL. Close with ✕ or a click on the scrim to return to `from` or `/browse`. A load error shows "… · Go back".
- Trailer: the backdrop, then a youtube-nocookie embed (autoplay, muted) with the note "The trailer starts muted…". No trailer or an error → a note plus "Search for a trailer on YouTube".
- Title and meta; labelled library toggles ("In favourites", "Saved for later"); when signed out, these redirect to `/login?next=`.
- **Your rating** [RatingStars]: 1–5 stars, a status sentence, "Sign in to rate this movie", and loading and error states.
- Overview; facts: IMDb, Year, Runtime, Genres, Cast.
- **Similar language and era**: a row, or "No similar movies found."

## Search `/search` [SearchForm]

- Eyebrow, H1, the "Movie title" field (100 characters max), and Search. The URL holds `?q=&page=`.
- States: not searched yet, "Searching movies…", error, "N results for “q”", no results, the result grid, and Previous / Page x / y / Next [Pagination].

## Library `/library/favorites`, `/library/watchlist`, `/library/lists` (new) [Tabs + WatchlistManager]

- Eyebrow "YOUR COLLECTION", H1, and tabs for Favourite, Watch later and My lists.
- Loading, error, "N saved movies", empty (+ "Explore movies"), a grid, and pagination. The page refreshes when a movie is unsaved from a card. A 401 goes to `/login?next=`. An invalid kind shows "List not found".

## Chatbot W2W `/chat` [ChatScreen]

- Header: eyebrow, H1 "Your movie assistant", lead.
- Sidebar [ConversationList]: "New conversation", Recent, the selected item (`aria-current`), × delete per conversation, and "No conversations yet."
- Feed [ChatMessage]:
  - Empty state with suggestions [ChatComposer].
  - User and assistant messages ("You" / "WhatToWatch"), with picks linking to `/movies/[id]` plus a reason.
  - "Finding movies and writing a reply…" while waiting, and the feed scrolls to the bottom on new messages.
- **New:** each reply status has its own look: `answered`, `no_match`, `insufficient_context`, `error`.
- Composer: 2000 characters max; it locks while sending; on error it restores the draft. A 401 goes to `/login?next=/chat`.

## New screens on existing backend endpoints

Some of these endpoints need backend fixes before the screens can ship. The `UI` section's status table lists each one.

- **Discover `/discover`** [FilterPanel, DiscoverScreen]: `GET /movies/filter` filtering by genres, year range, rating range, language, and runtime range. Results show in a grid with pagination, and the filters are mirrored into the URL.
- **My ratings `/me/ratings`** [RatingHistory]: `GET /ratings/my-ratings`, with change and remove (`DELETE /ratings/movie/{id}`).
- **Watch history `/me/history`** [WatchHistory]: `/watch-history`, grouped by day, with remove one and clear all (confirm first).
- **My lists `/library/lists`** [WatchlistManager, LibraryScreen]: `/watchlists/lists`, with create, rename and delete, and listing a list's movies.
- **Add to list** [AddToList, in MovieDetail]: tick or untick named lists from the detail modal (`POST` / `DELETE /watchlists/{id}/movies/{movieId}`), or create a new list there with this movie in it.

## Screen cards

Landing, Sign in, Browse, Search, Discover, Chat, Library (My lists), My ratings, Watch history. The detail modal appears in the MovieDetail card with the Add to list popover open.
