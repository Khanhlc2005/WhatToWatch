import { Movie } from '../../types';
import MovieCard from './MovieCard';
import styles from '../../styles/Cards.module.scss';

export interface MovieRowProps {
  movies: Movie[];
}

export default function MovieRow({ movies }: MovieRowProps) {
  return <div className={styles.cardRow}>
    {movies.map(movie => <MovieCard key={movie.id} item={movie} />)}
  </div>;
}
