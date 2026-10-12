import Brand from '../Brand';
import styles from '../../styles/Footer.module.scss';

export default function Footer() {
  return <footer className={styles.footer}>
    <Brand />
    <p>Discover your next great story.</p>
    <span>© {new Date().getFullYear()} WhatToWatch</span>
  </footer>;
}
