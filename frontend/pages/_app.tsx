/* eslint-disable @next/next/no-img-element */
import Head from 'next/head';
import '../styles/globals.scss';
import type { AppProps } from 'next/app';
import { ModalProvider } from '../context/ModalContext';
import Browse from './browse';

function App({ Component, pageProps, router }: AppProps) {
  const isMovieRoute = router.pathname === '/movies/[id]';
  const showBrowse = router.pathname === '/browse' || isMovieRoute;

  return (
    <>
      <Head>
        <title>WhatToWatch — Chọn phim cho tối nay</title>
        <meta name='description' content='Khám phá phim hay và tìm câu chuyện phù hợp với bạn trên WhatToWatch.' />
        <link rel='icon' href='/favicon.svg' type='image/svg+xml' />
      </Head>
      <ModalProvider>
        {showBrowse ? <Browse /> : <Component {...pageProps} />}
        {isMovieRoute && <Component {...pageProps} />}
      </ModalProvider>
    </>
  );
}
export default App;
