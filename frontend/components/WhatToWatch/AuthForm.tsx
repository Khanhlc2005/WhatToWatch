import Head from 'next/head';
import Link from 'next/link';
import { FormEvent, useState } from 'react';
import { useRouter } from 'next/router';
import Brand from '../Brand';
import { invalidateLibrarySession } from '../LibraryActions';
import Button from '../ui/Button';
import Icon, { IconName } from '../ui/Icon';
import Perforation from '../ui/Perforation';
import StatusNote from '../ui/StatusNote';
import TextField from '../ui/TextField';
import styles from '../../styles/Login.module.scss';

type Props = { mode: 'login' | 'register' };

const perks: { icon: IconName; text: string }[] = [
  { icon: 'heart', text: 'Keep favourites and a watch-later queue' },
  { icon: 'star', text: 'Rate 3 movies to unlock picks made for you' },
  { icon: 'message', text: 'Ask Chatbot W2W what to watch tonight' }
];

export default function AuthForm({ mode }: Props) {
  const router = useRouter();
  const isRegister = mode === 'register';
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [mismatch, setMismatch] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setMismatch(false);
    if (isRegister && password !== confirm) {
      setMismatch(true);
      return;
    }
    setBusy(true);
    try {
      const response = await fetch('/api/auth/' + mode, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password })
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.message || 'Could not complete your request.');
      if (!isRegister) { invalidateLibrarySession(); window.dispatchEvent(new Event('wtw-auth-change')); }
      const next = typeof router.query.next === 'string' && router.query.next.startsWith('/') && !router.query.next.startsWith('//')
        ? router.query.next : '/browse';
      await router.push(isRegister ? '/login?registered=1&next=' + encodeURIComponent(next) : next);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Something went wrong.');
    } finally {
      setBusy(false);
    }
  }

  return <div className={styles.authPage}>
    <Head><title>{isRegister ? 'Sign up' : 'Sign in'} | WhatToWatch</title></Head>
    <header className={styles.authHeader}><Brand href='/' /></header>
    <main className={styles.authMain}>
      <div className={styles.authIntro}>
        <span className={styles.eyebrow}>WELCOME TO WHAT TO WATCH</span>
        <h1>A new story<br /><em>every night.</em></h1>
        <p>Save movies you want to watch and discover more stories worth seeing.</p>
        <ul className={styles.perks}>
          {perks.map(perk => <li key={perk.icon}><Icon name={perk.icon} />{perk.text}</li>)}
        </ul>
      </div>
      <form onSubmit={submit} className={styles.authCard}>
        <div className={styles.stub}>
          <span className={styles.admit}>{isRegister ? 'ADMIT ONE · NEW MEMBER' : 'ADMIT ONE · MEMBER'}</span>
          <h2>{isRegister ? 'Create an account' : 'Sign in'}</h2>
          <p>{isRegister ? 'Start discovering movies you will love.' : 'Welcome back.'}</p>
        </div>
        <Perforation inset />
        <div className={styles.authBody}>
          {!isRegister && router.query.registered === '1' && <StatusNote tone='success'>Account created. Please sign in.</StatusNote>}
          <TextField id='email' label='Email' type='email' required autoComplete='email' value={email}
            onChange={event => setEmail(event.target.value)} placeholder='you@example.com' />
          <TextField id='password' label='Password' type='password' required minLength={8}
            autoComplete={isRegister ? 'new-password' : 'current-password'} value={password}
            onChange={event => setPassword(event.target.value)} placeholder='At least 8 characters' />
          {isRegister && <TextField id='confirm' label='Confirm password' type='password' required minLength={8}
            autoComplete='new-password' value={confirm} onChange={event => setConfirm(event.target.value)}
            error={mismatch ? 'The passwords do not match.' : undefined} />}
          {error && <StatusNote tone='error'>{error}</StatusNote>}
          <Button variant='primary' type='submit' block busy={busy} busyLabel='Please wait…'
            iconRight={busy ? undefined : 'arrow-up-right'}>{isRegister ? 'Create account' : 'Sign in'}</Button>
          <p className={styles.switchLink}>{isRegister ? 'Already have an account?' : 'New here?'}{' '}
            <Link href={(isRegister ? '/login' : '/register') + (typeof router.query.next === 'string' ? '?next=' + encodeURIComponent(router.query.next) : '')}>
              <a>{isRegister ? 'Sign in' : 'Sign up'}</a>
            </Link>
          </p>
        </div>
      </form>
    </main>
    <footer className={styles.strip}>
      <Perforation />
      <div className={styles.stripText}>ADMIT ONE · WHAT TO WATCH</div>
    </footer>
  </div>;
}
