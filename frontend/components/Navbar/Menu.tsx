import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Brand from '../Brand';
import { DISCOVER_ENABLED } from '../../config/features';
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
  const links = [
    { href: '/browse', label: 'Home', active: path === '/browse' },
    { href: '/search', label: 'Search', active: path === '/search' },
    ...(DISCOVER_ENABLED ? [{ href: '/discover', label: 'Discover', active: path === '/discover' }] : []),
    { href: '/chat', label: 'Chatbot W2W', active: path === '/chat' },
    { href: '/library/favorites', label: 'Library', active: path.startsWith('/library') }
  ];

  return <div className={styles.navigation}>
    <Brand />
    <nav className={styles.links} aria-label='Main navigation'>
      {links.map(link => <Link key={link.href} href={link.href}>
        <a className={link.active ? styles.active : undefined} aria-current={link.active ? 'page' : undefined}
          onClick={() => setCurrentPath(link.href)}>{link.label}</a>
      </Link>)}
    </nav>
  </div>;
}
