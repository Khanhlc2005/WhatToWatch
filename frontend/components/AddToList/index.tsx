import { FormEvent, useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import { LIST_NAME_MAX, ListMembership } from '../../lib/watchlists';
import { signedIn } from '../LibraryActions';
import Button from '../ui/Button';
import Icon from '../ui/Icon';
import IconButton from '../ui/IconButton';
import StatusNote from '../ui/StatusNote';
import styles from '../../styles/AddToList.module.scss';

// "Add to list" popover for the detail modal. Favourite and Watch later stay separate toggles.
export default function AddToList({ movieId }: { movieId: string }): React.ReactElement {
  const router = useRouter();
  const root = useRef<HTMLDivElement>(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [open, setOpen] = useState(false);
  const [lists, setLists] = useState<ListMembership[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const shown = useRef(movieId);
  shown.current = movieId;

  useEffect(() => { void signedIn().then(setAuthenticated); }, [movieId]);
  useEffect(() => { setOpen(false); setLists([]); setCreating(false); setError(''); setLoading(false); setBusy(false); }, [movieId]);

  const requireSignIn = useCallback(() => void router.push('/login?next=' + encodeURIComponent(router.asPath)), [router]);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/watchlists/membership?movieId=' + encodeURIComponent(movieId));
      if (response.status === 401) { requireSignIn(); return; }
      const body = await response.json();
      if (shown.current !== movieId) return;
      if (!response.ok) throw new Error(body.message || 'Could not load your lists.');
      setLists(body as ListMembership[]);
    } catch (reason) {
      if (shown.current === movieId) setError(reason instanceof Error ? reason.message : 'Could not load your lists.');
    } finally {
      if (shown.current === movieId) setLoading(false);
    }
  }, [movieId, requireSignIn]);

  // Close with Escape (before the modal sees it) or a click outside.
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      event.stopImmediatePropagation();
      setOpen(false);
    };
    const onPointer = (event: MouseEvent) => { if (!root.current?.contains(event.target as Node)) setOpen(false); };
    window.addEventListener('keydown', onKey, true);
    document.addEventListener('mousedown', onPointer);
    return () => { window.removeEventListener('keydown', onKey, true); document.removeEventListener('mousedown', onPointer); };
  }, [open]);

  async function request(listId: number, method: 'POST' | 'DELETE'): Promise<string | null> {
    const response = await fetch(`/api/watchlists/${listId}/movies/${encodeURIComponent(movieId)}`, { method });
    if (response.status === 401) { requireSignIn(); return null; }
    if (!response.ok) return (await response.json().catch(() => ({}))).message || 'Could not update your list.';
    return null;
  }

  async function toggle(list: ListMembership) {
    if (busy) return;
    setBusy(true);
    setError('');
    const message = await request(list.id, list.checked ? 'DELETE' : 'POST');
    if (shown.current !== movieId) {
      if (!message) window.dispatchEvent(new CustomEvent('wtw-library-change', { detail: movieId }));
      setBusy(false);
      return;
    }
    if (message) setError(message);
    else {
      setLists(current => current.map(item => item.id === list.id
        ? { ...item, checked: !item.checked, count: item.count + (item.checked ? -1 : 1) } : item));
      window.dispatchEvent(new CustomEvent('wtw-library-change', { detail: movieId }));
    }
    setBusy(false);
  }

  // New list: create it, then add this movie to it in one step.
  async function create(event: FormEvent) {
    event.preventDefault();
    if (busy || !name.trim()) return;
    setBusy(true);
    setError('');
    try {
      const response = await fetch('/api/watchlists', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name })
      });
      const body = await response.json().catch(() => ({}));
      if (shown.current !== movieId) return;
      if (!response.ok) { setError(body.message || 'Could not create the list.'); return; }
      const message = await request(body.id, 'POST');
      if (shown.current !== movieId) return;
      if (message) { setError(message); void load(); return; }
      setLists(current => [{ id: body.id, name: body.name, count: 1, checked: true }, ...current]);
      setName('');
      setCreating(false);
      window.dispatchEvent(new CustomEvent('wtw-library-change', { detail: movieId }));
    } finally {
      setBusy(false);
    }
  }

  if (!authenticated) return <Button icon='list' onClick={requireSignIn}>Add to list</Button>;

  const saved = lists.filter(list => list.checked).length;
  return <div className={styles.wrap} ref={root}>
    <button type='button' className={`${styles.button} ${saved ? styles.listed : ''}`} aria-haspopup='dialog' aria-expanded={open}
      onClick={() => { const next = !open; setOpen(next); if (next) void load(); }}>
      <Icon name='list' />
      <span>{saved ? `In ${saved} ${saved === 1 ? 'list' : 'lists'}` : 'Add to list'}</span>
      <Icon name='chevron-down' size={16} />
    </button>
    {open && <div className={styles.popover} role='dialog' aria-label='Save to a list'>
      <div className={styles.head}>
        <span className={styles.eyebrow}>SAVE TO</span>
        <IconButton icon='x' label='Close' onClick={() => setOpen(false)} />
      </div>
      {loading && <div className={styles.note}><StatusNote tone='loading'>Loading your lists…</StatusNote></div>}
      {!loading && lists.length === 0 && !error && <p className={styles.empty}>You have no lists yet.</p>}
      {lists.length > 0 && <ul className={styles.items}>
        {lists.map(list => <li key={list.id}>
          <label className={styles.row}>
            <input type='checkbox' checked={list.checked} disabled={busy} onChange={() => void toggle(list)} />
            <span className={styles.check} aria-hidden='true'>{list.checked && <Icon name='check' size={14} />}</span>
            <span className={styles.name}>{list.name}</span>
            <span className={styles.count}>{list.count}</span>
          </label>
        </li>)}
      </ul>}
      {error && <div className={styles.note}><StatusNote tone='error'>{error}</StatusNote></div>}
      <div className={styles.foot}>
        {creating
          ? <form className={styles.create} onSubmit={create}>
            <label htmlFor='new-list-name-modal' className={styles.sr}>List name</label>
            <input id='new-list-name-modal' autoFocus maxLength={LIST_NAME_MAX} placeholder='New list name' value={name}
              onChange={event => setName(event.target.value)} />
            <Button variant='primary' size='sm' type='submit' disabled={!name.trim() || busy}>Create</Button>
          </form>
          : <button type='button' className={styles.newList} onClick={() => setCreating(true)}><Icon name='plus' />New list</button>}
      </div>
    </div>}
  </div>;
}
