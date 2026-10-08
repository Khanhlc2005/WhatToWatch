/* eslint-disable @next/next/no-img-element */
import React, { useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import styles from '../../styles/Modal.module.scss';
import { ModalContext } from '../../context/ModalContext';
import { Genre } from '../../types';
import { Trailer, youtubeTrailerSearchUrl } from '../../lib/movies';
import LibraryActions from '../LibraryActions';
import MovieRow from '../List/MovieRow';

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
        const body = await response.json();
        if (!response.ok) throw new Error(body.message || 'Không tải được trailer');
        return body as Trailer;
      })
      .then(trailer => {
        if (!trailer || controller.signal.aborted) return;
        if (/^[A-Za-z0-9_-]{11}$/.test(trailer.trailerKey)) setTrailerKey(trailer.trailerKey);
        else setTrailerError('Trailer không hợp lệ.');
      })
      .catch(reason => {
        if (reason instanceof Error && reason.name !== 'AbortError')
          setTrailerError(reason.message || 'Không tải được trailer.');
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
        <div className={styles.cross} onClick={close} role='button' aria-label='Đóng chi tiết phim'>
          &#10005;
        </div>
        <div className={styles.details}>
          <div className={styles.title}>{title}</div>
          <LibraryActions movieId={id} />
          {trailerKey && <p className={styles.trailerHint}>Trailer tự phát ở chế độ tắt tiếng. Bạn có thể bật tiếng trong khung video.</p>}
          {(trailerUnavailable || trailerError) &&
            <p role={trailerError ? 'alert' : 'status'} className={styles.trailerError}>
              {trailerError || 'Phim này chưa có trailer để phát tự động.'}{' '}
              <a href={youtubeTrailerSearchUrl(title, releaseDate)} target='_blank' rel='noopener noreferrer'>
                Tìm trailer trên YouTube
              </a>
            </p>}
        </div>
        <div className={styles.bottomContainer}>
          <div className={styles.column}><h3>Giới thiệu</h3><p>{overview || 'Phim này chưa có mô tả.'}</p></div>
          <div className={styles.column}>
            <div className={styles.metadataRow}>
              <span className={styles.greenText}>{rating == null ? 'Chưa có điểm' : `${rating}/10`}</span>
              {releaseDate && <span>Năm: {releaseDate.slice(0, 4)}</span>}
            </div>
            {genre.length > 0 && <div className={styles.genre}>Thể loại: {renderGenre(genre)} </div>}
            {runtime && <div>Thời lượng: {runtime} phút</div>}
            <div><strong>Diễn viên:</strong> {cast || 'Chưa có dữ liệu diễn viên.'}</div>
          </div>
        </div>
        <section className={styles.related}>
          <h3>Cùng ngôn ngữ và thời kỳ</h3>
          <p>Những phim phát hành gần thời điểm này và có cùng ngôn ngữ gốc.</p>
          {modalData.similarMovies?.length ? <MovieRow movies={modalData.similarMovies} /> : <p>Chưa có phim gợi ý phù hợp.</p>}
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
