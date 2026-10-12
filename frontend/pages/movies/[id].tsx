import Head from 'next/head';
import { useRouter } from 'next/router';
import { useContext, useEffect, useState } from 'react';
import { ModalContext } from '../../context/ModalContext';
import { MovieDetail, toMedia } from '../../lib/movies';
import { readApiJson } from '../../lib/readApiJson';
import styles from '../../styles/WhatToWatch.module.scss';

export default function MoviePage() {
  const router = useRouter();
  const id = router.query.id;
  const { setModalData, setIsModal } = useContext(ModalContext);
  const [error, setError] = useState('');

  useEffect(() => {
    if (typeof id !== 'string') return;
    let active = true;
    setError('');
    fetch('/api/movies/' + encodeURIComponent(id))
      .then(async response => {
        const body = await readApiJson<MovieDetail & { message?: string }>(response, 'Could not load movie details.');
        if (!response.ok) throw new Error(body.message || 'Movie not found.');
        return body as MovieDetail;
      })
      .then(movie => {
        if (!active) return;
        setModalData(toMedia(movie));
        setIsModal(true);
      })
      .catch(reason => {
        if (active) {
          setIsModal(false);
          setError(reason instanceof Error ? reason.message : 'Could not load the movie.');
        }
      });
    return () => { active = false; };
  }, [id, setIsModal, setModalData]);

  useEffect(() => () => setIsModal(false), [setIsModal]);

  return <>
    <Head><title>Movie details | WhatToWatch</title></Head>
    {error && <div role='alert' className={styles.detailError} onClick={() => router.replace('/browse', undefined, { scroll: false })}>
      {error} · Go back
    </div>}
  </>;
}
