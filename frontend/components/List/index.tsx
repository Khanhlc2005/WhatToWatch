import { useEffect, useState } from 'react';
import axios from 'axios';
import { Movie } from '../../types';
import { MovieSummary, toMovie } from '../../lib/movies';
import MovieRow from './MovieRow';
import styles from '../../styles/Cards.module.scss';

interface ListProps {
  defaultCard?: boolean;
  heading: string;
  topList?: boolean;
  endpoint: string;
}

export default function List({ defaultCard = true, heading, topList = false, endpoint }: ListProps) {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(false);
    setMovies([]);
    axios.get<MovieSummary[]>(endpoint)
      .then(result => { if (active) setMovies(result.data.map(toMovie)); })
      .catch(() => { if (active) setError(true); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [endpoint]);

  return <section className={styles.listContainer} aria-busy={loading}>
    <strong className={styles.category}>{heading}</strong>
    {loading && <p role='status'>Đang tải phim…</p>}
    {error && <p role='alert' className={styles.listError}>Không tải được danh sách phim.</p>}
    {!loading && !error && movies.length === 0 && <p role='status'>Chưa có phim.</p>}
    <MovieRow movies={movies} defaultCard={defaultCard} topList={topList} />
  </section>;
}
