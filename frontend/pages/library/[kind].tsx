import Head from 'next/head';
import { GetServerSideProps } from 'next';
import Link from 'next/link';
import { useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../../components/Layout';
import Modal from '../../components/Modal';
import MovieCard from '../../components/List/MovieCard';
import { ModalContext } from '../../context/ModalContext';
import { MovieSummary, PageResult, toMovie } from '../../lib/movies';
import styles from '../../styles/LibraryPage.module.scss';

export default function LibraryPage() {
  const router = useRouter();
  const { isModal } = useContext(ModalContext);
  const kind = router.query.kind === 'favorites' || router.query.kind === 'watchlist' ? router.query.kind : null;
  const page = Number(router.query.page || 1);
  const returnPath = router.asPath;
  const [results, setResults] = useState<PageResult<MovieSummary> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const onChange = () => setRevision(value => value + 1);
    window.addEventListener('wtw-library-change', onChange);
    return () => window.removeEventListener('wtw-library-change', onChange);
  }, []);
  useEffect(() => {
    if (!router.isReady || !kind) return;
    let active = true;
    setLoading(true);
    setError('');
    fetch(`/api/library/${kind}?page=${Number.isSafeInteger(page) && page > 0 ? page : 1}`)
      .then(async response => {
        if (response.status === 401) { void router.replace('/login?next=' + encodeURIComponent(returnPath)); return null; }
        const body = await response.json();
        if (!response.ok) throw new Error(body.message || 'Không tải được danh sách.');
        return body as PageResult<MovieSummary>;
      })
      .then(body => { if (active && body) setResults(body); })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : 'Không tải được danh sách.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [router, router.isReady, returnPath, kind, page, revision]);
  const title = kind === 'favorites' ? 'Phim yêu thích' : 'Danh sách xem sau';
  if (router.isReady && !kind) return <Layout><main className={styles.page}><h1>Không tìm thấy danh sách</h1></main></Layout>;
  return <>
    <Head><title>{title} | WhatToWatch</title></Head>
    {isModal && <Modal />}
    <Layout><main className={styles.page}>
      <span className={styles.eyebrow}>BỘ SƯU TẬP CỦA BẠN</span>
      <h1>{title}</h1>
      <nav className={styles.tabs} aria-label='Danh sách đã lưu'>
        <Link href='/library/favorites'><a aria-current={kind === 'favorites' ? 'page' : undefined}>Yêu thích</a></Link>
        <Link href='/library/watchlist'><a aria-current={kind === 'watchlist' ? 'page' : undefined}>Xem sau</a></Link>
      </nav>
      {loading && <p role='status'>Đang tải danh sách…</p>}
      {error && <p role='alert' className={styles.error}>{error}</p>}
      {!loading && results && <>
        <p className={styles.count}>{results.totalElements} phim đã lưu</p>
        {results.data.length === 0 && <p>Danh sách còn trống. <Link href='/browse'><a>Khám phá phim</a></Link> để bắt đầu.</p>}
        <div className={styles.grid}>{results.data.map(movie => <MovieCard key={movie.id} item={toMovie(movie)} />)}</div>
        {results.totalPages > 1 && <div className={styles.pagination}>
          <button disabled={page <= 1} onClick={() => void router.push(`/library/${kind}?page=${page - 1}`)}>Trang trước</button>
          <span>Trang {page} / {results.totalPages}</span>
          <button disabled={page >= results.totalPages} onClick={() => void router.push(`/library/${kind}?page=${page + 1}`)}>Trang sau</button>
        </div>}
      </>}
    </main></Layout>
  </>;
}

export const getServerSideProps: GetServerSideProps = async () => ({ props: {} });
