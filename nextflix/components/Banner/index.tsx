/* eslint-disable @next/next/no-img-element */
import { useContext, useEffect, useState } from 'react';
import { ModalContext } from '../../context/ModalContext';
import { useRouter } from 'next/router';
import axios from 'axios';

import Button from '../Button';
import { Media } from '../../types';
import { MovieSummary, toMedia } from '../../lib/movies';
import { Play, Info } from '../../utils/icons';
import styles from '../../styles/Banner.module.scss';

export default function Banner() {
  const [media, setMedia] = useState<Media>();
  const router = useRouter();
  const { setModalData, setIsModal } = useContext(ModalContext);

  useEffect(() => {
    axios.get<MovieSummary[]>('/api/movies/top-rated')
      .then(result => {
        if (result.data.length) setMedia(toMedia(result.data[0]));
      })
      .catch(() => setMedia(undefined));
  }, []);

  const openDetail = (watchTrailer = false) => {
    if (!media) return;
    setModalData(media);
    setIsModal(true);
    const url = '/movies/' + media.id + (watchTrailer ? '?trailer=1' : '');
    void router.push(url, undefined, { scroll: false });
  };

  return (
    <div className={styles.spotlight}>
      <img src={media?.banner} alt='spotlight' className={styles.spotlight__image} />
      <div className={styles.spotlight__details}>
        <div className={styles.title}>{media?.title}</div>
        <div className={styles.synopsis}>{media?.overview}</div>
        <div className={styles.buttonRow}>
          <Button label='More Info' filled Icon={Info} onClick={() => openDetail()} />
          {media && <Button label='Watch Trailer' Icon={Play} onClick={() => openDetail(true)} />}
        </div>
      </div>
    </div>
  );
}
