/* eslint-disable @next/next/no-img-element */
import { useContext, useEffect, useState } from 'react';
import { ModalContext } from '../../context/ModalContext';
import { useRouter } from 'next/router';
import axios from 'axios';

import { Media } from '../../types';
import { MovieSummary, toMedia } from '../../lib/movies';
import { Info } from '../../utils/icons';
import styles from '../../styles/Banner.module.scss';

export default function Banner() {
  const [media, setMedia] = useState<Media>();
  const router = useRouter();
  const { setModalData, setIsModal } = useContext(ModalContext);
  const hasBackdrop = Boolean(media && media.banner !== media.poster);

  useEffect(() => {
    let active = true;
    axios.get<MovieSummary[]>('/api/movies/top-rated')
      .then(result => {
        if (!active || !result.data.length) return;
        const topTen = result.data.slice(0, 10);
        let previousId: string | null = null;
        try { previousId = sessionStorage.getItem('wtw_featured_movie_id'); } catch { /* Storage is optional. */ }
        const choices = topTen.length > 1
          ? topTen.filter(movie => String(movie.id) !== previousId)
          : topTen;
        const featured = toMedia(choices[Math.floor(Math.random() * choices.length)]);
        try { sessionStorage.setItem('wtw_featured_movie_id', featured.id); } catch { /* Storage is optional. */ }
        setMedia(featured);
        return axios.get('/api/movies/' + featured.id)
          .then(detail => { if (active) setMedia(toMedia(detail.data)); })
          .catch(() => undefined);
      })
      .catch(() => { if (active) setMedia(undefined); });
    return () => { active = false; };
  }, []);

  const openDetail = () => {
    if (!media) return;
    setModalData(media);
    setIsModal(true);
    const url = '/movies/' + media.id;
    void router.push(url, undefined, { scroll: false });
  };

  return (
    <section className={styles.spotlight} aria-label='Featured movie'>
      {media?.banner && <img
        src={media.banner}
        alt=''
        className={`${styles.spotlight__image} ${hasBackdrop ? '' : styles.posterImage}`}
        onError={event => {
          if (event.currentTarget.getAttribute('src') !== '/assets/poster-placeholder.svg') {
            event.currentTarget.src = '/assets/poster-placeholder.svg';
          }
        }}
      />}
      <div className={styles.spotlight__shade} />
      <div className={styles.spotlight__details}>
        <span className={styles.kicker}><span className={styles.kickerLine} /> FEATURED MOVIE</span>
        <h2 className={styles.title}>{media?.title || 'Discover your next story'}</h2>
        <div className={styles.metadata}>
          {media?.rating != null && <span className={styles.rating} aria-label={`IMDb rating ${media.rating.toFixed(1)} out of 10`}>IMDb ★ {media.rating.toFixed(1)} / 10</span>}
          {media?.releaseDate && <span className={styles.releaseYear}>{media.releaseDate.slice(0, 4)}</span>}
        </div>
        <p className={styles.synopsis}>{media?.overview || 'Find a movie that fits your mood in the WhatToWatch collection.'}</p>
        {media && <button className={styles.detailButton} onClick={openDetail}>
          <Info aria-hidden='true' /> View details <span aria-hidden='true'>↗</span>
        </button>}
      </div>
      <div className={styles.heroIndex} aria-hidden='true'>TOP 10 / WHAT TO WATCH</div>
    </section>
  );
}
