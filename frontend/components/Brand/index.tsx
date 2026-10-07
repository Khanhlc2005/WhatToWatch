import Link from 'next/link';
import styles from '../../styles/Brand.module.scss';

export default function Brand({ href = '/browse' }: { href?: string }) {
  return <Link href={href}>
    <a className={styles.brand} aria-label='WhatToWatch — Trang duyệt phim'>
      <span className={styles.mark} aria-hidden='true'><span /></span>
      <span className={styles.wordmark}>WHAT<span>TO</span>WATCH<span className={styles.period}>.</span></span>
    </a>
  </Link>;
}
