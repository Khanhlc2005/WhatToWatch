import Head from 'next/head';
import Link from 'next/link';
import Brand from '../components/Brand';
import styles from '../styles/Login.module.scss';

export default function Home(): React.ReactElement {
  return <div className={styles.landing}>
    <Head><title>WhatToWatch — Chọn phim cho tối nay</title></Head>
    <header className={styles.landingHeader}>
      <Brand href='/' />
      <Link href='/login'><a className={styles.headerLink}>Đăng nhập <span aria-hidden='true'>↗</span></a></Link>
    </header>
    <main className={styles.landingMain}>
      <span className={styles.eyebrow}>KHÁM PHÁ ĐIỆN ẢNH THEO CÁCH CỦA BẠN</span>
      <h1>Chọn phim hay.<br /><em>Thưởng thức tối nay.</em></h1>
      <p>Những câu chuyện đáng xem đang chờ bạn. Bắt đầu với các bộ phim được đánh giá cao và mới phát hành.</p>
      <div className={styles.landingActions}>
        <Link href='/login'><a className={styles.primaryLink}>Bắt đầu khám phá <span aria-hidden='true'>↗</span></a></Link>
        <Link href='/register'><a className={styles.secondaryLink}>Tạo tài khoản</a></Link>
      </div>
    </main>
    <div className={styles.landingFooter}>WHAT TO WATCH <span>•</span> YOUR NEXT GREAT STORY</div>
  </div>;
}
