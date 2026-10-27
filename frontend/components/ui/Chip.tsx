import React from 'react';
import styles from '../../styles/ui/Chip.module.scss';
import Icon from './Icon';

export interface ChipProps {
  selected?: boolean;
  onClick?: () => void;
  children?: React.ReactNode;
}

// Static genre chip, or a toggle (`selected` set) that exposes aria-pressed.
export default function Chip({ selected, onClick, children }: ChipProps): React.ReactElement {
  const selectable = selected !== undefined;
  if (!selectable && !onClick) return <span className={styles.chip}>{children}</span>;
  return <button type='button' className={`${styles.chip} ${styles.action} ${selected ? styles.on : ''}`}
    aria-pressed={selectable ? selected : undefined} onClick={onClick}>
    {selected && <Icon name='check' size={14} />}
    {children}
  </button>;
}
