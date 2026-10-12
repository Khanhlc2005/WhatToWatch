import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import styles from '../../styles/Modal.module.scss';
import { readApiJson } from '../../lib/readApiJson';

export default function MovieRating({ movieId }: { movieId: string }) {
  const router = useRouter();
  const [rating, setRating] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [signedOut, setSignedOut] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    setRating(null);
    setLoading(true);
    setError('');
    fetch('/api/ratings/' + encodeURIComponent(movieId))
      .then(async response => {
        if (response.status === 401) { if (active) setSignedOut(true); return null; }
        const body = await readApiJson<{ rating: number; message?: string } | null>(response,
          'Could not load your rating.', true);
        if (!response.ok) throw new Error(body?.message || 'Could not load your rating.');
        if (active) setSignedOut(false);
        return body;
      })
      .then(result => { if (active) setRating(result?.rating ?? null); })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : 'Could not load your rating.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [movieId]);

  async function save(value: number) {
    if (busy) return;
    setBusy(true);
    setError('');
    try {
      const response = await fetch('/api/ratings/' + encodeURIComponent(movieId), {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ rating: value })
      });
      if (response.status === 401) { setSignedOut(true); return; }
      const body = await readApiJson<{ rating: number; message?: string }>(response, 'Could not save your rating.');
      if (!response.ok) throw new Error(body.message || 'Could not save your rating.');
      setRating(body.rating);
      window.dispatchEvent(new Event('wtw-rating-change'));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not save your rating.');
    } finally { setBusy(false); }
  }

  return <div className={styles.userRating}>
    <strong>Your rating</strong>
    {loading && <span>Loading…</span>}
    {!loading && signedOut && <Link href={'/login?next=' + encodeURIComponent(router.asPath)}><a>Sign in to rate this movie</a></Link>}
    {!loading && !signedOut && <>
      <div className={styles.ratingChoices} aria-label='Rate this movie from 1 to 5 stars'>
        {[1, 2, 3, 4, 5].map(value => <button key={value} type='button' disabled={busy}
          aria-label={`${value} stars`} aria-pressed={rating === value} onClick={() => void save(value)}>{value} ★</button>)}
      </div>
      <span>{rating === null ? 'You have not rated this movie.' : `You rated this movie ${rating}/5 stars.`}</span>
    </>}
    {error && <span role='alert' className={styles.ratingError}>{error}</span>}
  </div>;
}
