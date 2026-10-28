import styles from '../../styles/ui/Perforation.module.scss';

// The torn-ticket divider. At most one per block.
export default function Perforation({ inset = false }: { inset?: boolean }): React.ReactElement {
  return <div className={`${styles.perforation} ${inset ? styles.inset : ''}`} role='separator' aria-hidden='true'>
    <span className={`${styles.notch} ${styles.left}`} />
    <span className={styles.line} />
    <span className={`${styles.notch} ${styles.right}`} />
  </div>;
}
