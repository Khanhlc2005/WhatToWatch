import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import { PageResult } from '../lib/movies';

// Loads one page of a signed-in list (`?page=` in the URL), reloads on the given window events and
// sends a 401 to /login?next=.
export default function usePagedList<T>(endpoint: string | null, reloadEvents: string[] = []) {
  const router = useRouter();
  const routerRef = useRef(router);
  routerRef.current = router;
  const { isReady } = router;
  const queryPage = Number(router.query.page || 1);
  const page = Number.isSafeInteger(queryPage) && queryPage > 0 ? queryPage : 1;
  const returnPath = router.asPath;
  const [result, setResult] = useState<PageResult<T> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  const reload = useCallback(() => setRevision(value => value + 1), []);
  const eventKey = reloadEvents.join(',');

  useEffect(() => {
    const names = eventKey ? eventKey.split(',') : [];
    names.forEach(name => window.addEventListener(name, reload));
    return () => names.forEach(name => window.removeEventListener(name, reload));
  }, [eventKey, reload]);

  // A different list starts from a clean slate instead of showing the previous one.
  useEffect(() => { setResult(null); }, [endpoint]);

  useEffect(() => {
    if (!isReady) return;
    if (!endpoint) { setLoading(false); return; }
    let active = true;
    setLoading(true);
    setError('');
    fetch(`${endpoint}?page=${page}`)
      .then(async response => {
        if (response.status === 401) { void routerRef.current.replace('/login?next=' + encodeURIComponent(returnPath)); return null; }
        const body = await response.json();
        if (!response.ok) throw new Error(body.message || 'Could not load this list.');
        return body as PageResult<T>;
      })
      .then(body => {
        if (!active || !body) return;
        // The last item of a later page was removed: step back one page.
        const { pathname, query } = routerRef.current;
        if (body.data.length === 0 && page > 1) void routerRef.current.replace({ pathname, query: { ...query, page: page - 1 } });
        else setResult(body);
      })
      .catch(reason => { if (active) setError(reason instanceof Error ? reason.message : 'Could not load this list.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [isReady, returnPath, endpoint, page, revision]);

  return { page, result, loading, error, setError, reload };
}
