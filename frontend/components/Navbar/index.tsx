import Menu from './Menu';
import Profile from './Profile';
import styles from '../../styles/Navbar.module.scss';

interface NavbarProps { isScrolled: boolean }

export default function Navbar({ isScrolled }: NavbarProps): React.ReactElement {
  return <header className={`${styles.navBar} ${isScrolled ? styles.navBar__filled : ''}`}>
    <Menu />
    <Profile />
  </header>;
}
