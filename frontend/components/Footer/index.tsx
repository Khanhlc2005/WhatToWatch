import Brand from '../Brand';
import Perforation from '../ui/Perforation';
import styles from '../../styles/Footer.module.scss';

export default function Footer() {
  return <footer className={styles.footer}>
    <Perforation />
    <div className={styles.row}>
      <Brand />
      <p>Discover your next great story.</p>
      <span className={styles.copyright}>© {new Date().getFullYear()} WHATTOWATCH</span>
    </div>
  </footer>;
}
