import { RatingItem } from '../../lib/activity';
import { formatMonthDay } from '../../lib/apiTime';
import { posterUrl } from '../../lib/movies';
import Link from 'next/link';
import Button from '../ui/Button';
import Icon from '../ui/Icon';
import IconButton from '../ui/IconButton';
import Poster from '../ui/Poster';
import StatusNote from '../ui/StatusNote';
import styles from '../../styles/Ledger.module.scss';

export interface RatingHistoryProps {
  items: RatingItem[];
  busyId: number | null;
  onChange: (item: RatingItem) => void;
  onRemove: (item: RatingItem) => void;
}

export default function RatingHistory({ items, busyId, onChange, onRemove }: RatingHistoryProps): React.ReactElement {
  if (items.length === 0) {
    return <StatusNote tone='empty' block title='No ratings yet'
      action={<Button size='sm' href='/browse'>Explore movies</Button>}>
      Rate at least 3 movies you have watched to unlock personalized picks.
    </StatusNote>;
  }
  return <ul className={styles.ledger}>
    {items.map(item => {
      const stars = Math.round(item.rating);
      return <li key={item.id} className={styles.row}>
        <div className={styles.poster}><Poster src={posterUrl(item.moviePoster)} /></div>
        <div className={styles.main}>
          <Link href={`/movies/${item.movieId}?from=${encodeURIComponent('/me/ratings')}`}>
            <a className={styles.title}>{item.movieTitle}</a>
          </Link>
        </div>
        <div className={styles.stars} role='img' aria-label={`You rated ${stars} out of 5`}>
          {[1, 2, 3, 4, 5].map(value => <Icon key={value} name='star' size={16} filled={value <= stars}
            className={value <= stars ? styles.starOn : styles.starOff} />)}
        </div>
        <span className={styles.date}>{formatMonthDay(item.createdAt)}</span>
        <div className={styles.actions}>
          <IconButton icon='edit' label={`Change rating for ${item.movieTitle}`} disabled={busyId === item.id} onClick={() => onChange(item)} />
          <IconButton icon='trash' label={`Remove rating for ${item.movieTitle}`} variant='danger' disabled={busyId === item.id}
            onClick={() => onRemove(item)} />
        </div>
      </li>;
    })}
  </ul>;
}
