import styles from '../../styles/ui/Pagination.module.scss';
import Button from './Button';

export interface PaginationProps {
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
}

// `page` is 1-based.
export default function Pagination({ page, totalPages, onChange }: PaginationProps): React.ReactElement {
  return <nav className={styles.pager} aria-label='Pagination'>
    <Button size='sm' icon='chevron-left' disabled={page <= 1} onClick={() => onChange(page - 1)}>Previous</Button>
    <span className={styles.status}>PAGE {page} / {totalPages}</span>
    <Button size='sm' iconRight='chevron-right' disabled={page >= totalPages} onClick={() => onChange(page + 1)}>Next</Button>
  </nav>;
}
