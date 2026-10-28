The sticky top bar. It holds the brand, five destinations, a search shortcut, and either the account menu or "Sign in".

- Props: `active` (`home` · `search` · `discover` · `chat` · `library`), `scrolled` (switches to the solid `surface-100` bar, replacing the old translucent one), `user` (`{ email }` when signed in, else `null`), `onSignOut`.
- Links: Home `/browse`, Search `/search`, Discover `/discover` (new filters page), Chatbot W2W `/chat`, Library `/library/favorites` (Favourite, Watch later and named lists sit in tabs there).
- The account menu holds My ratings `/me/ratings`, Watch history `/me/history`, My lists `/library/lists`, and Sign out (which fires `wtw-auth-change`, then goes to `/`).
- The active link gets a 3px `marquee` bar on its bottom edge.
