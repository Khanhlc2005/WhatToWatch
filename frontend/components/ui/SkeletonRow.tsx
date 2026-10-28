import styles from '../../styles/ui/SkeletonRow.module.scss';

export default function SkeletonRow({ count = 5, label = 'Loading movies' }: { count?: number; label?: string }): React.ReactElement {
  return <div className={styles.row} role='status' aria-label={label}>
    {Array.from({ length: count }, (_, index) => <div key={index} className={styles.card}>
      <span className={`${styles.skeleton} ${styles.poster}`} />
      <span className={`${styles.skeleton} ${styles.line}`} />
      <span className={`${styles.skeleton} ${styles.line} ${styles.short}`} />
    </div>)}
  </div>;
}
