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
      setError('Mật khẩu xác nhận không khớp.');
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
      if (!response.ok) throw new Error(body.message || 'Không thể hoàn tất yêu cầu.');
      if (!isRegister) { invalidateLibrarySession(); window.dispatchEvent(new Event('wtw-auth-change')); }
      const next = typeof router.query.next === 'string' && router.query.next.startsWith('/') && !router.query.next.startsWith('//')
        ? router.query.next : '/browse';
      await router.push(isRegister ? '/login?registered=1&next=' + encodeURIComponent(next) : next);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Đã xảy ra lỗi.');
    } finally {
      setBusy(false);
    }
  }

  return <div className={styles.authPage}>
    <Head><title>{isRegister ? 'Đăng ký' : 'Đăng nhập'} | WhatToWatch</title></Head>
    <header className={styles.authHeader}><Brand href='/' /></header>
    <main className={styles.authMain}>
      <div className={styles.authIntro}>
        <span className={styles.eyebrow}>CHÀO MỪNG ĐẾN VỚI WHAT TO WATCH</span>
        <h1>Mỗi tối, một<br /><em>câu chuyện mới.</em></h1>
        <p>Lưu lại những bộ phim bạn muốn xem và khám phá thêm những câu chuyện thú vị.</p>
      </div>
      <form onSubmit={submit} className={styles.authCard}>
        <h2>{isRegister ? 'Tạo tài khoản' : 'Đăng nhập'}</h2>
        <p>{isRegister ? 'Bắt đầu hành trình khám phá phim của bạn.' : 'Rất vui được gặp lại bạn.'}</p>
        {!isRegister && router.query.registered === '1' && <p className={styles.success}>Tạo tài khoản thành công. Hãy đăng nhập.</p>}
        <label htmlFor='email'>Email</label>
        <input id='email' type='email' required autoComplete='email' value={email} onChange={event => setEmail(event.target.value)} placeholder='ban@example.com' />
        <label htmlFor='password'>Mật khẩu</label>
        <input id='password' type='password' required minLength={8} autoComplete={isRegister ? 'new-password' : 'current-password'} value={password} onChange={event => setPassword(event.target.value)} placeholder='Ít nhất 8 ký tự' />
        {isRegister && <>
          <label htmlFor='confirm'>Xác nhận mật khẩu</label>
          <input id='confirm' type='password' required minLength={8} autoComplete='new-password' value={confirm} onChange={event => setConfirm(event.target.value)} />
        </>}
        {error && <p role='alert' className={styles.error}>{error}</p>}
        <button disabled={busy} className={styles.submit} type='submit'>{busy ? 'Đang xử lý…' : isRegister ? 'Tạo tài khoản' : 'Đăng nhập'} <span aria-hidden='true'>↗</span></button>
        <p className={styles.switchLink}>{isRegister ? 'Đã có tài khoản?' : 'Chưa có tài khoản?'}{' '}
          <Link href={(isRegister ? '/login' : '/register') + (typeof router.query.next === 'string' ? '?next=' + encodeURIComponent(router.query.next) : '')}><a>{isRegister ? 'Đăng nhập' : 'Đăng ký ngay'}</a></Link>
        </p>
      </form>
    </main>
  </div>;
}
