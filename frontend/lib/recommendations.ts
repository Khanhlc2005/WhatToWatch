import { MovieSummary } from './movies';

export type RecommendationHit = {
  movie: MovieSummary;
  score: number | null;
  scoreComponents: {
    profile_similarity: number | null;
    imdb_rating: number | null;
    weights: Record<string, number>;
  } | null;
  reasons: { code: string; value: number | null }[];
};

export type RecommendationResult = {
  status: string;
  hits: RecommendationHit[];
};

export function recommendationReason(hit: RecommendationHit): string {
  const codes = new Set((hit.reasons || []).map(reason => reason.code));
  if (codes.has('profile_similarity') && codes.has('imdb_rating')) return 'Matches your taste · Highly rated on IMDb';
  if (codes.has('profile_similarity')) return 'Matches your taste';
  if (codes.has('imdb_rating')) return 'Highly rated on IMDb';
  return 'Recommended for you';
}
