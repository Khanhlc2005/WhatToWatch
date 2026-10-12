/* eslint-disable @next/next/no-img-element */
import React, { useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import styles from '../../styles/Modal.module.scss';
import { ModalContext } from '../../context/ModalContext';
import { Genre } from '../../types';
import { Trailer, youtubeTrailerSearchUrl } from '../../lib/movies';
import LibraryActions from '../LibraryActions';
import MovieRow from '../List/MovieRow';
import MovieRating from '../MovieRating';
import { readApiJson } from '../../lib/readApiJson';

export default function Modal() {
  const router = useRouter();
  const { modalData, setIsModal, isModal } = useContext(ModalContext);
  const { title, banner, rating, overview, genre, runtime, cast, releaseDate, id } = modalData;
  const [trailerKey, setTrailerKey] = useState('');
  const [trailerError, setTrailerError] = useState('');
  const [trailerUnavailable, setTrailerUnavailable] = useState(false);
  const [videoReady, setVideoReady] = useState(false);

  function close() {
    setIsModal(false);
    if (router.pathname === '/movies/[id]') {
      const from = typeof router.query.from === 'string' ? router.query.from : '';
      const destination = from.startsWith('/') && !from.startsWith('//') && !from.startsWith('/movies/') ? from : '/browse';
      void router.replace(destination, undefined, { scroll: false });
    }
  }

  useEffect(() => {
    setTrailerKey('');
    setTrailerError('');
    setTrailerUnavailable(false);
    setVideoReady(false);
    if (!isModal || !id) return;

    if (modalData.trailerKey) {
      if (/^[A-Za-z0-9_-]{11}$/.test(modalData.trailerKey)) {
        setTrailerKey(modalData.trailerKey);
        return;
      }
    }

    const controller = new AbortController();
    fetch('/api/movies/' + encodeURIComponent(id) + '/trailer', { signal: controller.signal })
      .then(async response => {
        if (response.status === 404) {
          if (!controller.signal.aborted) setTrailerUnavailable(true);
          return null;
        }
        const body = await readApiJson<Trailer & { message?: string }>(response, 'Could not load the trailer.');
        if (!response.ok) throw new Error(body.message || 'Could not load the trailer.');
        return body as Trailer;
      })
      .then(trailer => {
        if (!trailer || controller.signal.aborted) return;
        if (/^[A-Za-z0-9_-]{11}$/.test(trailer.trailerKey)) setTrailerKey(trailer.trailerKey);
        else setTrailerError('The trailer is invalid.');
      })
      .catch(reason => {
        if (reason instanceof Error && reason.name !== 'AbortError')
          setTrailerError(reason.message || 'Could not load the trailer.');
      });
    return () => controller.abort();
  }, [isModal, id, modalData.trailerKey]);

  const trailerUrl = trailerKey
    ? `https://www.youtube-nocookie.com/embed/${trailerKey}?autoplay=1&mute=1&playsinline=1&controls=1&rel=0`
    : '';

  return (
    <div className={styles.container} style={{ display: isModal ? 'flex' : 'none' }}>
      <div className={styles.overlay} onClick={close}></div>
      <div className={styles.modal}>
        <div className={styles.spotlight}>
          <img src={banner} alt='' className={`${styles.spotlight__image} ${videoReady ? styles.imageHidden : ''}`} />
          {trailerKey && <div className={styles.trailerFrame}>
            <iframe key={trailerKey} title={'Trailer ' + title} src={trailerUrl} loading='eager'
              allow='autoplay; encrypted-media; picture-in-picture' allowFullScreen
              onLoad={() => setVideoReady(true)} />
          </div>}
        </div>
        <div className={styles.cross} onClick={close} role='button' aria-label='Close movie details'>
          &#10005;
        </div>
        <div className={styles.details}>
          <div className={styles.title}>{title}</div>
          <LibraryActions movieId={id} />
          {id && <MovieRating movieId={id} />}
          {trailerKey && <p className={styles.trailerHint}>The trailer starts muted. You can turn on sound in the video player.</p>}
          {(trailerUnavailable || trailerError) &&
            <p role={trailerError ? 'alert' : 'status'} className={styles.trailerError}>
              {trailerError || 'No trailer is available for this movie.'}{' '}
              <a href={youtubeTrailerSearchUrl(title, releaseDate)} target='_blank' rel='noopener noreferrer'>
                Search for a trailer on YouTube
              </a>
            </p>}
        </div>
        <div className={styles.bottomContainer}>
          <div className={styles.column}><h3>Overview</h3><p>{overview || 'No overview is available for this movie.'}</p></div>
          <div className={styles.column}>
            <div className={styles.metadataRow}>
              <span className={styles.greenText}>{rating == null ? 'Not rated' : `IMDb ${rating.toFixed(1)}/10`}</span>
              {releaseDate && <span>Year: {releaseDate.slice(0, 4)}</span>}
            </div>
            {genre.length > 0 && <div className={styles.genre}>Genres: {renderGenre(genre)} </div>}
            {runtime && <div>Runtime: {runtime} minutes</div>}
            <div><strong>Cast:</strong> {cast || 'No cast information available.'}</div>
          </div>
        </div>
        <section className={styles.related}>
          <h3>Similar language and era</h3>
          <p>Movies from around the same time with the same original language.</p>
          {modalData.similarMovies?.length ? <MovieRow movies={modalData.similarMovies} /> : <p>No similar movies found.</p>}
        </section>
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
            <span>&nbsp;{item.name}</span>
            {!isLast && <div>,</div>}
          </div>
        );
      })}
    </div>
  );
}
