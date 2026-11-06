import { MovieDetail, posterUrl } from './movies';

export type MoviePreview = {
  poster: string | null;
  rating: number | null;
  year: string | null;
  runtime: number | null;
};

// One request per movie per page load; chat messages re-render often and may repeat the same pick.
const previews = new Map<string, Promise<MoviePreview | null>>();

export function loadMoviePreview(movieId: string): Promise<MoviePreview | null> {
  if (!/^[1-9][0-9]*$/.test(movieId)) return Promise.resolve(null);
  let pending = previews.get(movieId);
  if (!pending) {
    pending = fetch('/api/movies/' + movieId)
      .then(response => (response.ok ? response.json() as Promise<MovieDetail> : null))
      .then(detail => detail && {
        poster: posterUrl(detail.posterPath),
        rating: detail.imdbRating != null && detail.imdbRating > 0 ? detail.imdbRating : detail.tmdbVoteAverage ?? null,
        year: detail.releaseDate?.slice(0, 4) || null,
        runtime: detail.runtimeMinutes
      })
      .catch(() => null);
    // A failed lookup is not cached, so a later render can retry.
    void pending.then(value => { if (!value) previews.delete(movieId); });
    previews.set(movieId, pending);
  }
  return pending;
}
