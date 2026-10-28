import { useRouter } from 'next/router';
import { useState } from 'react';
import ActivityPage from '../../components/me/ActivityPage';
import WatchHistory from '../../components/me/WatchHistory';
import Pagination from '../../components/ui/Pagination';
import StatusNote from '../../components/ui/StatusNote';
import usePagedList from '../../hooks/usePagedList';
import { HistoryItem } from '../../lib/activity';

export default function WatchHistoryPage() {
  const router = useRouter();
  const { page: current, result, loading, error, setError, reload } = usePagedList<HistoryItem>('/api/watch-history');
  const [busy, setBusy] = useState(false);

  async function send(path: string, failure: string) {
    if (busy) return;
    setBusy(true);
    setError('');
    try {
      const response = await fetch(path, { method: 'DELETE' });
      if (response.status === 401) { void router.replace('/login?next=%2Fme%2Fhistory'); return; }
      if (!response.ok) throw new Error((await response.json().catch(() => ({}))).message || failure);
      reload();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : failure);
    } finally {
      setBusy(false);
    }
  }

  return <ActivityPage active='history' title='Watch history' count={result?.totalElements}
    lead='Movies you opened and watched, newest first.'>
    {loading && !result && <StatusNote tone='loading'>Loading your watch history…</StatusNote>}
    {error && <StatusNote tone='error'>{error}</StatusNote>}
    {result && <>
      <WatchHistory items={result.data} total={result.totalElements} busy={busy}
        onRemove={item => void send('/api/watch-history/' + item.id, 'Could not remove this entry.')}
        onClear={() => void send('/api/watch-history', 'Could not clear your watch history.')} />
      {result.totalPages > 1 && <Pagination page={current} totalPages={result.totalPages}
        onChange={target => void router.push('/me/history?page=' + target)} />}
    </>}
  </ActivityPage>;
}
