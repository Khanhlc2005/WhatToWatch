import Head from 'next/head';
import { useContext } from 'react';
import Layout from '../Layout';
import Modal from '../Modal';
import Tabs from '../ui/Tabs';
import { ModalContext } from '../../context/ModalContext';
import page from '../../styles/Page.module.scss';
import styles from '../../styles/Activity.module.scss';

export interface ActivityPageProps {
  active: 'ratings' | 'history';
  title: string;
  lead: string;
  count?: number;
  children: React.ReactNode;
}

// Shared frame for /me/ratings and /me/history: heading, the two tabs, then the ledger.
export default function ActivityPage({ active, title, lead, count, children }: ActivityPageProps): React.ReactElement {
  const { isModal } = useContext(ModalContext);
  return <>
    <Head><title>{title} | WhatToWatch</title></Head>
    {isModal && <Modal />}
    <Layout><main className={`${page.page} ${page.tight} ${styles.narrow}`}>
      <div className={page.head}>
        <span className={page.eyebrow}>YOUR ACTIVITY</span>
        <h1>{title}</h1>
        <p>{lead}</p>
      </div>
      <Tabs label='Your activity' active={active} items={[
        { id: 'ratings', label: 'My ratings', href: '/me/ratings', count: active === 'ratings' ? count : undefined },
        { id: 'history', label: 'Watch history', href: '/me/history', count: active === 'history' ? count : undefined }
      ]} />
      {children}
    </main></Layout>
  </>;
}
