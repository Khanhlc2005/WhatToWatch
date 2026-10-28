import { useContext } from 'react';
import { useRouter } from 'next/router';
import { Movie } from '../../types';
import { ModalContext } from '../../context/ModalContext';
import styles from '../../styles/Cards.module.scss';
import LibraryActions from '../LibraryActions';
import Icon from '../ui/Icon';
import Poster from '../ui/Poster';
import TicketMeta from '../ui/TicketMeta';

export interface MovieCardProps {
  item: Movie;
  reason?: string;
  rank?: number;
  // Fill the grid column instead of the fixed 176px row width.
  fluid?: boolean;
}

export default function MovieCard({ item, reason, rank, fluid = false }: MovieCardProps): React.ReactElement {
  const router = useRouter();
  const { setModalData, setIsModal } = useContext(ModalContext);

  const openDetail = () => {
    setModalData(item);
    setIsModal(true);
    const from = router.pathname === '/search' || router.pathname === '/library/[kind]'
      ? router.asPath : typeof router.query.from === 'string' ? router.query.from : '';
    const url = '/movies/' + item.id + (from ? '?from=' + encodeURIComponent(from) : '');
    void router.push(url, undefined, { scroll: false });
  };

  return <article className={`${styles.card} ${rank ? styles.ranked : ''} ${fluid ? styles.fluid : ''}`}>
    {rank && <span className={styles.rank} aria-label={'Rank ' + rank}>{rank < 10 ? '0' + rank : rank}</span>}
    <button type='button' className={styles.posterButton} onClick={openDetail} aria-label={`View details for ${item.title}`}>
      <Poster src={item.poster} />
      <span className={styles.veil}>View details <Icon name='arrow-up-right' /></span>
    </button>
    <div className={styles.info}>
      <span className={styles.title} title={item.title}>{item.title}</span>
      <TicketMeta rating={item.rating} year={item.releaseDate?.slice(0, 4) || 'MOVIE'} highlight />
      {reason && <p className={styles.reason}>{reason}</p>}
      <LibraryActions movieId={item.id} compact />
    </div>
  </article>;
}
