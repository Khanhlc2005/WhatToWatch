import React, { useContext, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import styles from '../../styles/Modal.module.scss';
import { ModalContext } from '../../context/ModalContext';
import { Trailer, youtubeTrailerSearchUrl } from '../../lib/movies';
import AddToList from '../AddToList';
import LibraryActions, { signedIn } from '../LibraryActions';
import { ADD_TO_LIST_ENABLED } from '../../config/features';
import MovieRow from '../List/MovieRow';
import MovieRating from '../MovieRating';
import Chip from '../ui/Chip';
import IconButton from '../ui/IconButton';
import Perforation from '../ui/Perforation';
import SectionHeading from '../ui/SectionHeading';
import StatusNote from '../ui/StatusNote';
import TicketMeta from '../ui/TicketMeta';
import { readApiJson } from '../../lib/readApiJson';

const PLACEHOLDER = '/assets/poster-placeholder.svg';

export default function Modal() {
  const router = useRouter();
  const { modalData, setIsModal, isModal } = useContext(ModalContext);
  const { title, banner, rating, overview, genre, runtime, cast, releaseDate, id } = modalData;
  const [trailerKey, setTrailerKey] = useState('');
  const [trailerError, setTrailerError] = useState('');
  const [trailerUnavailable, setTrailerUnavailable] = useState(false);
  const [videoReady, setVideoReady] = useState(false);
  const closeRef = useRef<HTMLButtonElement>(null);

  function close() {
    setIsModal(false);
    if (router.pathname === '/movies/[id]') {
      const from = typeof router.query.from === 'string' ? router.query.from : '';
      const destination = from.startsWith('/') && !from.startsWith('//') && !from.startsWith('/movies/') ? from : '/browse';
      void router.replace(destination, undefined, { scroll: false });
    }
  }

  useEffect(() => {
    if (!isModal) return;
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape') close(); };
    const overflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    document.addEventListener('keydown', onKey);
    closeRef.current?.focus();
    return () => { document.body.style.overflow = overflow; document.removeEventListener('keydown', onKey); };
    // close() only reads router state at call time.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isModal]);

  // Opening a movie records it in the watch history (the backend keeps one entry per movie).
  useEffect(() => {
    if (!isModal || !id) return;
    let active = true;
    void signedIn().then(loggedIn => {
      if (!loggedIn || !active) return;
      return fetch('/api/watch-history', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ movieId: Number(id) })
      });
    }).catch(() => undefined);
    return () => { active = false; };
  }, [isModal, id]);

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
  const year = releaseDate?.slice(0, 4);
  const genres = genre || [];

  return (
    <div className={styles.wrap} style={{ display: isModal ? 'flex' : 'none' }}>
      <div className={styles.scrim} onClick={close}></div>
      <div className={styles.modal} role='dialog' aria-modal='true' aria-label={title}>
        <IconButton ref={closeRef} icon='x' label='Close movie details' variant='float' className={styles.close} onClick={close} />
        <div className={styles.media}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={banner} alt='' className={[videoReady && styles.hidden, banner?.endsWith(PLACEHOLDER) && styles.placeholder].filter(Boolean).join(' ')}
            onError={event => { event.currentTarget.src = PLACEHOLDER; event.currentTarget.classList.add(styles.placeholder); }} />
          {trailerKey && <iframe key={trailerKey} title={'Trailer ' + title} src={trailerUrl} loading='eager'
            allow='autoplay; encrypted-media; picture-in-picture' allowFullScreen
            onLoad={() => setVideoReady(true)} />}
        </div>
        <div className={styles.head}>
          <h2 className={styles.title}>{title}</h2>
          <TicketMeta rating={rating} year={year} runtime={runtime} highlight />
          <div className={styles.actions}>
            <LibraryActions movieId={id} />
            {ADD_TO_LIST_ENABLED && id && <AddToList movieId={id} />}
          </div>
          {trailerKey && <p className={styles.hint}>The trailer starts muted. You can turn on sound in the video player.</p>}
          {(trailerUnavailable || trailerError) && <StatusNote tone={trailerError ? 'error' : 'info'}
            action={<a className={styles.link} href={youtubeTrailerSearchUrl(title, releaseDate)} target='_blank' rel='noopener noreferrer'>
              Search for a trailer on YouTube
            </a>}>
            {trailerError || 'No trailer is available for this movie.'}
          </StatusNote>}
        </div>
        <Perforation inset />
        <div className={styles.body}>
          <div className={styles.column}>
            <h3 className={styles.eyebrow}>OVERVIEW</h3>
            <p>{overview || 'No overview is available for this movie.'}</p>
            {id && <MovieRating movieId={id} />}
          </div>
          <dl className={styles.facts}>
            <dt>IMDb</dt><dd className={styles.mono}>{rating == null ? 'NOT RATED' : `${rating.toFixed(1)} / 10`}</dd>
            {year && <><dt>Year</dt><dd className={styles.mono}>{year}</dd></>}
            {runtime ? <><dt>Runtime</dt><dd className={styles.mono}>{runtime} minutes</dd></> : null}
            {genres.length > 0 && <><dt>Genres</dt><dd className={styles.chips}>{genres.map(item => <Chip key={item.id}>{item.name}</Chip>)}</dd></>}
            <dt>Cast</dt><dd>{cast || 'No cast information available.'}</dd>
          </dl>
        </div>
        <section className={styles.related}>
          <SectionHeading title='Similar language and era' />
          {modalData.similarMovies?.length ? <>
            <p className={styles.muted}>Movies from around the same time with the same original language.</p>
            <MovieRow movies={modalData.similarMovies} />
          </> : <StatusNote tone='empty'>No similar movies found.</StatusNote>}
        </section>
      </div>
    </div>
  );
}
