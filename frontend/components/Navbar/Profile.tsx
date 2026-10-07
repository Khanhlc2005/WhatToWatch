import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import styles from '../../styles/Navbar.module.scss';
import { invalidateLibrarySession } from '../LibraryActions';

export default function Profile(): React.ReactElement {
  const [authenticated, setAuthenticated] = useState(false);
  const router = useRouter();

  useEffect(() => {
    fetch('/api/auth/session').then(response => response.json())
      .then(data => setAuthenticated(Boolean(data.authenticated)))
      .catch(() => setAuthenticated(false));
  }, []);

  const onAccountClick = async () => {
    if (authenticated) {
      await fetch('/api/auth/logout', { method: 'POST' });
      invalidateLibrarySession();
      window.dispatchEvent(new Event('wtw-auth-change'));
      setAuthenticated(false);
      await router.push('/');
    } else {
      await router.push('/login');
    }
  };

  return <button className={styles.accountButton} onClick={onAccountClick}>
    <span className={styles.accountDot} aria-hidden='true' />
    {authenticated ? 'Đăng xuất' : 'Đăng nhập'}
  </button>;
}
