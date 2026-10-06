/* eslint-disable @next/next/no-img-element */
import { useContext } from 'react';
import { useRouter } from 'next/router';
import dynamic from 'next/dynamic';

import { Genre, Movie } from '../../types';
import styles from '../../styles/Cards.module.scss';
import { ModalContext } from '../../context/ModalContext';
import { Add, Play, Down, Like, Dislike } from '../../utils/icons';

const Button = dynamic(import('../Button'));

export interface MovieCardProps {
  defaultCard?: boolean;
  item: Movie;
}

export default function MovieCard({ defaultCard = true, item }: MovieCardProps): React.ReactElement {
  const style = defaultCard ? styles.card : styles.longCard;
  const infoStyle = defaultCard ? styles.cardInfo : styles.more;
  const { title, poster, banner, rating, genre } = item;
  const image = defaultCard ? banner : poster;

  const router = useRouter();
  const { setModalData, setIsModal } = useContext(ModalContext);

  const onClick = (data: Movie, watchTrailer = false) => {
    setModalData(data);
    setIsModal(true);
    const url = '/movies/' + data.id + (watchTrailer ? '?trailer=1' : '');
    void router.push(url, undefined, { scroll: false });
  };

  return (
    <div className={style}>
      <img src={image} alt={title} className={styles.cardPoster} onClick={() => onClick(item)} />
      <div className={infoStyle}>
        <div className={styles.actionRow}>
          <div className={styles.actionRow}>
            <Button Icon={Play} rounded filled onClick={() => onClick(item, true)} />
            <Button Icon={Add} rounded />
            {defaultCard && (
              <>
                <Button Icon={Like} rounded />
                <Button Icon={Dislike} rounded />
              </>
            )}
          </div>
          <Button Icon={Down} rounded onClick={() => onClick(item)} />
        </div>
        <div className={styles.textDetails}>
          <strong>{title}</strong>
          <div className={styles.row}>
            <span className={styles.greenText}>{rating == null ? 'Chưa có điểm' : `${rating}/10`}</span>
            {/* <span className={styles.regularText}>length </span> */}
          </div>
          {renderGenre(genre)}
        </div>
      </div>
    </div>
  );
}

function renderGenre(genre: Genre[]) {
  return (
    <div className={styles.row}>
      {genre.map((item, index) => {
        const isLast = index === genre.length - 1;
        return (
          <div key={index} className={styles.row}>
            <span className={styles.regularText}>{item.name}</span>
            {!isLast && <div className={styles.dot}>&bull;</div>}
          </div>
        );
      })}
    </div>
  );
}
