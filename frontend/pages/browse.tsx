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

export default function Browse(): React.ReactElement {
  const { isModal } = useContext(ModalContext);
  return (
    <>
      {isModal && <Modal />}
      <Layout>
        <Banner />
        <div className={styles.contentContainer}>
          <div className={styles.intro}>
            <span className={styles.eyebrow}>KHÁM PHÁ ĐIỆN ẢNH</span>
            <h1>Một bộ phim hay cho tối nay.</h1>
            <p>Bắt đầu từ những bộ phim được yêu thích và các tựa phim mới nhất.</p>
          </div>
          <nav className={styles.quickLinks} aria-label='Danh mục phim'>
            <a href='#top-rated'>Đánh giá cao</a>
            <a href='#newest'>Mới phát hành</a>
          </nav>
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
    heading: 'Được đánh giá cao',
    endpoint: '/api/movies/top-rated'
  },
  {
    id: 'newest',
    heading: 'Mới phát hành',
    endpoint: '/api/movies/newest'
  }
];
