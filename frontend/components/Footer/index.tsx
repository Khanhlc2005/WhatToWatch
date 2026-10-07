import Brand from '../Brand';
import styles from '../../styles/Footer.module.scss';

export default function Footer() {
  return <footer className={styles.footer}>
    <Brand />
    <p>Khám phá câu chuyện đáng xem tiếp theo của bạn.</p>
    <span>© {new Date().getFullYear()} WhatToWatch</span>
  </footer>;
}
