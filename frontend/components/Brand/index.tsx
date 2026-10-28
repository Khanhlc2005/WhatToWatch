import Link from 'next/link';
import styles from '../../styles/Brand.module.scss';

interface BrandProps {
  href?: string;
  size?: 'md' | 'lg';
  markOnly?: boolean;
}

export default function Brand({ href = '/browse', size = 'md', markOnly = false }: BrandProps) {
  const markSize = size === 'lg' ? 44 : 28;
  return <Link href={href}>
    <a className={`${styles.brand} ${size === 'lg' ? styles.large : ''}`} aria-label='WhatToWatch — Browse movies'>
      <svg className={styles.mark} width={markSize} height={markSize} viewBox='0 0 64 64' aria-hidden='true'>
        <path fillRule='evenodd' d='M8 12h48a4 4 0 0 1 4 4v9a7 7 0 0 0 0 14v9a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4v-9a7 7 0 0 0 0-14v-9a4 4 0 0 1 4-4zM26 22.5v19l16-9.5z' />
      </svg>
      {!markOnly && <span className={styles.wordmark}>WhatToWatch</span>}
    </a>
  </Link>;
}
