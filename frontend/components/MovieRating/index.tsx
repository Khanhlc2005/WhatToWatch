import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import styles from '../../styles/Rating.module.scss';
import { readApiJson } from '../../lib/readApiJson';
import Icon from '../ui/Icon';
import StatusNote from '../ui/StatusNote';

export default function MovieRating({ movieId }: { movieId: string }) {
  const router = useRouter();
  const [rating, setRating] = useState<number | null>(null);
  const [hover, setHover] = useState(0);
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

  const shown = hover || rating || 0;
  return <div className={styles.rate}>
    <strong className={styles.label}>Your rating</strong>
    {loading && <StatusNote tone='loading'>Loading your rating…</StatusNote>}
    {!loading && signedOut && <Link href={'/login?next=' + encodeURIComponent(router.asPath)}>
      <a className={styles.link}>Sign in to rate this movie</a>
    </Link>}
    {!loading && !signedOut && <>
      <div className={styles.stars} role='group' aria-label='Rate this movie from 1 to 5 stars' onMouseLeave={() => setHover(0)}>
        {[1, 2, 3, 4, 5].map(value => <button key={value} type='button' disabled={busy}
          className={value <= shown ? styles.on : undefined}
          aria-label={`${value} stars`} aria-pressed={rating === value}
          onMouseEnter={() => setHover(value)} onClick={() => void save(value)}>
          <Icon name='star' size={20} filled={value <= shown} />
        </button>)}
      </div>
      <span className={styles.status}>{rating === null ? 'You have not rated this movie.' : `You rated this movie ${rating}/5 stars.`}</span>
    </>}
    {error && <span role='alert' className={styles.error}>{error}</span>}
  </div>;
}
