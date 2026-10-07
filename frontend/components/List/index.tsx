import { useEffect, useState } from 'react';
import axios from 'axios';
import { Movie } from '../../types';
import { MovieSummary, toMovie } from '../../lib/movies';
import MovieRow from './MovieRow';
import styles from '../../styles/Cards.module.scss';

interface ListProps {
  id?: string;
  heading: string;
  endpoint: string;
}

export default function List({ id, heading, endpoint }: ListProps) {
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

  return <section id={id} className={styles.listContainer} aria-busy={loading}>
    <div className={styles.sectionHeading}>
      <h2 className={styles.category}>{heading}</h2>
      <span className={styles.sectionLine} />
      <span className={styles.sectionCount}>{!loading && !error ? `${movies.length} phim` : 'KHÁM PHÁ'}</span>
    </div>
    {loading && <div className={styles.skeletonRow} role='status' aria-label='Đang tải phim'>
      {[0, 1, 2, 3, 4].map(index => <span key={index} />)}
    </div>}
    {error && <p role='alert' className={styles.listError}>Không tải được danh sách phim.</p>}
    {!loading && !error && movies.length === 0 && <p role='status'>Chưa có phim.</p>}
    {!loading && !error && <MovieRow movies={movies} />}
  </section>;
}
