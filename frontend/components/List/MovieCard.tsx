/* eslint-disable @next/next/no-img-element */
import { useContext } from 'react';
import { useRouter } from 'next/router';
import { Movie } from '../../types';
import { ModalContext } from '../../context/ModalContext';
import styles from '../../styles/Cards.module.scss';
import LibraryActions from '../LibraryActions';

export interface MovieCardProps { item: Movie }

export default function MovieCard({ item }: MovieCardProps): React.ReactElement {
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

  return <article className={styles.card}>
    <button className={styles.cardPosterButton} onClick={openDetail} aria-label={`Xem chi tiết ${item.title}`}>
      <img src={item.poster} alt='' className={styles.cardPoster} loading='lazy'
        onError={event => {
          if (event.currentTarget.getAttribute('src') !== '/assets/poster-placeholder.svg') {
            event.currentTarget.src = '/assets/poster-placeholder.svg';
          }
        }} />
      <span className={styles.cardOverlay}>Xem chi tiết ↗</span>
    </button>
    <div className={styles.cardInfo}>
      <span className={styles.cardTitle} title={item.title}>{item.title}</span>
      <div className={styles.cardMeta}>
        <span className={styles.cardRating}>{item.rating == null ? 'Chưa có điểm' : `★ ${item.rating.toFixed(1)}`}</span>
        <span>{item.releaseDate?.slice(0, 4) || 'Phim điện ảnh'}</span>
      </div>
      <LibraryActions movieId={item.id} compact />
    </div>
  </article>;
}
