import { MovieDetail } from './movies';

const VIDEO_ID = /^[A-Za-z0-9_-]{11}$/;
const POSITIVE_TTL = 7 * 24 * 60 * 60 * 1000;
const NEGATIVE_TTL = 6 * 60 * 60 * 1000;
const CACHE_LIMIT = 1000;

type Video = { key?: string; site?: string; type?: string; official?: boolean; iso_639_1?: string };
type SearchItem = { id?: { videoId?: string }; snippet?: { title?: string } };
type VideoItem = {
  id?: string;
  snippet?: { title?: string };
  status?: { embeddable?: boolean; privacyStatus?: string };
  contentDetails?: { duration?: string; regionRestriction?: { blocked?: string[] } };
};
type Cached = { key: string | null; expiresAt: number };

const cache = new Map<number, Cached>();
const pending = new Map<number, Promise<string | null>>();

export function validVideoId(value: unknown): value is string {
  return typeof value === 'string' && VIDEO_ID.test(value);
}

async function getJson<T>(url: URL): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  try {
    const response = await fetch(url.toString(), { signal: controller.signal });
    if (!response.ok) throw new Error('Trailer provider returned ' + response.status);
    return await response.json() as T;
  } finally {
    clearTimeout(timeout);
  }
}

async function fromTmdb(movie: MovieDetail, apiKey: string): Promise<string | null> {
  if (!movie.tmdbId || !Number.isSafeInteger(movie.tmdbId)) return null;
  const url = new URL(`https://api.themoviedb.org/3/movie/${movie.tmdbId}/videos`);
  url.searchParams.set('api_key', apiKey);
  url.searchParams.set('language', 'en-US');
  const body = await getJson<{ results?: Video[] }>(url);
  const trailers = (body.results || []).filter(video =>
    video.site?.toLowerCase() === 'youtube' && video.type?.toLowerCase() === 'trailer' && validVideoId(video.key));
  trailers.sort((a, b) => Number(Boolean(b.official)) - Number(Boolean(a.official))
    || Number(b.iso_639_1 === 'en') - Number(a.iso_639_1 === 'en'));
  return trailers[0]?.key || null;
}

function normalize(value: string): string {
  return value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
    .replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, ' ').trim();
}

function matchesMovie(videoTitle: string, movie: MovieDetail): boolean {
  const title = normalize(videoTitle);
  if (!/\btrailer\b/.test(title) || /\b(review|reaction|fan made|fan edit|scene|clip|full movie|teaser)\b/.test(title)) return false;
  const names = [movie.originalTitle, movie.title].filter((name): name is string => Boolean(name));
  if (!names.some(name => {
    const normalized = normalize(name);
    return normalized.length >= 3 && (` ${title} `).includes(` ${normalized} `);
  })) return false;
  const year = movie.releaseDate?.slice(0, 4);
  const years = title.match(/\b(?:19|20)\d{2}\b/g) || [];
  return !year || years.length === 0 || years.some(candidate => Math.abs(Number(candidate) - Number(year)) <= 1);
}

function durationSeconds(duration: string): number {
  const match = /^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$/.exec(duration);
  return match ? Number(match[1] || 0) * 3600 + Number(match[2] || 0) * 60 + Number(match[3] || 0) : 0;
}

async function fromYouTube(movie: MovieDetail, apiKey: string): Promise<string | null> {
  const query = [movie.originalTitle || movie.title, movie.releaseDate?.slice(0, 4), 'official trailer'].filter(Boolean).join(' ');
  const searchUrl = new URL('https://www.googleapis.com/youtube/v3/search');
  searchUrl.searchParams.set('key', apiKey);
  searchUrl.searchParams.set('part', 'snippet');
  searchUrl.searchParams.set('type', 'video');
  searchUrl.searchParams.set('videoEmbeddable', 'true');
  searchUrl.searchParams.set('maxResults', '5');
  searchUrl.searchParams.set('q', query);
  const search = await getJson<{ items?: SearchItem[] }>(searchUrl);
  const candidates = (search.items || []).filter(item =>
    validVideoId(item.id?.videoId) && matchesMovie(item.snippet?.title || '', movie));
  if (!candidates.length) return null;

  const videosUrl = new URL('https://www.googleapis.com/youtube/v3/videos');
  videosUrl.searchParams.set('key', apiKey);
  videosUrl.searchParams.set('part', 'snippet,status,contentDetails');
  videosUrl.searchParams.set('id', candidates.map(item => item.id!.videoId).join(','));
  const videos = await getJson<{ items?: VideoItem[] }>(videosUrl);
  const byId = new Map((videos.items || []).map(video => [video.id, video]));
  for (const candidate of candidates) {
    const id = candidate.id!.videoId!;
    const video = byId.get(id);
    const seconds = durationSeconds(video?.contentDetails?.duration || '');
    if (video?.status?.embeddable !== true || video.status.privacyStatus !== 'public'
      || video.contentDetails?.regionRestriction?.blocked?.includes('VN')
      || seconds < 30 || seconds > 6 * 60
      || !matchesMovie(video.snippet?.title || '', movie)) continue;
    return id;
  }
  return null;
}

async function findTrailer(movie: MovieDetail): Promise<{ key: string | null; cacheable: boolean }> {
  let failed = false;
  const tmdbKey = process.env.TMDB_KEY || process.env.TMDB_API;
  if (tmdbKey) {
    try {
      const key = await fromTmdb(movie, tmdbKey);
      if (key) return { key, cacheable: true };
    } catch (error) {
      failed = true;
      console.warn('TMDB trailer lookup failed:', error instanceof Error ? error.message : 'unknown error');
    }
  }
  const youtubeKey = process.env.YOUTUBE_API_KEY;
  if (youtubeKey) {
    try {
      const key = await fromYouTube(movie, youtubeKey);
      return { key, cacheable: Boolean(key) || !failed };
    } catch (error) {
      failed = true;
      console.warn('YouTube trailer lookup failed:', error instanceof Error ? error.message : 'unknown error');
    }
  }
  return { key: null, cacheable: !failed && Boolean(tmdbKey || youtubeKey) };
}

export async function resolveTrailer(movie: MovieDetail): Promise<string | null> {
  if (movie.trailerSite?.toLowerCase() === 'youtube' && validVideoId(movie.trailerKey)) return movie.trailerKey;
  const cached = cache.get(movie.id);
  if (cached && cached.expiresAt > Date.now()) return cached.key;
  if (pending.has(movie.id)) return pending.get(movie.id)!;
  const task = findTrailer(movie).then(({ key, cacheable }) => {
    if (cacheable) {
      cache.set(movie.id, { key, expiresAt: Date.now() + (key ? POSITIVE_TTL : NEGATIVE_TTL) });
      if (cache.size > CACHE_LIMIT) {
        const oldest = cache.keys().next().value;
        if (oldest !== undefined) cache.delete(oldest);
      }
    }
    return key;
  }).finally(() => pending.delete(movie.id));
  pending.set(movie.id, task);
  return task;
}
