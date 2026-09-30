/* eslint-disable @next/next/no-img-element */
import React, { useCallback, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import styles from '../../styles/Modal.module.scss';
import { ModalContext } from '../../context/ModalContext';
import { Play, Add, Like, Dislike } from '../../utils/icons';
import Button from '../Button';
import { Genre } from '../../types';
import { Trailer, youtubeTrailerSearchUrl } from '../../lib/movies';

export default function Modal() {
  const router = useRouter();
  const { modalData, setIsModal, isModal } = useContext(ModalContext);
  const { title, banner, rating, overview, genre, runtime, cast, releaseDate, id } = modalData;
  const [trailerKey, setTrailerKey] = useState('');
  const [trailerError, setTrailerError] = useState('');
  const [trailerUnavailable, setTrailerUnavailable] = useState(false);

  function close() {
    setIsModal(false);
    if (router.pathname === '/movies/[id]') void router.replace('/browse', undefined, { scroll: false });
  }

  const loadTrailer = useCallback(async () => {
    if (!id) return;
    setTrailerError('');
    setTrailerUnavailable(false);
    if (modalData.trailerKey) {
      setTrailerKey(modalData.trailerKey);
      return;
    }
    if (modalData.trailerKey === null) return;
    try {
      const response = await fetch('/api/movies/' + encodeURIComponent(id) + '/trailer');
      const body = await response.json();
      if (response.status === 404) {
        setTrailerUnavailable(true);
        return;
      }
      if (!response.ok) throw new Error(body.message || 'Không tải được trailer');
      setTrailerKey((body as Trailer).trailerKey);
    } catch (reason) {
      setTrailerError(reason instanceof Error ? reason.message : 'Không tải được trailer');
    }
  }, [id, modalData.trailerKey]);

  useEffect(() => {
    setTrailerKey('');
    setTrailerError('');
    setTrailerUnavailable(false);
  }, [id]);

  useEffect(() => {
    if (isModal && router.query.trailer === '1') void loadTrailer();
  }, [isModal, router.query.trailer, loadTrailer]);

  return (
    <div className={styles.container} style={{ display: isModal ? 'flex' : 'none' }}>
      <div className={styles.overlay} onClick={close}></div>
      <div className={styles.modal}>
        <div className={styles.spotlight}>
          <img src={banner} alt='spotlight' className={styles.spotlight__image} />
          <div className={styles.details}>
            <div className={styles.title}>{title}</div>
            <div className={styles.buttonRow}>
              {modalData.trailerKey === null
                ? <a className={styles.trailerLink} href={youtubeTrailerSearchUrl(title, releaseDate)}
                    target='_blank' rel='noopener noreferrer'>
                    <Play /> Tìm trailer trên YouTube
                  </a>
                : <Button label='Watch Trailer' filled Icon={Play} onClick={() => void loadTrailer()} />}
              <Button Icon={Add} rounded />
              <Button Icon={Like} rounded />
              <Button Icon={Dislike} rounded />
            </div>
            {(trailerUnavailable || trailerError) &&
              <p role={trailerError ? 'alert' : 'status'} className={styles.trailerError}>
                {trailerError || 'Phim này chưa có trailer được gắn sẵn.'}{' '}
                <a href={youtubeTrailerSearchUrl(title, releaseDate)} target='_blank' rel='noopener noreferrer'>
                  Tìm trailer trên YouTube
                </a>
              </p>}
          </div>
        </div>

        <div className={styles.cross} onClick={close} role='button' aria-label='Close details'>
          &#10005;
        </div>
        <div className={styles.bottomContainer}>
          <div className={styles.column}>{overview}</div>
          <div className={styles.column}>
            <div className={styles.metadataRow}>
              <span className={styles.greenText}>{Math.round(rating * 10)}% Match</span>
              {releaseDate && <span>Year: {releaseDate.slice(0, 4)}</span>}
            </div>
            <div className={styles.genre}>Genre: {renderGenre(genre)} </div>
            {runtime && <div>Runtime: {runtime} min</div>}
            {cast && <div>Cast: {cast}</div>}
          </div>
        </div>
        {trailerKey && <div className={styles.trailerFrame}>
          <iframe title={'Trailer ' + title}
            src={'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(trailerKey) + '?autoplay=1&rel=0'}
            allow='autoplay; encrypted-media; picture-in-picture'
            allowFullScreen />
          <a className={styles.youtubeLink}
            href={'https://www.youtube.com/watch?v=' + encodeURIComponent(trailerKey)}
            target='_blank' rel='noopener noreferrer'>Mở trên YouTube</a>
        </div>}
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
