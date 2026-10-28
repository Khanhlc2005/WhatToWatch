import Head from 'next/head';
import { useCallback, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../../components/Layout';
import Modal from '../../components/Modal';
import MovieCard from '../../components/List/MovieCard';
import LibraryTabs from '../../components/library/LibraryTabs';
import WatchlistManager from '../../components/library/WatchlistManager';
import Button from '../../components/ui/Button';
import Pagination from '../../components/ui/Pagination';
import StatusNote from '../../components/ui/StatusNote';
import { ADD_TO_LIST_ENABLED } from '../../config/features';
import { ModalContext } from '../../context/ModalContext';
import usePagedList from '../../hooks/usePagedList';
import useLibraryCounts from '../../hooks/useLibraryCounts';
import { MovieSummary, toMovie } from '../../lib/movies';
import { WatchlistSummary } from '../../lib/watchlists';
import page from '../../styles/Page.module.scss';

async function send(url: string, method: string, body?: unknown): Promise<{ ok: boolean; status: number; body: any }> {
  const response = await fetch(url, {
    method, ...(body === undefined ? {} : { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  });
  return { ok: response.ok, status: response.status, body: await response.json().catch(() => ({})) };
}

export default function MyLists() {
  const router = useRouter();
  const { isModal } = useContext(ModalContext);
  const counts = useLibraryCounts();
  const [lists, setLists] = useState<WatchlistSummary[] | null>(null);
  const [loadError, setLoadError] = useState('');
  const [busy, setBusy] = useState(false);
  const queryId = Number(router.query.list);
  const selected = lists ? lists.find(list => list.id === queryId) || lists[0] || null : null;
  // A `?page=` left over from another list must not be applied to the list shown instead.
  const staleUrl = Boolean(selected && selected.id !== queryId && router.query.page);
  const { page: current, result, loading, error } = usePagedList<MovieSummary>(
    selected && !staleUrl ? `/api/watchlists/${selected.id}/movies` : null, ['wtw-library-change']);

  const loadLists = useCallback(async () => {
    const response = await send('/api/watchlists', 'GET');
    if (response.status === 401) { void router.replace('/login?next=%2Flibrary%2Flists'); return null; }
    if (!response.ok) throw new Error(response.body.message || 'Could not load your lists.');
    setLists(response.body as WatchlistSummary[]);
    return response.body as WatchlistSummary[];
  }, [router]);

  useEffect(() => { loadLists().catch(reason => setLoadError(reason instanceof Error ? reason.message : 'Could not load your lists.')); }, [loadLists]);

  // Runs one change and reloads the lists; resolves to an error message or null.
  async function change(request: () => Promise<{ ok: boolean; status: number; body: any }>, after?: (body: any) => void): Promise<string | null> {
    setBusy(true);
    try {
      const response = await request();
      if (response.status === 401) { void router.replace('/login?next=%2Flibrary%2Flists'); return null; }
      if (!response.ok) return response.body.message || 'Could not update your lists.';
      await loadLists();
      after?.(response.body);
      window.dispatchEvent(new Event('wtw-library-change'));
      return null;
    } catch {
      return 'Could not update your lists.';
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (staleUrl && selected) void router.replace({ pathname: '/library/lists', query: { list: selected.id } }, undefined, { scroll: false });
  }, [staleUrl, selected, router]);

  const select = (id: number) => void router.replace({ pathname: '/library/lists', query: { list: id } }, undefined, { scroll: false });

  return <>
    <Head><title>My lists | WhatToWatch</title></Head>
    {isModal && <Modal />}
    <Layout><main className={`${page.page} ${page.tight}`}>
      <div className={page.head}>
        <span className={page.eyebrow}>YOUR COLLECTION</span>
        <h1>My lists</h1>
        <p>Keep favourites, a watch-later queue and as many named lists as you like.</p>
      </div>
      <LibraryTabs active='lists' />
      {loadError && <StatusNote tone='error'>{loadError}</StatusNote>}
      {!lists && !loadError && <StatusNote tone='loading'>Loading your lists…</StatusNote>}
      {!ADD_TO_LIST_ENABLED && lists && <StatusNote tone='info'>
        You can create, rename and delete lists here. Adding movies to a list is not available yet.
      </StatusNote>}
      {lists && <WatchlistManager lists={lists} selected={selected} favorites={counts.favorites} watchLater={counts.watchlist} busy={busy}
        onSelect={select}
        onCreate={name => change(() => send('/api/watchlists', 'POST', { name }), created => created?.id && select(created.id))}
        onRename={name => change(() => send(`/api/watchlists/${selected?.id}`, 'PUT', { name }))}
        onDelete={() => change(() => send(`/api/watchlists/${selected?.id}`, 'DELETE'), () => void router.replace('/library/lists', undefined, { scroll: false }))}>
        {loading && !result && <StatusNote tone='loading'>Loading this list…</StatusNote>}
        {error && <StatusNote tone='error'>{error}</StatusNote>}
        {result && result.data.length === 0 && <StatusNote tone='empty' block title='This list is empty'
          action={<Button size='sm' href='/browse'>Explore movies</Button>}>
          {ADD_TO_LIST_ENABLED ? 'Add movies from the detail view of any movie.' : 'Movies you add will show up here.'}
        </StatusNote>}
        {result && result.data.length > 0 && <div className={page.grid}>
          {result.data.map(movie => <MovieCard key={movie.id} item={toMovie(movie)} fluid />)}
        </div>}
        {result && result.totalPages > 1 && selected && <Pagination page={current} totalPages={result.totalPages}
          onChange={target => void router.push({ pathname: '/library/lists', query: { list: selected.id, page: target } })} />}
      </WatchlistManager>}
    </main></Layout>
  </>;
}
