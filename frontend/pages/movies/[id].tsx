import Head from 'next/head';
import { useRouter } from 'next/router';
import { useContext, useEffect, useState } from 'react';
import { ModalContext } from '../../context/ModalContext';
import { MovieDetail, toMedia } from '../../lib/movies';
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
        const body = await response.json();
        if (!response.ok) throw new Error(body.message || 'Không tìm thấy phim');
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
          setError(reason instanceof Error ? reason.message : 'Không tải được phim');
        }
      });
    return () => { active = false; };
  }, [id, setIsModal, setModalData]);

  useEffect(() => () => setIsModal(false), [setIsModal]);

  return <>
    <Head><title>Chi tiết phim | WhatToWatch</title></Head>
    {error && <div role='alert' className={styles.detailError} onClick={() => router.replace('/browse', undefined, { scroll: false })}>
      {error} · Quay lại
    </div>}
  </>;
}
