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
        if (!response.ok) throw new Error(body.message || 'Không thể tìm kiếm phim.');
        return body as PageResult<MovieSummary>;
      })
      .then(body => { if (active) setResults(body); })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : 'Không thể tìm kiếm phim.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [router.isReady, query, page]);

  function submit(event: FormEvent) {
    event.preventDefault();
    if (input.trim()) void router.push('/search?q=' + encodeURIComponent(input.trim()));
  }

  return <>
    <Head><title>Tìm kiếm phim | WhatToWatch</title></Head>
    {isModal && <Modal />}
    <Layout><main className={styles.page}>
      <span className={styles.eyebrow}>KHÁM PHÁ WHAT TO WATCH</span>
      <h1>Tìm phim theo tên</h1>
      <form className={styles.searchForm} onSubmit={submit}>
        <label htmlFor='movie-query'>Tên phim</label>
        <div><input id='movie-query' value={input} onChange={event => setInput(event.target.value)}
          maxLength={100} placeholder='Ví dụ: The Godfather' autoComplete='off' />
          <button type='submit'>Tìm phim</button></div>
      </form>
      {!query && <p>Nhập tên phim để tìm trong bộ sưu tập.</p>}
      {loading && <p role='status'>Đang tìm phim…</p>}
      {error && <p role='alert' className={styles.error}>{error}</p>}
      {!loading && results && <>
        <p className={styles.count}>{results.totalElements} kết quả cho “{query}”</p>
        {results.data.length === 0 && <p>Chưa tìm thấy phim phù hợp. Hãy thử tên khác.</p>}
        <div className={styles.grid}>{results.data.map(movie => <MovieCard key={movie.id} item={toMovie(movie)} />)}</div>
        {results.totalPages > 1 && <div className={styles.pagination}>
          <button disabled={page <= 0} onClick={() => void router.push('/search?q=' + encodeURIComponent(query) + '&page=' + (page - 1))}>Trang trước</button>
          <span>Trang {(Number.isSafeInteger(page) ? page : 0) + 1} / {results.totalPages}</span>
          <button disabled={page + 1 >= results.totalPages} onClick={() => void router.push('/search?q=' + encodeURIComponent(query) + '&page=' + (page + 1))}>Trang sau</button>
        </div>}
      </>}
    </main></Layout>
  </>;
}
