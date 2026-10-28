import Head from 'next/head';
import { useContext, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
import Modal from '../components/Modal';
import MovieCard from '../components/List/MovieCard';
import FilterPanel from '../components/discover/FilterPanel';
import Button from '../components/ui/Button';
import Chip from '../components/ui/Chip';
import Pagination from '../components/ui/Pagination';
import StatusNote from '../components/ui/StatusNote';
import TicketMeta from '../components/ui/TicketMeta';
import { GENRE_FILTER_ENABLED, RATING_FILTER_ENABLED } from '../config/features';
import { ModalContext } from '../context/ModalContext';
import {
  DiscoverFilters, emptyFilters, filtersFromQuery, movieGenres, pageFromQuery, queryFromFilters, rangeLabel
} from '../lib/discover';
import { MovieSummary, PageResult, toMovie } from '../lib/movies';
import page from '../styles/Page.module.scss';
import styles from '../styles/Discover.module.scss';

export default function Discover() {
  const router = useRouter();
  const { isModal } = useContext(ModalContext);
  const queryKey = JSON.stringify(router.query);
  const applied = useMemo(() => {
    const filters = filtersFromQuery(router.query);
    return GENRE_FILTER_ENABLED ? filters : { ...filters, genreIds: [] };
  },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [queryKey]);
  const current = pageFromQuery(router.query);
  const [results, setResults] = useState<PageResult<MovieSummary> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!router.isReady) return;
    let active = true;
    setLoading(true);
    setError('');
    const params = new URLSearchParams(queryFromFilters(applied, current));
    if (!RATING_FILTER_ENABLED) { params.delete('minRating'); params.delete('maxRating'); }
    fetch('/api/discover?' + params)
      .then(async response => {
        const body = await response.json();
        if (!response.ok) throw new Error(body.message || 'Could not load movies.');
        return body as PageResult<MovieSummary>;
      })
      .then(body => { if (active) setResults(body); })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : 'Could not load movies.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [router.isReady, applied, current]);

  const apply = (filters: DiscoverFilters, target = 1) =>
    void router.push({ pathname: '/discover', query: queryFromFilters(filters, target) }, undefined, { scroll: false });
  const genreName = (id: number) => movieGenres.find(genre => genre.id === id)?.name || String(id);
  const ranges = [
    rangeLabel(applied.yearFrom, applied.yearTo),
    RATING_FILTER_ENABLED ? rangeLabel(applied.minRating, applied.maxRating, 'IMDb ') : null,
    rangeLabel(applied.minRuntime, applied.maxRuntime, '', ' MIN'),
    applied.language ? applied.language.toUpperCase() : null
  ].filter(Boolean) as string[];

  return <>
    <Head><title>Discover movies | WhatToWatch</title></Head>
    {isModal && <Modal />}
    <Layout><main className={`${page.page} ${page.tight}`}>
      <div className={page.head}>
        <span className={page.eyebrow}>EXPLORE THE COLLECTION</span>
        <h1>Discover movies</h1>
        <p>Narrow the catalogue by genre, era, rating, language and runtime.</p>
      </div>
      {(!RATING_FILTER_ENABLED || !GENRE_FILTER_ENABLED) && <StatusNote tone='info'>
        {[!GENRE_FILTER_ENABLED && 'The genre filter is paused until the catalogue has genre data.',
          !RATING_FILTER_ENABLED && 'The IMDb rating filter is paused until the backend filters on the same score the cards show.']
          .filter(Boolean).join(' ')} The other filters work.
      </StatusNote>}
      <div className={styles.layout}>
        <div className={styles.side}>
          <FilterPanel applied={applied} ratingEnabled={RATING_FILTER_ENABLED} genresEnabled={GENRE_FILTER_ENABLED} onApply={filters => apply(filters)} />
        </div>
        <section className={styles.results} aria-label='Results' aria-busy={loading}>
          <div className={styles.summary}>
            {results && !loading && <TicketMeta extra={[`${results.totalElements} RESULTS`]} />}
            {applied.genreIds.map(id => <Chip key={id} selected
              onClick={() => apply({ ...applied, genreIds: applied.genreIds.filter(item => item !== id) })}>{genreName(id)}</Chip>)}
            {ranges.map(label => <Chip key={label}>{label}</Chip>)}
          </div>
          {loading && <StatusNote tone='loading'>Finding movies…</StatusNote>}
          {error && <StatusNote tone='error'>{error}</StatusNote>}
          {!loading && !error && results && results.data.length === 0 && <StatusNote tone='empty' block title='No movies match these filters'
            action={<Button size='sm' onClick={() => apply(emptyFilters)}>Reset all</Button>}>
            Try a wider year or runtime range, or fewer genres.
          </StatusNote>}
          {!loading && results && results.data.length > 0 && <div className={page.grid}>
            {results.data.map(movie => <MovieCard key={movie.id} item={toMovie(movie)} fluid />)}
          </div>}
          {results && results.totalPages > 1 && <Pagination page={current} totalPages={results.totalPages} onChange={target => apply(applied, target)} />}
        </section>
      </div>
    </main></Layout>
  </>;
}
