import { useState } from 'react';
import Link from 'next/link';
import { HistoryItem } from '../../lib/activity';
import { formatClock, formatDayLabel } from '../../lib/apiTime';
import { posterUrl } from '../../lib/movies';
import Button from '../ui/Button';
import IconButton from '../ui/IconButton';
import Poster from '../ui/Poster';
import StatusNote from '../ui/StatusNote';
import ledger from '../../styles/Ledger.module.scss';
import styles from '../../styles/WatchHistory.module.scss';

export interface WatchHistoryProps {
  items: HistoryItem[];
  total: number;
  busy: boolean;
  onRemove: (item: HistoryItem) => void;
  onClear: () => void;
}

export default function WatchHistory({ items, total, busy, onRemove, onClear }: WatchHistoryProps): React.ReactElement {
  const [confirming, setConfirming] = useState(false);

  if (items.length === 0) {
    return <StatusNote tone='empty' block title='Nothing watched yet'>Movies you open and watch will show up here.</StatusNote>;
  }

  // Entries arrive newest first, so groups keep that order.
  const groups: { label: string; items: HistoryItem[] }[] = [];
  items.forEach(item => {
    const label = formatDayLabel(item.createdAt);
    const last = groups[groups.length - 1];
    if (last && last.label === label) last.items.push(item);
    else groups.push({ label, items: [item] });
  });

  return <div className={styles.history}>
    <div className={styles.bar}>
      <span className={styles.count}>{total} {total === 1 ? 'MOVIE' : 'MOVIES'} WATCHED</span>
      {confirming
        ? <div className={styles.confirm} role='group' aria-label='Confirm clearing history'>
          <span>Clear all {total} entries? This cannot be undone.</span>
          <Button size='sm' onClick={() => setConfirming(false)}>Cancel</Button>
          <Button size='sm' variant='ghost-danger' icon='trash' busy={busy} busyLabel='Clearing…'
            onClick={() => { onClear(); setConfirming(false); }}>Yes, clear history</Button>
        </div>
        : <Button variant='ghost-danger' size='sm' icon='trash' disabled={busy} onClick={() => setConfirming(true)}>Clear history</Button>}
    </div>
    {groups.map(group => <section key={group.label} className={styles.day}>
      <h3 className={styles.heading}>{group.label}</h3>
      <ul className={ledger.ledger}>
        {group.items.map(item => <li key={item.id} className={ledger.row}>
          <span className={styles.time}>{formatClock(item.createdAt)}</span>
          <div className={ledger.poster}><Poster src={posterUrl(item.posterPath)} /></div>
          <div className={ledger.main}>
            <Link href={`/movies/${item.movieId}?from=${encodeURIComponent('/me/history')}`}>
              <a className={ledger.title}>{item.title}</a>
            </Link>
          </div>
          <div className={ledger.actions}>
            <IconButton icon='x' label={`Remove ${item.title} from history`} variant='danger' disabled={busy}
              onClick={() => onRemove(item)} />
          </div>
        </li>)}
      </ul>
    </section>)}
  </div>;
}
