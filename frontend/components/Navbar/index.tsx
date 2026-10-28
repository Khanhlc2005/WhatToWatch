import Link from 'next/link';
import Menu from './Menu';
import Profile from './Profile';
import Icon from '../ui/Icon';
import styles from '../../styles/Navbar.module.scss';

interface NavbarProps { isScrolled: boolean }

export default function Navbar({ isScrolled }: NavbarProps): React.ReactElement {
  return <header className={`${styles.navBar} ${isScrolled ? styles.filled : ''}`}>
    <div className={styles.inner}>
      <Menu />
      <div className={styles.end}>
        <Link href='/search'>
          <a className={styles.searchLink} aria-label='Search movies'><Icon name='search' size={20} /></a>
        </Link>
        <Profile />
      </div>
    </div>
  </header>;
}
