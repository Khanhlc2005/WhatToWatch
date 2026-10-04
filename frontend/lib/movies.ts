import { Movie } from '../types';

// Wire contracts from the current Spring Boot DTOs (main), not the old UI branch.
export type MovieSummary = {
  id: number;
  title: string;
  posterUrl: string | null;
  voteAverage: number | null;
  releaseDate: string | null;
};

export type MovieDetail = {
  id: number;
  title: string;
  overview: string | null;
  posterPath: string | null;
  backdropPath: string | null;
  tmdbVoteAverage: number | null;
  imdbRating: number | null;
  runtimeMinutes: number | null;
  trailerKey: string | null;
  trailerSite: string | null;
  releaseDate: string | null;
};

export type Trailer = { trailerKey: string; embedUrl: string };

export function posterUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  if (value.startsWith('https://')) return value;
  if (value.startsWith('/') && !value.startsWith('//')) return 'https://image.tmdb.org/t/p/w500' + value;
  return null;
}

export function youtubeTrailerSearchUrl(title: string, releaseDate?: string | null): string {
  const query = [title, releaseDate?.slice(0, 4), 'official trailer'].filter(Boolean).join(' ');
  return 'https://www.youtube.com/results?search_query=' + encodeURIComponent(query);
}

export function toMovie(movie: MovieSummary | MovieDetail): Movie {
  // Java Longs beyond JS safe integers need a backend string-ID contract first.
  if (!Number.isSafeInteger(movie.id) || movie.id <= 0) throw new Error('Invalid movie ID');
  const detail = 'posterPath' in movie ? movie : null;
  const summary = 'posterUrl' in movie ? movie : null;
  const poster = posterUrl(detail ? detail.posterPath : summary?.posterUrl) || '/assets/loginBg.jpg';
  const tmdbRating = detail?.tmdbVoteAverage;
  return {
    id: String(movie.id),
    title: movie.title,
    overview: detail?.overview || '',
    poster,
    banner: posterUrl(detail?.backdropPath) || poster,
    rating: summary ? summary.voteAverage : (tmdbRating != null && tmdbRating > 0 ? tmdbRating : detail?.imdbRating ?? null),
    // Current DTOs do not expose genre/cast. Do not invent them from the title.
    genre: [],
    cast: null,
    runtime: detail?.runtimeMinutes ?? null,
    trailerKey: detail ? (detail.trailerSite === 'YouTube' ? detail.trailerKey : null) : undefined,
    releaseDate: movie.releaseDate
  };
}

// Compatibility for the imported starter; all paths use the same adapter.
export const toMedia = toMovie;
