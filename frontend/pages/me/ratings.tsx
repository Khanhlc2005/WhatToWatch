import Link from 'next/link';
import { useRouter } from 'next/router';
import { useState } from 'react';
import ActivityPage from '../../components/me/ActivityPage';
import RatingHistory from '../../components/me/RatingHistory';
import Pagination from '../../components/ui/Pagination';
import StatusNote from '../../components/ui/StatusNote';
import TicketMeta from '../../components/ui/TicketMeta';
import usePagedList from '../../hooks/usePagedList';
import { RatingItem } from '../../lib/activity';
import page from '../../styles/Page.module.scss';

export default function MyRatings() {
  const router = useRouter();
  const { page: current, result, loading, error, setError } = usePagedList<RatingItem>('/api/ratings', ['wtw-rating-change']);
  const [busyId, setBusyId] = useState<number | null>(null);
  const total = result?.totalElements ?? 0;

  async function remove(item: RatingItem) {
    if (busyId !== null) return;
    setBusyId(item.id);
    setError('');
    try {
      const response = await fetch('/api/ratings/' + item.movieId, { method: 'DELETE' });
      if (response.status === 401) { void router.replace('/login?next=%2Fme%2Fratings'); return; }
      if (!response.ok) throw new Error((await response.json().catch(() => ({}))).message || 'Could not remove your rating.');
      window.dispatchEvent(new Event('wtw-rating-change'));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not remove your rating.');
    } finally {
      setBusyId(null);
    }
  }

  // Changing a rating happens in the detail modal, under "Your rating".
  const change = (item: RatingItem) => void router.push(`/movies/${item.movieId}?from=${encodeURIComponent('/me/ratings')}`);

  return <ActivityPage active='ratings' title='My ratings' count={result ? total : undefined}
    lead='Every star you give shapes the movies picked for you.'>
    {loading && !result && <StatusNote tone='loading'>Loading your ratings…</StatusNote>}
    {error && <StatusNote tone='error'>{error}</StatusNote>}
    {result && <>
      {total >= 3
        ? <StatusNote tone='success' action={<Link href='/browse#for-you'><a className={page.link}>See your picks</a></Link>}>
          You have rated {total} movies, so For you is personalized.
        </StatusNote>
        : total > 0 && <StatusNote tone='invite'>Rate {3 - total} more {3 - total === 1 ? 'movie' : 'movies'} to unlock personalized picks.</StatusNote>}
      {total > 0 && <TicketMeta extra={[`${total} RATED MOVIES`, 'NEWEST FIRST']} />}
      <RatingHistory items={result.data} busyId={busyId} onChange={change} onRemove={item => void remove(item)} />
      {result.totalPages > 1 && <Pagination page={current} totalPages={result.totalPages}
        onChange={target => void router.push('/me/ratings?page=' + target)} />}
    </>}
  </ActivityPage>;
}
