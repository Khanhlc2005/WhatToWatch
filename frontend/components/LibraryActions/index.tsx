import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import styles from '../../styles/Library.module.scss';
import Icon from '../ui/Icon';

type Kind = 'favorites' | 'watchlist';
type Status = { favorites: boolean; watchlist: boolean };

let sessionPromise: Promise<boolean> | null = null;
export function invalidateLibrarySession() { sessionPromise = null; }
export function signedIn() {
  if (!sessionPromise) sessionPromise = fetch('/api/auth/session')
    .then(response => response.json()).then(body => Boolean(body.authenticated))
    .catch(() => false);
  return sessionPromise;
}

export default function LibraryActions({ movieId, compact = false }: { movieId: string; compact?: boolean }) {
  const router = useRouter();
  const [status, setStatus] = useState<Status>({ favorites: false, watchlist: false });
  const [authenticated, setAuthenticated] = useState(false);
  const [busy, setBusy] = useState<Kind | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    async function load() {
      const loggedIn = await signedIn();
      if (!active) return;
      setAuthenticated(loggedIn);
      if (!loggedIn) return;
      try {
        const [favorite, watchlist] = await Promise.all(['favorites', 'watchlist'].map(kind =>
          fetch(`/api/library/${kind}/${movieId}`).then(response => {
            if (!response.ok) throw new Error();
            return response.json();
          })));
        if (active) setStatus({ favorites: Boolean(favorite.favorite ?? favorite.isFavorite), watchlist: Boolean(watchlist.inWatchlist) });
      } catch {
        sessionPromise = null;
        if (active) setError('Could not load your saved movie status.');
      }
    }
    void load();
    const onChange = (event: Event) => {
      if (event.type === 'wtw-auth-change') invalidateLibrarySession();
      if (event.type === 'wtw-auth-change' || (event as CustomEvent).detail === movieId) void load();
    };
    window.addEventListener('wtw-library-change', onChange);
    window.addEventListener('wtw-auth-change', onChange);
    return () => {
      active = false;
      window.removeEventListener('wtw-library-change', onChange);
      window.removeEventListener('wtw-auth-change', onChange);
    };
  }, [movieId]);

  async function toggle(kind: Kind) {
    if (!authenticated) {
      void router.push('/login?next=' + encodeURIComponent(router.asPath));
      return;
    }
    if (busy) return;
    setBusy(kind);
    setError('');
    try {
      const response = await fetch(`/api/library/${kind}/${movieId}`, {
        method: status[kind] ? 'DELETE' : 'POST'
      });
      if (response.status === 401) {
        invalidateLibrarySession();
        setAuthenticated(false);
        void router.push('/login?next=' + encodeURIComponent(router.asPath));
        return;
      }
      if (!response.ok) {
        const body = await response.json();
        throw new Error(body.message || 'Could not update your list.');
      }
      setStatus(current => ({ ...current, [kind]: !current[kind] }));
      window.dispatchEvent(new CustomEvent('wtw-library-change', { detail: movieId }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not update your list.');
    } finally {
      setBusy(null);
    }
  }

  const favouriteLabel = status.favorites ? 'Remove from favourites' : 'Add to favourites';
  const laterLabel = status.watchlist ? 'Remove from Watch later' : 'Add to Watch later';
  return <div className={`${styles.actions} ${compact ? styles.compact : ''}`} onClick={event => event.stopPropagation()}>
    <button type='button' className={styles.favourite} aria-pressed={status.favorites} disabled={busy !== null}
      onClick={() => void toggle('favorites')} title={favouriteLabel} aria-label={compact ? favouriteLabel : undefined}>
      <Icon name='heart' filled={status.favorites} />
      {!compact && <span>{status.favorites ? 'In favourites' : 'Favourite'}</span>}
    </button>
    <button type='button' className={styles.later} aria-pressed={status.watchlist} disabled={busy !== null}
      onClick={() => void toggle('watchlist')} title={laterLabel} aria-label={compact ? laterLabel : undefined}>
      <Icon name={status.watchlist ? 'check' : 'plus'} />
      {!compact && <span>{status.watchlist ? 'Saved for later' : 'Watch later'}</span>}
    </button>
    {error && <span className={styles.error} role='alert'>{error}</span>}
  </div>;
}
