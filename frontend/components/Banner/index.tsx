import { useContext, useEffect, useState } from 'react';
import { ModalContext } from '../../context/ModalContext';
import { useRouter } from 'next/router';
import axios from 'axios';

import { Media } from '../../types';
import { MovieSummary, toMedia } from '../../lib/movies';
import LibraryActions from '../LibraryActions';
import Button from '../ui/Button';
import Icon from '../ui/Icon';
import Poster from '../ui/Poster';
import TicketMeta from '../ui/TicketMeta';
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

  if (!media) {
    return <section className={styles.hero} aria-label='Featured movie'>
      <div className={styles.panel}>
        <span className={styles.eyebrow}>FEATURED MOVIE</span>
        <h1 className={styles.title}>Discover your next story</h1>
        <p className={styles.synopsis}>Find a movie that fits your mood in the WhatToWatch collection.</p>
      </div>
      <div className={`${styles.art} ${styles.empty}`}><Icon name='film' size={40} /></div>
    </section>;
  }

  return <section className={styles.hero} aria-label='Featured movie'>
    <div className={styles.panel}>
      <span className={styles.eyebrow}><span className={styles.stamp}>TOP 10</span>FEATURED MOVIE</span>
      <h1 className={styles.title}>{media.title}</h1>
      <TicketMeta rating={media.rating} year={media.releaseDate?.slice(0, 4)} runtime={media.runtime} highlight />
      <p className={styles.synopsis}>{media.overview || 'No overview is available for this movie.'}</p>
      <div className={styles.actions}>
        <Button variant='primary' icon='info' onClick={openDetail}>View details</Button>
        <LibraryActions movieId={media.id} />
      </div>
    </div>
    <div className={`${styles.art} ${hasBackdrop ? '' : styles.posterArt}`}>
      {hasBackdrop
        // eslint-disable-next-line @next/next/no-img-element
        ? <img src={media.banner} alt='' onError={event => { event.currentTarget.src = '/assets/poster-placeholder.svg'; }} />
        : <div className={styles.posterWrap}><Poster src={media.poster} alt={media.title} /></div>}
      <span className={styles.index} aria-hidden='true'>TOP 10 / WHAT TO WATCH</span>
    </div>
  </section>;
}
