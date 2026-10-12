import Head from 'next/head';
import Link from 'next/link';
import Brand from '../components/Brand';
import styles from '../styles/Login.module.scss';

export default function Home(): React.ReactElement {
  return <div className={styles.landing}>
    <Head><title>WhatToWatch — Find your next movie</title></Head>
    <header className={styles.landingHeader}>
      <Brand href='/' />
      <Link href='/login'><a className={styles.headerLink}>Sign in <span aria-hidden='true'>↗</span></a></Link>
    </header>
    <main className={styles.landingMain}>
      <span className={styles.eyebrow}>DISCOVER MOVIES YOUR WAY</span>
      <h1>Find a great movie.<br /><em>Enjoy it tonight.</em></h1>
      <p>Your next great story is waiting. Start with top rated and newly released movies.</p>
      <div className={styles.landingActions}>
        <Link href='/login'><a className={styles.primaryLink}>Start exploring <span aria-hidden='true'>↗</span></a></Link>
        <Link href='/register'><a className={styles.secondaryLink}>Create an account</a></Link>
      </div>
    </main>
    <div className={styles.landingFooter}>WHAT TO WATCH <span>•</span> YOUR NEXT GREAT STORY</div>
  </div>;
}
