A 2:3 poster image with `radius-sm` corners. If the image fails to load, it shows the flat NO POSTER placeholder (no gradient).

- Props: `movie` (`{ poster?, title, year, art? }`). `poster` is the TMDB URL. `art` (`[background, ink]`) draws a typographic poster; previews use it, and you can use it when a catalogue movie has no image.
- Production falls back to `/assets/poster-placeholder.svg` (new file: `assets/Images/poster-placeholder.svg`).
