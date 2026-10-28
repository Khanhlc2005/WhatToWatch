import Link from 'next/link';
import { FormEvent, useState } from 'react';
import { LIST_NAME_MAX, WatchlistSummary } from '../../lib/watchlists';
import Button from '../ui/Button';
import Icon, { IconName } from '../ui/Icon';
import StatusNote from '../ui/StatusNote';
import TextField from '../ui/TextField';
import styles from '../../styles/WatchlistManager.module.scss';

export interface WatchlistManagerProps {
  lists: WatchlistSummary[];
  selected: WatchlistSummary | null;
  favorites?: number;
  watchLater?: number;
  busy: boolean;
  onSelect: (id: number) => void;
  // Each handler resolves to an error message, or null on success.
  onCreate: (name: string) => Promise<string | null>;
  onRename: (name: string) => Promise<string | null>;
  onDelete: () => Promise<string | null>;
  children: React.ReactNode;
}

function SystemLink({ href, icon, label, count }: { href: string; icon: IconName; label: string; count?: number }) {
  return <li><Link href={href}><a className={styles.item}><Icon name={icon} /><span>{label}</span>{count != null && <span className={styles.count}>{count}</span>}</a></Link></li>;
}

export default function WatchlistManager({ lists, selected, favorites, watchLater, busy, onSelect, onCreate, onRename, onDelete, children }: WatchlistManagerProps): React.ReactElement {
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [renaming, setRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState('');
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState('');

  async function run(action: () => Promise<string | null>, done: () => void) {
    setError('');
    const message = await action();
    if (message) setError(message);
    else done();
  }
  const create = (event: FormEvent) => {
    event.preventDefault();
    if (newName.trim()) void run(() => onCreate(newName), () => { setNewName(''); setCreating(false); });
  };
  const rename = (event: FormEvent) => {
    event.preventDefault();
    if (renameValue.trim()) void run(() => onRename(renameValue), () => setRenaming(false));
  };

  return <div className={styles.lists}>
    <aside className={styles.side} aria-label='Your lists'>
      <h2 className={styles.heading}>YOUR LISTS</h2>
      <ul>
        <SystemLink href='/library/favorites' icon='heart' label='Favourite' count={favorites} />
        <SystemLink href='/library/watchlist' icon='bookmark' label='Watch later' count={watchLater} />
        {lists.map(list => <li key={list.id} className={selected?.id === list.id ? styles.on : undefined}>
          <button type='button' className={styles.item} aria-current={selected?.id === list.id ? 'true' : undefined}
            onClick={() => { setRenaming(false); setConfirming(false); setError(''); onSelect(list.id); }}>
            <Icon name='list' /><span>{list.name}</span><span className={styles.count}>{list.movieCount}</span>
          </button>
        </li>)}
      </ul>
      {creating
        ? <form className={styles.create} onSubmit={create}>
          <TextField id='new-list-name' label='List name' placeholder='e.g. Sunday classics' maxLength={LIST_NAME_MAX} autoFocus
            value={newName} onChange={event => setNewName(event.target.value)} />
          <div className={styles.actions}>
            <Button variant='primary' size='sm' type='submit' busy={busy} busyLabel='Creating…' disabled={!newName.trim()}>Create</Button>
            <Button variant='ghost' size='sm' onClick={() => { setCreating(false); setError(''); }}>Cancel</Button>
          </div>
        </form>
        : <Button icon='plus' block onClick={() => { setCreating(true); setError(''); }}>New list</Button>}
    </aside>
    <section className={styles.main} aria-label={selected?.name || 'Your lists'}>
      {error && <StatusNote tone='error'>{error}</StatusNote>}
      {selected ? <>
        <div className={styles.head}>
          {renaming
            ? <form className={styles.rename} onSubmit={rename}>
              <TextField id='rename-list' label='List name' maxLength={LIST_NAME_MAX} autoFocus value={renameValue}
                onChange={event => setRenameValue(event.target.value)} />
              <Button variant='primary' size='sm' type='submit' busy={busy} busyLabel='Saving…' disabled={!renameValue.trim()}>Save</Button>
              <Button variant='ghost' size='sm' onClick={() => { setRenaming(false); setError(''); }}>Cancel</Button>
            </form>
            : <div>
              <h2>{selected.name}</h2>
              <span className={styles.meta}>{selected.movieCount} SAVED {selected.movieCount === 1 ? 'MOVIE' : 'MOVIES'}</span>
            </div>}
          {!renaming && (confirming
            ? <div className={styles.confirm} role='group' aria-label='Confirm deleting this list'>
              <span>Delete “{selected.name}”? The movies stay in the catalogue.</span>
              <Button size='sm' onClick={() => setConfirming(false)}>Cancel</Button>
              <Button size='sm' variant='ghost-danger' icon='trash' busy={busy} busyLabel='Deleting…'
                onClick={() => void run(onDelete, () => setConfirming(false))}>Yes, delete list</Button>
            </div>
            : <div className={styles.actions}>
              <Button size='sm' icon='edit' disabled={busy} onClick={() => { setRenameValue(selected.name); setRenaming(true); setError(''); }}>Rename</Button>
              <Button size='sm' variant='ghost-danger' icon='trash' disabled={busy} onClick={() => { setConfirming(true); setError(''); }}>Delete list</Button>
            </div>)}
        </div>
        {children}
      </> : <StatusNote tone='empty' block title='You have no lists yet'>Create a list to group movies, like “Sunday classics”.</StatusNote>}
    </section>
  </div>;
}
