import Head from 'next/head';
import { FormEvent, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
import Modal from '../components/Modal';
import MovieCard from '../components/List/MovieCard';
import { ModalContext } from '../context/ModalContext';
import { MovieSummary, PageResult, toMovie } from '../lib/movies';
import styles from '../styles/LibraryPage.module.scss';

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

  return <>
    <Head><title>Search movies | WhatToWatch</title></Head>
    {isModal && <Modal />}
    <Layout><main className={styles.page}>
      <span className={styles.eyebrow}>EXPLORE WHAT TO WATCH</span>
      <h1>Search for a movie</h1>
      <form className={styles.searchForm} onSubmit={submit}>
        <label htmlFor='movie-query'>Movie title</label>
        <div><input id='movie-query' value={input} onChange={event => setInput(event.target.value)}
          maxLength={100} placeholder='For example: The Godfather' autoComplete='off' />
          <button type='submit'>Search</button></div>
      </form>
      {!query && <p>Enter a movie title to search the collection.</p>}
      {loading && <p role='status'>Searching movies…</p>}
      {error && <p role='alert' className={styles.error}>{error}</p>}
      {!loading && results && <>
        <p className={styles.count}>{results.totalElements} results for “{query}”</p>
        {results.data.length === 0 && <p>No matching movies found. Try another title.</p>}
        <div className={styles.grid}>{results.data.map(movie => <MovieCard key={movie.id} item={toMovie(movie)} />)}</div>
        {results.totalPages > 1 && <div className={styles.pagination}>
          <button disabled={page <= 0} onClick={() => void router.push('/search?q=' + encodeURIComponent(query) + '&page=' + (page - 1))}>Previous</button>
          <span>Page {(Number.isSafeInteger(page) ? page : 0) + 1} / {results.totalPages}</span>
          <button disabled={page + 1 >= results.totalPages} onClick={() => void router.push('/search?q=' + encodeURIComponent(query) + '&page=' + (page + 1))}>Next</button>
        </div>}
      </>}
    </main></Layout>
  </>;
}
