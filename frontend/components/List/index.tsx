import { useEffect, useState } from 'react';
import axios from 'axios';
import { Movie } from '../../types';
import { MovieSummary, toMovie } from '../../lib/movies';
import MovieRow from './MovieRow';
import SectionHeading from '../ui/SectionHeading';
import SkeletonRow from '../ui/SkeletonRow';
import StatusNote from '../ui/StatusNote';
import styles from '../../styles/Cards.module.scss';

interface ListProps {
  id?: string;
  heading: string;
  endpoint: string;
  // Show Top 10 rank numerals and cap the row at ten movies.
  ranked?: boolean;
}

export default function List({ id, heading, endpoint, ranked = false }: ListProps) {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(false);
    setMovies([]);
    axios.get<MovieSummary[]>(endpoint)
      .then(result => { if (active) setMovies((ranked ? result.data.slice(0, 10) : result.data).map(toMovie)); })
      .catch(() => { if (active) setError(true); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [endpoint, ranked]);

  return <section id={id} className={styles.section} aria-busy={loading}>
    <SectionHeading title={heading} count={!loading && !error ? `${movies.length} MOVIES` : 'EXPLORE'} />
    {loading && <SkeletonRow />}
    {error && <StatusNote tone='error'>Could not load movies.</StatusNote>}
    {!loading && !error && movies.length === 0 && <StatusNote tone='empty'>No movies yet.</StatusNote>}
    {!loading && !error && movies.length > 0 && <MovieRow movies={movies} ranked={ranked} />}
  </section>;
}
