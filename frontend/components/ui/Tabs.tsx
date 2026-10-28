import Link from 'next/link';
import styles from '../../styles/ui/Tabs.module.scss';

export interface TabsProps {
  items: { id: string; label: string; href: string; count?: number }[];
  active: string;
  label: string;
}

export default function Tabs({ items, active, label }: TabsProps): React.ReactElement {
  return <nav className={styles.tabs} aria-label={label}>
    {items.map(tab => <Link key={tab.id} href={tab.href}>
      <a className={tab.id === active ? styles.on : undefined} aria-current={tab.id === active ? 'page' : undefined}>
        {tab.label}
        {tab.count != null && <span className={styles.count}>{tab.count}</span>}
      </a>
    </Link>)}
  </nav>;
}
