import { Breakpoint } from '../config/breakpoints';

export type Maybe<T> = T | null;

export type Dimension = {
  height: number;
  width: number;
};

export type DimensionDetail = {
  dimension: Dimension;
  breakpoint: Breakpoint;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
};

export type Genre = {
  id: number;
  name: string;
};

export enum MediaType {
  MOVIE = 'movie',
  TV = 'tv'
}

export type Movie = {
  id: string;
  title: string;
  overview: string;
  poster: string;
  banner: string;
  rating: number | null;
  genre: Genre[];
  runtime?: number | null;
  trailerKey?: string | null;
  cast?: string | null;
  similarMovies?: Movie[];
  releaseDate?: string | null;
};

// Compatibility alias for the imported UI; Movie is the canonical contract.
export type Media = Movie;

export type ImageType = 'poster' | 'original';

export type Section = {
  heading: string;
  endpoint: string;
};
