import Head from 'next/head';
import Image from 'next/image';
import { NextRouter, useRouter } from 'next/router';

import styles from '../styles/Login.module.scss';
import { ROUTES } from '../config/route';

export default function Home(): React.ReactElement {
  const router: NextRouter = useRouter();

  const onSignIn = () => {
    router.push('/login')
  }

  return (
    <div className={styles.container}>
      <Head>
        <title>Nextflix</title>
        <meta name='description' content='Netflix clone, made using Next.js' />
        <link rel='icon' href='/favicon.ico' />
      </Head>

      <main className={styles.main}>
        <Image src='/assets/loginBg.jpg' alt='background image' layout='fill' unoptimized className={styles.main__bgImage} />
        <div className={styles.main__card}>
          <h1>
            Nextflix
          </h1>
          <p>A simple Netflix clone built using Next.js</p>
          <div className={styles.button} onClick={onSignIn}>Sign in</div>
        </div>
      </main>
    </div>
  );
}
