import { Media } from '../types';

export type MovieSummary = {
  id: string;
  title: string;
  posterUrl?: string | null;
  posterPath?: string | null;
  backdropUrl?: string | null;
  backdropPath?: string | null;
  overview?: string | null;
  genres?: string | null;
  voteAverage?: number | null;
  tmdbVoteAverage?: number | null;
  imdbRating?: number | null;
  releaseDate?: string | null;
};

export type MovieDetail = MovieSummary & {
  runtime?: number | null;
  runtimeMinutes?: number | null;
  trailerYoutubeKey?: string | null;
  trailerKey?: string | null;
  cast?: string | null;
};

export type Trailer = {
  trailerKey: string;
  embedUrl: string;
};

export function posterUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  if (value.startsWith('https://')) return value;
  if (value.startsWith('/')) return 'https://image.tmdb.org/t/p/w500' + value;
  return null;
}

export function youtubeTrailerSearchUrl(title: string, releaseDate?: string | null): string {
  const year = releaseDate?.slice(0, 4);
  const query = [title, year, 'official trailer'].filter(Boolean).join(' ');
  return 'https://www.youtube.com/results?search_query=' + encodeURIComponent(query);
}

export function toMedia(movie: MovieSummary | MovieDetail): Media {
  const poster = posterUrl(movie.posterUrl ?? movie.posterPath) || '/assets/loginBg.jpg';
  const banner = posterUrl(movie.backdropUrl ?? movie.backdropPath) || poster;
  const tmdbRating = movie.tmdbVoteAverage && movie.tmdbVoteAverage > 0
    ? movie.tmdbVoteAverage : null;
  return {
    id: movie.id,
    title: movie.title,
    overview: movie.overview || '',
    poster,
    banner,
    rating: movie.voteAverage ?? tmdbRating ?? movie.imdbRating ?? 0,
    genre: (movie.genres || '').split(',').map(name => name.trim())
      .filter(Boolean).map((name, id) => ({ id, name })),
    runtime: 'runtime' in movie || 'runtimeMinutes' in movie
      ? (movie as MovieDetail).runtime ?? (movie as MovieDetail).runtimeMinutes ?? null : null,
    trailerKey: 'trailerYoutubeKey' in movie || 'trailerKey' in movie
      ? (movie as MovieDetail).trailerYoutubeKey ?? (movie as MovieDetail).trailerKey ?? null : undefined,
    cast: 'cast' in movie ? (movie as MovieDetail).cast : null,
    releaseDate: movie.releaseDate ?? null
  };
}
