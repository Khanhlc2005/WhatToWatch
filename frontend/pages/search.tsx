import Head from 'next/head';
import { FormEvent, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
import Modal from '../components/Modal';
import MovieCard from '../components/List/MovieCard';
import { ModalContext } from '../context/ModalContext';
import { MovieSummary, PageResult, toMovie } from '../lib/movies';
import { DISCOVER_ENABLED } from '../config/features';
import styles from '../styles/Page.module.scss';
import Button from '../components/ui/Button';
import Icon from '../components/ui/Icon';
import Pagination from '../components/ui/Pagination';
import StatusNote from '../components/ui/StatusNote';
import TicketMeta from '../components/ui/TicketMeta';
import Link from 'next/link';

export default function Search() {
  const router = useRouter();
  const { isModal } = useContext(ModalContext);
  const query = typeof router.query.q === 'string' ? router.query.q.trim() : '';
  const page = Number(router.query.page || 0);
  const [input, setInput] = useState('');
  const [results, setResults] = useState<PageResult<MovieSummary> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => { setInput(query); }, [query]);
  useEffect(() => {
    if (!router.isReady || !query) { setResults(null); return; }
    let active = true;
    setLoading(true);
    setError('');
    fetch('/api/movies/search?q=' + encodeURIComponent(query) + '&page=' + (Number.isSafeInteger(page) && page >= 0 ? page : 0))
      .then(async response => {
        const body = await response.json();
        if (!response.ok) throw new Error(body.message || 'Could not search for movies.');
        return body as PageResult<MovieSummary>;
      })
      .then(body => { if (active) setResults(body); })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : 'Could not search for movies.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [router.isReady, query, page]);

  function submit(event: FormEvent) {
    event.preventDefault();
    if (input.trim()) void router.push('/search?q=' + encodeURIComponent(input.trim()));
  }

  const currentPage = (Number.isSafeInteger(page) && page >= 0 ? page : 0) + 1;
  const goToPage = (target: number) => void router.push('/search?q=' + encodeURIComponent(query) + '&page=' + (target - 1));

  return <>
    <Head><title>Search movies | WhatToWatch</title></Head>
    {isModal && <Modal />}
    <Layout><main className={`${styles.page} ${styles.tight}`}>
      <div className={styles.head}>
        <span className={styles.eyebrow}>EXPLORE WHAT TO WATCH</span>
        <h1>Search for a movie</h1>
      </div>
      <form className={styles.search} role='search' onSubmit={submit}>
        <label htmlFor='movie-query'>Movie title</label>
        <div className={styles.searchBar}>
          <Icon name='search' size={20} />
          <input id='movie-query' value={input} onChange={event => setInput(event.target.value)}
            maxLength={100} placeholder='For example: The Godfather' autoComplete='off' />
          <Button variant='primary' type='submit'>Search</Button>
        </div>
      </form>
      {!query && <StatusNote tone='info' block>Enter a movie title to search the collection.</StatusNote>}
      {loading && <StatusNote tone='loading'>Searching movies…</StatusNote>}
      {error && <StatusNote tone='error'>{error}</StatusNote>}
      {!loading && results && <>
        <div className={styles.toolbar}>
          {results.data.length > 0 ? <TicketMeta extra={[`${results.totalElements} RESULTS FOR “${query}”`]} /> : <span />}
          {DISCOVER_ENABLED && <Link href='/discover'><a className={styles.link}>
            <Icon name='sliders' size={16} />Need more control? Try Discover
          </a></Link>}
        </div>
        {results.data.length === 0 && <StatusNote tone='empty' block title={`0 results for “${query}”`}
          action={<Button size='sm' href='/chat' icon='message'>Ask Chatbot W2W</Button>}>
          No matching movies found. Try another title.
        </StatusNote>}
        <div className={styles.grid}>{results.data.map(movie => <MovieCard key={movie.id} item={toMovie(movie)} fluid />)}</div>
        {results.totalPages > 1 && <Pagination page={currentPage} totalPages={results.totalPages} onChange={goToPage} />}
      </>}
    </main></Layout>
  </>;
}
