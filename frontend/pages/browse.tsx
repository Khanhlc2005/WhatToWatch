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
          {sections.map((item, index) => {
            return (
              <List
                key={index}
                heading={item.heading}
                endpoint={item.endpoint}
                defaultCard={item?.defaultCard}
                topList={item?.topList}
              />
            );
          })}
        </div>
      </Layout>
    </>
  );
}

const sections: Section[] = [
  {
    heading: 'Popular on Nextflix',
    endpoint: '/api/movies/top-rated'
  },
  {
    heading: 'New & Popular',
    endpoint: '/api/movies/newest',
    defaultCard: false
  },
  {
    heading: 'Top 10 Today',
    endpoint: '/api/movies/top-rated',
    topList: true
  }
];
