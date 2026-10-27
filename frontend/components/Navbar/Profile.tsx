import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import styles from '../../styles/Navbar.module.scss';
import { invalidateLibrarySession } from '../LibraryActions';
import Button from '../ui/Button';
import Icon, { IconName } from '../ui/Icon';

type Session = { authenticated: boolean; email?: string | null };

// `ready` is flipped as each page ships (My ratings and Watch history in Phase 4, My lists in Phase 5).
const accountLinks: { href: string; label: string; icon: IconName; ready: boolean }[] = [
  { href: '/me/ratings', label: 'My ratings', icon: 'star', ready: false },
  { href: '/me/history', label: 'Watch history', icon: 'clock', ready: false },
  { href: '/library/lists', label: 'My lists', icon: 'list', ready: false }
];

export default function Profile(): React.ReactElement {
  const [session, setSession] = useState<Session>({ authenticated: false });
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    let active = true;
    const load = () => fetch('/api/auth/session').then(response => response.json())
      .then((data: Session) => active && setSession({ authenticated: Boolean(data.authenticated), email: data.email }))
      .catch(() => active && setSession({ authenticated: false }));
    load();
    window.addEventListener('wtw-auth-change', load);
    return () => { active = false; window.removeEventListener('wtw-auth-change', load); };
  }, []);

  useEffect(() => {
    if (!open) return;
    const onPointer = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape') setOpen(false); };
    document.addEventListener('mousedown', onPointer);
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('mousedown', onPointer); document.removeEventListener('keydown', onKey); };
  }, [open]);

  useEffect(() => {
    const close = () => setOpen(false);
    router.events.on('routeChangeStart', close);
    return () => router.events.off('routeChangeStart', close);
  }, [router.events]);

  const signOut = async () => {
    setOpen(false);
    await fetch('/api/auth/logout', { method: 'POST' });
    invalidateLibrarySession();
    window.dispatchEvent(new Event('wtw-auth-change'));
    setSession({ authenticated: false });
    await router.push('/');
  };

  if (!session.authenticated) {
    return <Button variant='secondary' size='sm' href='/login' iconRight='arrow-up-right'>Sign in</Button>;
  }

  const email = session.email || 'Account';
  return <div className={styles.account} ref={rootRef}>
    <button type='button' className={styles.accountButton} aria-expanded={open} aria-haspopup='menu'
      aria-label={'Account menu for ' + email} onClick={() => setOpen(!open)}>
      <span className={styles.avatar} aria-hidden='true'>{email.charAt(0).toUpperCase()}</span>
      <span className={styles.accountMail}>{email}</span>
      <Icon name='chevron-down' size={16} />
    </button>
    {open && <div className={styles.menu} role='menu'>
      {accountLinks.filter(item => item.ready).map(item => <Link key={item.href} href={item.href}>
        <a role='menuitem'><Icon name={item.icon} />{item.label}</a>
      </Link>)}
      {accountLinks.some(item => item.ready) && <div className={styles.menuRule} />}
      <button type='button' role='menuitem' onClick={signOut}><Icon name='log-out' />Sign out</button>
    </div>}
  </div>;
}
