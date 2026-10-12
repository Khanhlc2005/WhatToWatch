import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Movie } from '../../types';
import { MovieSummary, toMovie } from '../../lib/movies';
import { RecommendationResult, recommendationReason } from '../../lib/recommendations';
import { readApiJson } from '../../lib/readApiJson';
import MovieRow from '../List/MovieRow';
import styles from '../../styles/Cards.module.scss';

export default function Recommendations() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [reasons, setReasons] = useState<string[]>([]);
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    async function loadTopImdb(fallbackStatus: string) {
      const response = await fetch('/api/movies/top-rated');
      const body = await readApiJson<MovieSummary[]>(response, 'Could not load top IMDb movies.');
      if (!response.ok) throw new Error('Could not load top IMDb movies.');
      const choices = [...body];
      for (let index = choices.length - 1; index > 0; index--) {
        const randomIndex = Math.floor(Math.random() * (index + 1));
        [choices[index], choices[randomIndex]] = [choices[randomIndex], choices[index]];
      }
      if (active) {
        setMovies(choices.slice(0, 10).map(toMovie));
        setReasons([]);
        setStatus(fallbackStatus);
      }
    }
    async function load() {
      setStatus('loading');
      setError('');
      try {
        const response = await fetch('/api/movies/recommendations');
        if (response.status === 401) {
          await loadTopImdb('sign_in');
          return;
        }
        const body = await readApiJson<RecommendationResult & { message?: string }>(response, 'Could not load your recommendations.');
        if (!response.ok) throw new Error(body.message || 'Could not load your recommendations.');
        const result = body as RecommendationResult;
        if (!active) return;
        if (result.status === 'cold_start') {
          await loadTopImdb('cold_start');
          return;
        }
        setStatus(result.status);
        setMovies((result.hits || []).map(hit => toMovie(hit.movie)));
        setReasons((result.hits || []).map(recommendationReason));
      } catch (reason) {
        if (!active) return;
        setStatus('error');
        setError(reason instanceof Error ? reason.message : 'Could not load your recommendations.');
      }
    }
    void load();
    window.addEventListener('wtw-rating-change', load);
    window.addEventListener('wtw-auth-change', load);
    return () => {
      active = false;
      window.removeEventListener('wtw-rating-change', load);
      window.removeEventListener('wtw-auth-change', load);
    };
  }, []);

  return <section id='for-you' className={styles.listContainer} aria-busy={status === 'loading'}>
    <div className={styles.sectionHeading}>
      <h2 className={styles.category}>For you</h2>
      <span className={styles.sectionLine} />
      <span className={styles.sectionCount}>{status === 'ready' ? `${movies.length} movies` : 'PERSONALIZED'}</span>
    </div>
    {status === 'loading' && <p role='status' className={styles.listNote}>Finding movies for you…</p>}
    {status === 'sign_in' && <p className={styles.listNote}>
      A random selection of top rated IMDb movies. <Link href='/login?next=%2Fbrowse%23for-you'><a>Sign in</a></Link> and rate 3 movies for personalized picks.
    </p>}
    {status === 'cold_start' && <p role='status' className={styles.listNote}>
      These top rated IMDb movies were picked at random. Rate at least 3 movies you have watched (1–5 stars) to get personalized picks.
    </p>}
    {status === 'unavailable' && <p role='alert' className={styles.listError}>Recommendations are temporarily unavailable. Please try again later.</p>}
    {status === 'error' && <p role='alert' className={styles.listError}>{error}</p>}
    {status === 'ready' && movies.length === 0 && <p role='status' className={styles.listNote}>No matching recommendations yet.</p>}
    {(status === 'ready' || status === 'cold_start' || status === 'sign_in') && movies.length > 0 && <>
      {status === 'ready' && <p className={styles.listNote}>Ranked by your preferences and IMDb rating.</p>}
      <MovieRow movies={movies} reasons={status === 'ready' ? reasons : undefined} />
    </>}
  </section>;
}
