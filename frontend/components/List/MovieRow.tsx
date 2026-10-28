import { useEffect, useRef, useState } from 'react';
import { Movie } from '../../types';
import MovieCard from './MovieCard';
import IconButton from '../ui/IconButton';
import styles from '../../styles/Cards.module.scss';

export interface MovieRowProps {
  movies: Movie[];
  reasons?: string[];
  ranked?: boolean;
}

export default function MovieRow({ movies, reasons, ranked = false }: MovieRowProps) {
  const rowRef = useRef<HTMLDivElement>(null);
  const [canGoLeft, setCanGoLeft] = useState(false);
  const [canGoRight, setCanGoRight] = useState(false);

  function updateArrows() {
    const row = rowRef.current;
    if (!row) return;
    setCanGoLeft(row.scrollLeft > 2);
    setCanGoRight(row.scrollLeft + row.clientWidth < row.scrollWidth - 2);
  }

  useEffect(() => {
    updateArrows();
    window.addEventListener('resize', updateArrows);
    return () => window.removeEventListener('resize', updateArrows);
  }, [movies]);

  function move(direction: -1 | 1) {
    const row = rowRef.current;
    if (!row) return;
    row.scrollBy({ left: direction * Math.max(200, row.clientWidth * .85), behavior: 'smooth' });
  }

  return <div className={styles.rowViewport}>
    {canGoLeft && <IconButton icon='chevron-left' label='Previous movies' variant='float' className={styles.prev} onClick={() => move(-1)} />}
    <div ref={rowRef} className={styles.row} onScroll={updateArrows}>
      {movies.map((movie, index) => <MovieCard key={movie.id} item={movie} reason={reasons?.[index]} rank={ranked ? index + 1 : undefined} />)}
    </div>
    {canGoRight && <IconButton icon='chevron-right' label='Next movies' variant='float' className={styles.next} onClick={() => move(1)} />}
  </div>;
}
