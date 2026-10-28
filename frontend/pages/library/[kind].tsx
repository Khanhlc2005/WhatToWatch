import Head from 'next/head';
import { GetServerSideProps } from 'next';
import { useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../../components/Layout';
import Modal from '../../components/Modal';
import MovieCard from '../../components/List/MovieCard';
import { ModalContext } from '../../context/ModalContext';
import { MovieSummary, PageResult, toMovie } from '../../lib/movies';
import styles from '../../styles/Page.module.scss';
import Button from '../../components/ui/Button';
import Pagination from '../../components/ui/Pagination';
import StatusNote from '../../components/ui/StatusNote';
import Tabs from '../../components/ui/Tabs';
import TicketMeta from '../../components/ui/TicketMeta';

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
  if (router.isReady && !kind) return <Layout><main className={styles.page}><div className={styles.head}><h1>List not found</h1></div></main></Layout>;
  return <>
    <Head><title>{title} | WhatToWatch</title></Head>
    {isModal && <Modal />}
    <Layout><main className={`${styles.page} ${styles.tight}`}>
      <div className={styles.head}>
        <span className={styles.eyebrow}>YOUR COLLECTION</span>
        <h1>{title}</h1>
      </div>
      <Tabs label='Saved lists' active={kind || ''} items={[
        { id: 'favorites', label: 'Favourite', href: '/library/favorites' },
        { id: 'watchlist', label: 'Watch later', href: '/library/watchlist' }
      ]} />
      {loading && <StatusNote tone='loading'>Loading your list…</StatusNote>}
      {error && <StatusNote tone='error'>{error}</StatusNote>}
      {!loading && results && <>
        <TicketMeta extra={[`${results.totalElements} SAVED MOVIES`]} />
        {results.data.length === 0 && <StatusNote tone='empty' block
          action={<Button size='sm' href='/browse'>Explore movies</Button>}>This list is empty.</StatusNote>}
        <div className={styles.grid}>{results.data.map(movie => <MovieCard key={movie.id} item={toMovie(movie)} fluid />)}</div>
        {results.totalPages > 1 && <Pagination page={page} totalPages={results.totalPages}
          onChange={target => void router.push(`/library/${kind}?page=${target}`)} />}
      </>}
    </main></Layout>
  </>;
}

export const getServerSideProps: GetServerSideProps = async () => ({ props: {} });
