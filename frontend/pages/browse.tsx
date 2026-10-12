/* eslint-disable @next/next/no-img-element */
import dynamic from 'next/dynamic';
import React, { useContext } from 'react';

import { ModalContext } from '../context/ModalContext';
import styles from '../styles/Browse.module.scss';
import { Section } from '../types';

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
        <Banner />
        <div className={styles.contentContainer}>
          <div className={styles.intro}>
            <span className={styles.eyebrow}>DISCOVER MOVIES</span>
            <h1>Find a great movie for tonight.</h1>
            <p>Explore picks for you, top rated movies, and the latest releases.</p>
          </div>
          <nav className={styles.quickLinks} aria-label='Movie sections'>
            <a href='#for-you'>For you</a>
            <a href='#top-rated'>Top rated</a>
            <a href='#newest'>New releases</a>
          </nav>
          <Recommendations />
          {sections.map((item) => {
            return (
              <List
                key={item.endpoint}
                id={item.id}
                heading={item.heading}
                endpoint={item.endpoint}
              />
            );
          })}
        </div>
      </Layout>
    </>
  );
}

const sections: (Section & { id: string })[] = [
  {
    id: 'top-rated',
    heading: 'Top rated',
    endpoint: '/api/movies/top-rated'
  },
  {
    id: 'newest',
    heading: 'New releases',
    endpoint: '/api/movies/newest'
  }
];
