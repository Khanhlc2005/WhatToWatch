import React from 'react';
import styles from '../../styles/ui/TicketMeta.module.scss';

export interface TicketMetaProps {
  rating?: number | null;
  year?: number | string;
  runtime?: number | null;
  extra?: string[];
  highlight?: boolean;
  className?: string;
}

// Metadata as a ticket prints it: "IMDb 8.7 · 1994 · 142 MIN".
export default function TicketMeta({ rating, year, runtime, extra = [], highlight, className }: TicketMetaProps): React.ReactElement {
  const parts: string[] = [];
  if (rating !== undefined) parts.push(rating === null ? 'NOT RATED' : 'IMDb ' + Number(rating).toFixed(1));
  if (year) parts.push(String(year));
  if (runtime) parts.push(runtime + ' MIN');
  parts.push(...extra);
  return <span className={`${styles.meta} ${className || ''}`}>
    {parts.map((part, index) => <React.Fragment key={index}>
      {index > 0 && <span className={styles.dot} aria-hidden='true'>·</span>}
      <span className={index === 0 && rating != null && highlight ? styles.highlight : undefined}>{part}</span>
    </React.Fragment>)}
  </span>;
}
