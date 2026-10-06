/* eslint-disable @next/next/no-img-element */
import dynamic from 'next/dynamic';
import { useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/router';

import styles from '../../styles/Cards.module.scss';
import { Genre, Movie } from '../../types';
import { ModalContext } from '../../context/ModalContext';
import { Add, Play, Down, Like, Dislike } from '../../utils/icons';

const Button = dynamic(import('../Button'));

interface FeatureCardProps {
  index: number;
  item: Movie;
}

export default function FeatureCard({ index, item }: FeatureCardProps): React.ReactElement {
  const { title, poster, banner, rating, genre } = item;
  const [isHovered, setIsHovered] = useState(false);
  const [backdropReady, setBackdropReady] = useState(false);

  useEffect(() => {
    setBackdropReady(false);
    if (banner === poster) return;

    let active = true;
    const preview = new Image();
    preview.onload = () => { if (active) setBackdropReady(true); };
    preview.src = banner;
    if (preview.complete && preview.naturalWidth > 0) setBackdropReady(true);

    return () => { active = false; };
  }, [banner, poster]);

  const image = isHovered && backdropReady ? banner : poster;

  const router = useRouter();
  const { setModalData, setIsModal } = useContext(ModalContext);

  const onClick = (data: Movie, watchTrailer = false) => {
    setModalData(data);
    setIsModal(true);
    const url = '/movies/' + data.id + (watchTrailer ? '?trailer=1' : '');
    void router.push(url, undefined, { scroll: false });
  };

  return (
    <div className={styles.container}>
      <div className={styles.rank}>{index}</div>

      <div className={styles.featureCard} onMouseEnter={() => setIsHovered(true)} onMouseLeave={() => setIsHovered(false)}>
        <img src={image} alt={title} className={styles.poster} onClick={() => onClick(item)} />

        <div className={styles.info}>
          <div className={styles.actionRow}>
            <div className={styles.actionRow}>
              <Button Icon={Play} rounded filled onClick={() => onClick(item, true)} />
              <Button Icon={Add} rounded />
              <Button Icon={Like} rounded />
              <Button Icon={Dislike} rounded />
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
