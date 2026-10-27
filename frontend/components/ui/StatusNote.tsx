import React from 'react';
import styles from '../../styles/ui/StatusNote.module.scss';
import Icon, { IconName } from './Icon';

export interface StatusNoteProps {
  tone?: 'loading' | 'info' | 'invite' | 'error' | 'success' | 'empty';
  title?: string;
  action?: React.ReactNode;
  block?: boolean;
  children?: React.ReactNode;
}

const icons: Record<Exclude<StatusNoteProps['tone'], 'loading' | undefined>, IconName> = {
  info: 'info', error: 'alert', empty: 'film', success: 'check', invite: 'sparkle'
};

// State is always carried by words or an icon, never by colour alone.
export default function StatusNote({ tone = 'info', title, action, block, children }: StatusNoteProps): React.ReactElement {
  return <div className={`${styles.note} ${styles[tone]} ${block ? styles.block : ''}`} role={tone === 'error' ? 'alert' : 'status'}>
    {tone === 'loading' ? <span className={styles.spinner} aria-hidden='true' /> : <Icon name={icons[tone]} />}
    <div className={styles.body}>
      {title && <strong>{title}</strong>}
      <span>{children}</span>
    </div>
    {action && <div className={styles.action}>{action}</div>}
  </div>;
}
