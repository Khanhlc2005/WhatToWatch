import Tabs from '../ui/Tabs';
import useLibraryCounts from '../../hooks/useLibraryCounts';

export default function LibraryTabs({ active }: { active: 'favorites' | 'watchlist' | 'lists' }): React.ReactElement {
  const counts = useLibraryCounts();
  return <Tabs label='Saved lists' active={active} items={[
    { id: 'favorites', label: 'Favourite', href: '/library/favorites', count: counts.favorites },
    { id: 'watchlist', label: 'Watch later', href: '/library/watchlist', count: counts.watchlist },
    { id: 'lists', label: 'My lists', href: '/library/lists', count: counts.lists }
  ]} />;
}
