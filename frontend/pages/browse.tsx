import dynamic from 'next/dynamic';
import React, { useContext } from 'react';

import { ModalContext } from '../context/ModalContext';
import styles from '../styles/Page.module.scss';
import { Section } from '../types';
import Chip from '../components/ui/Chip';

const List = dynamic(import('../components/List'));
const Modal = dynamic(import('../components/Modal'));
const Layout = dynamic(import('../components/Layout'));
const Banner = dynamic(import('../components/Banner'));
const Recommendations = dynamic(import('../components/Recommendations'));

export default function Browse(): React.ReactElement {
  const { isModal } = useContext(ModalContext);
  return (
    <>
      {isModal && <Modal />}
      <Layout>
        <main className={styles.page}>
          <Banner />
          <div className={styles.headRow}>
            <div className={styles.head}>
              <span className={styles.eyebrow}>DISCOVER MOVIES</span>
              <h2>Find a great movie for tonight.</h2>
              <p>Explore picks for you, top rated movies, latest releases, and curated genres.</p>
            </div>
            <nav className={styles.quick} aria-label='Movie sections'>
              <Chip href='#for-you'>For you</Chip>
              <Chip href='#top-rated'>Top rated</Chip>
              <Chip href='#newest'>New releases</Chip>
              <Chip href='#action'>Action</Chip>
              <Chip href='#comedy'>Comedy</Chip>
              <Chip href='#scifi'>Sci-Fi</Chip>
              <Chip href='#acclaimed'>Acclaimed</Chip>
            </nav>
          </div>
          <Recommendations />
          {sections.map((item) => {
            return (
              <List
                key={item.endpoint}
                id={item.id}
                heading={item.heading}
                endpoint={item.endpoint}
                ranked={item.ranked}
              />
            );
          })}
        </main>
      </Layout>
    </>
  );
}

const sections: (Section & { id: string; ranked?: boolean })[] = [
  {
    id: 'top-rated',
    heading: 'Top rated',
    endpoint: '/api/movies/top-rated',
    ranked: true
  },
  {
    id: 'newest',
    heading: 'New releases',
    endpoint: '/api/movies/newest'
  },
  {
    id: 'action',
    heading: 'Action & Adventure',
    endpoint: '/api/movies/row?genreIds=28,12'
  },
  {
    id: 'comedy',
    heading: 'Comedy & Feel-Good',
    endpoint: '/api/movies/row?genreIds=35'
  },
  {
    id: 'scifi',
    heading: 'Sci-Fi & Fantasy',
    endpoint: '/api/movies/row?genreIds=878,14'
  },
  {
    id: 'acclaimed',
    heading: 'Critically Acclaimed (8.0+ IMDb)',
    endpoint: '/api/movies/row?minRating=8.0'
  }
];
