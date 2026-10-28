import Head from 'next/head';
import { useEffect, useState } from 'react';
import axios from 'axios';
import Brand from '../components/Brand';
import Button from '../components/ui/Button';
import Perforation from '../components/ui/Perforation';
import Poster from '../components/ui/Poster';
import { Movie } from '../types';
import { MovieSummary, toMovie } from '../lib/movies';
import styles from '../styles/Landing.module.scss';

export default function Home(): React.ReactElement {
  const [posters, setPosters] = useState<Movie[]>([]);

  // Decorative collage of real top rated posters; the page works without it.
  useEffect(() => {
    let active = true;
    axios.get<MovieSummary[]>('/api/movies/top-rated')
      .then(result => { if (active) setPosters(result.data.filter(movie => movie.posterUrl).slice(0, 6).map(toMovie)); })
      .catch(() => undefined);
    return () => { active = false; };
  }, []);

  return <div className={styles.landing}>
    <Head><title>WhatToWatch — Find your next movie</title></Head>
    <header className={styles.header}>
      <Brand href='/' />
      <Button size='sm' href='/login' iconRight='arrow-up-right'>Sign in</Button>
    </header>
    <main className={`${styles.main} ${posters.length ? styles.withPosters : ''}`}>
      <div className={styles.copy}>
        <span className={styles.eyebrow}>DISCOVER MOVIES YOUR WAY</span>
        <h1>Find a great movie.<br /><em>Enjoy it tonight.</em></h1>
        <p>Your next great story is waiting. Start with top rated and newly released movies.</p>
        <div className={styles.actions}>
          <Button variant='primary' href='/login' iconRight='arrow-up-right'>Start exploring</Button>
          <Button href='/register'>Create an account</Button>
        </div>
      </div>
      {posters.length > 0 && <div className={styles.collage} aria-hidden='true'>
        {[2, 0, 5, 3, 1, 4].map(index => posters[index] && <div key={posters[index].id} className={styles.tile}>
          <Poster src={posters[index].poster} />
        </div>)}
      </div>}
    </main>
    <footer className={styles.strip}>
      <Perforation />
      <div className={styles.stripText}>WHAT TO WATCH · YOUR NEXT GREAT STORY</div>
    </footer>
  </div>;
}
