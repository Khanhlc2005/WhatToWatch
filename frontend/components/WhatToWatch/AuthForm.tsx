import Head from 'next/head';
import Link from 'next/link';
import { FormEvent, useState } from 'react';
import { useRouter } from 'next/router';
import Brand from '../Brand';
import { invalidateLibrarySession } from '../LibraryActions';
import styles from '../../styles/Login.module.scss';

type Props = { mode: 'login' | 'register' };

export default function AuthForm({ mode }: Props) {
  const router = useRouter();
  const isRegister = mode === 'register';
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    if (isRegister && password !== confirm) {
      setError('The passwords do not match.');
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
      </div>
      <form onSubmit={submit} className={styles.authCard}>
        <h2>{isRegister ? 'Create an account' : 'Sign in'}</h2>
        <p>{isRegister ? 'Start discovering movies you will love.' : 'Welcome back.'}</p>
        {!isRegister && router.query.registered === '1' && <p className={styles.success}>Account created. Please sign in.</p>}
        <label htmlFor='email'>Email</label>
        <input id='email' type='email' required autoComplete='email' value={email} onChange={event => setEmail(event.target.value)} placeholder='you@example.com' />
        <label htmlFor='password'>Password</label>
        <input id='password' type='password' required minLength={8} autoComplete={isRegister ? 'new-password' : 'current-password'} value={password} onChange={event => setPassword(event.target.value)} placeholder='At least 8 characters' />
        {isRegister && <>
          <label htmlFor='confirm'>Confirm password</label>
          <input id='confirm' type='password' required minLength={8} autoComplete='new-password' value={confirm} onChange={event => setConfirm(event.target.value)} />
        </>}
        {error && <p role='alert' className={styles.error}>{error}</p>}
        <button disabled={busy} className={styles.submit} type='submit'>{busy ? 'Please wait…' : isRegister ? 'Create account' : 'Sign in'} <span aria-hidden='true'>↗</span></button>
        <p className={styles.switchLink}>{isRegister ? 'Already have an account?' : 'New here?'}{' '}
          <Link href={(isRegister ? '/login' : '/register') + (typeof router.query.next === 'string' ? '?next=' + encodeURIComponent(router.query.next) : '')}><a>{isRegister ? 'Sign in' : 'Sign up'}</a></Link>
        </p>
      </form>
    </main>
  </div>;
}
