import styles from '../../styles/ui/SectionHeading.module.scss';

export interface SectionHeadingProps {
  title: string;
  stamp?: string;
  count?: string;
}

// One line: optional stamp, italic title, hairline, mono count.
export default function SectionHeading({ title, stamp, count }: SectionHeadingProps): React.ReactElement {
  return <div className={styles.heading}>
    {stamp && <span className={styles.stamp}>{stamp}</span>}
    <h2>{title}</h2>
    <span className={styles.rule} />
    {count != null && <span className={styles.count}>{count}</span>}
  </div>;
}
