import { useEffect, useRef, useState } from 'react';
import { Movie } from '../../types';
import MovieCard from './MovieCard';
import styles from '../../styles/Cards.module.scss';

export interface MovieRowProps {
  movies: Movie[];
  reasons?: string[];
}

export default function MovieRow({ movies, reasons }: MovieRowProps) {
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
    {canGoLeft && <button type='button' className={`${styles.rowArrow} ${styles.rowArrowLeft}`}
      aria-label='Previous movies' onClick={() => move(-1)}>‹</button>}
    <div ref={rowRef} className={styles.cardRow} onScroll={updateArrows}>
      {movies.map((movie, index) => <MovieCard key={movie.id} item={movie} reason={reasons?.[index]} />)}
    </div>
    {canGoRight && <button type='button' className={`${styles.rowArrow} ${styles.rowArrowRight}`}
      aria-label='Next movies' onClick={() => move(1)}>›</button>}
  </div>;
}
