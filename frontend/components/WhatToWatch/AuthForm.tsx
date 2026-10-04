import Head from 'next/head';
import Image from 'next/image';
import Link from 'next/link';
import { FormEvent, useState } from 'react';
import { useRouter } from 'next/router';
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
      setError('Passwords do not match.');
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
      if (!response.ok) throw new Error(body.message || 'Request failed');
      await router.push(isRegister ? '/login?registered=1' : '/browse');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Something went wrong');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={styles.container}>
      <Head><title>{isRegister ? 'Sign up' : 'Sign in'} | Nextflix</title></Head>
      <main className={styles.main}>
        <Image src='/assets/loginBg.jpg' alt='background image' layout='fill' unoptimized
          className={styles.main__bgImage} />
        <form onSubmit={submit} className={styles.main__card + ' ' + styles.authCard}>
          <h1>Nextflix</h1>
          <h2>{isRegister ? 'Sign up' : 'Sign in'}</h2>
          {!isRegister && router.query.registered === '1' &&
            <p className={styles.success}>Account created. Please sign in.</p>}
          <label htmlFor='email'>Email</label>
          <input id='email' type='email' required autoComplete='email' value={email}
            onChange={event => setEmail(event.target.value)} />
          <label htmlFor='password'>Password</label>
          <input id='password' type='password' required minLength={8}
            autoComplete={isRegister ? 'new-password' : 'current-password'} value={password}
            onChange={event => setPassword(event.target.value)} />
          {isRegister && <>
            <label htmlFor='confirm'>Confirm password</label>
            <input id='confirm' type='password' required minLength={8}
              autoComplete='new-password' value={confirm}
              onChange={event => setConfirm(event.target.value)} />
          </>}
          {error && <p role='alert' className={styles.error}>{error}</p>}
          <button disabled={busy} className={styles.submit} type='submit'>
            {busy ? 'Please wait...' : isRegister ? 'Sign up' : 'Sign in'}
          </button>
          <p>{isRegister ? 'Already have an account?' : 'New to Nextflix?'}{' '}
            <Link href={isRegister ? '/login' : '/register'}>
              <a>{isRegister ? 'Sign in' : 'Sign up now'}</a>
            </Link>
          </p>
          <Link href='/'><a className={styles.backLink}>Back</a></Link>
        </form>
      </main>
    </div>
  );
}
