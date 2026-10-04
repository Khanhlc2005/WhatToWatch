import { Movie } from '../../types';
import MovieCard from './MovieCard';
import FeatureCard from './FeatureCards';
import styles from '../../styles/Cards.module.scss';

export interface MovieRowProps {
  movies: Movie[];
  defaultCard?: boolean;
  topList?: boolean;
}

export default function MovieRow({ movies, defaultCard = true, topList = false }: MovieRowProps) {
  const visible = topList ? movies.slice(0, 10) : movies;
  return <div className={styles.cardRow}>
    {visible.map((movie, index) => topList
      ? <FeatureCard key={movie.id} index={index + 1} item={movie} />
      : <MovieCard key={movie.id} defaultCard={defaultCard} item={movie} />)}
  </div>;
}
