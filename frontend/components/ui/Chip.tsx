import Link from 'next/link';
import React from 'react';
import styles from '../../styles/ui/Chip.module.scss';
import Icon from './Icon';

export interface ChipProps {
  selected?: boolean;
  onClick?: () => void;
  href?: string;
  children?: React.ReactNode;
}

// Static genre chip, a link chip (`href`), or a toggle (`selected` set) that exposes aria-pressed.
export default function Chip({ selected, onClick, href, children }: ChipProps): React.ReactElement {
  const selectable = selected !== undefined;
  if (href) return <Link href={href}><a className={`${styles.chip} ${styles.action}`}>{children}</a></Link>;
  if (!selectable && !onClick) return <span className={styles.chip}>{children}</span>;
  return <button type='button' className={`${styles.chip} ${styles.action} ${selected ? styles.on : ''}`}
    aria-pressed={selectable ? selected : undefined} onClick={onClick}>
    {selected && <Icon name='check' size={14} />}
    {children}
  </button>;
}
