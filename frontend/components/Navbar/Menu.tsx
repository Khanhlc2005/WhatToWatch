import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Brand from '../Brand';
import styles from '../../styles/Navbar.module.scss';

export default function Menu() {
  const router = useRouter();
  const initialPath = router.pathname === '/library/[kind]' && typeof router.query.kind === 'string'
    ? '/library/' + router.query.kind : router.asPath;
  const [currentPath, setCurrentPath] = useState(initialPath);

  useEffect(() => {
    const updateFromLocation = () => setCurrentPath(window.location.pathname + window.location.hash);
    const updateFromRoute = (url: string) => setCurrentPath(url);
    updateFromLocation();
    router.events.on('routeChangeComplete', updateFromRoute);
    router.events.on('hashChangeComplete', updateFromRoute);
    window.addEventListener('hashchange', updateFromLocation);
    return () => {
      router.events.off('routeChangeComplete', updateFromRoute);
      router.events.off('hashChangeComplete', updateFromRoute);
      window.removeEventListener('hashchange', updateFromLocation);
    };
  }, [router.events]);

  const path = currentPath.split('#')[0].split('?')[0];
  const hash = currentPath.includes('#') ? currentPath.slice(currentPath.indexOf('#')) : '';
  const links = [
    { href: '/browse', label: 'Khám phá', active: path === '/browse' && !hash },
    { href: '/browse#top-rated', label: 'Đánh giá cao', active: path === '/browse' && hash === '#top-rated' },
    { href: '/browse#newest', label: 'Mới phát hành', active: path === '/browse' && hash === '#newest' },
    { href: '/search', label: 'Tìm kiếm', active: path === '/search' },
    { href: '/library/favorites', label: 'Yêu thích', active: path === '/library/favorites' },
    { href: '/library/watchlist', label: 'Xem sau', active: path === '/library/watchlist' }
  ];

  return <div className={styles.navigation}>
    <Brand />
    <nav className={styles.links} aria-label='Điều hướng chính'>
      {links.map(link => <Link key={link.href} href={link.href}>
        <a className={link.active ? styles.active : undefined} aria-current={link.active ? 'page' : undefined}
          onClick={() => setCurrentPath(link.href)}>{link.label}</a>
      </Link>)}
    </nav>
  </div>;
}
