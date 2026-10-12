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
        if (!response.ok) throw new Error(body.message || 'Could not load your list.');
        return body as PageResult<MovieSummary>;
      })
      .then(body => { if (active && body) setResults(body); })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : 'Could not load your list.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [router, router.isReady, returnPath, kind, page, revision]);
  const title = kind === 'favorites' ? 'Favourite movies' : 'Watch later';
  if (router.isReady && !kind) return <Layout><main className={styles.page}><h1>List not found</h1></main></Layout>;
  return <>
    <Head><title>{title} | WhatToWatch</title></Head>
    {isModal && <Modal />}
    <Layout><main className={styles.page}>
      <span className={styles.eyebrow}>YOUR COLLECTION</span>
      <h1>{title}</h1>
      <nav className={styles.tabs} aria-label='Saved lists'>
        <Link href='/library/favorites'><a aria-current={kind === 'favorites' ? 'page' : undefined}>Favourite</a></Link>
        <Link href='/library/watchlist'><a aria-current={kind === 'watchlist' ? 'page' : undefined}>Watch later</a></Link>
      </nav>
      {loading && <p role='status'>Loading your list…</p>}
      {error && <p role='alert' className={styles.error}>{error}</p>}
      {!loading && results && <>
        <p className={styles.count}>{results.totalElements} saved movies</p>
        {results.data.length === 0 && <p>This list is empty. <Link href='/browse'><a>Explore movies</a></Link> to get started.</p>}
        <div className={styles.grid}>{results.data.map(movie => <MovieCard key={movie.id} item={toMovie(movie)} />)}</div>
        {results.totalPages > 1 && <div className={styles.pagination}>
          <button disabled={page <= 1} onClick={() => void router.push(`/library/${kind}?page=${page - 1}`)}>Previous</button>
          <span>Page {page} / {results.totalPages}</span>
          <button disabled={page >= results.totalPages} onClick={() => void router.push(`/library/${kind}?page=${page + 1}`)}>Next</button>
        </div>}
      </>}
    </main></Layout>
  </>;
}

export const getServerSideProps: GetServerSideProps = async () => ({ props: {} });
