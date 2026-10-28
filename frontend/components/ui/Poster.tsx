/* eslint-disable @next/next/no-img-element */
import { useEffect, useState } from 'react';
import styles from '../../styles/ui/Poster.module.scss';

export const POSTER_FALLBACK = '/assets/poster-placeholder.svg';

export interface PosterProps {
  src?: string | null;
  alt?: string;
  className?: string;
}

// 2:3 poster with radius-sm. A missing or broken image falls back to the flat NO POSTER placeholder.
export default function Poster({ src, alt = '', className }: PosterProps): React.ReactElement {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [src]);
  return <img
    className={`${styles.poster} ${className || ''}`}
    src={!src || failed ? POSTER_FALLBACK : src}
    alt={alt}
    loading='lazy'
    onError={() => setFailed(true)}
  />;
}
