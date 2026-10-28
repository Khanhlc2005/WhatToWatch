import { useEffect, useState } from 'react';

export type LibraryCounts = { favorites?: number; watchlist?: number; lists?: number };

// Counts for the Library tabs. A failed request just leaves that count out.
export default function useLibraryCounts(): LibraryCounts {
  const [counts, setCounts] = useState<LibraryCounts>({});
  useEffect(() => {
    let active = true;
    let latest = 0;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const load = () => {
      const request = ++latest;
      const total = (url: string) => fetch(url).then(response => (response.ok ? response.json() : null))
        .then(body => (body && typeof body.totalElements === 'number' ? body.totalElements : undefined)).catch(() => undefined);
      void Promise.all([
        total('/api/library/favorites?page=1'),
        total('/api/library/watchlist?page=1'),
        fetch('/api/watchlists').then(response => (response.ok ? response.json() : null))
          .then(body => (Array.isArray(body) ? body.length : undefined)).catch(() => undefined)
      ]).then(([favorites, watchlist, lists]) => { if (active && request === latest) setCounts({ favorites, watchlist, lists }); });
    };
    // Several changes in a row (create a list, then add a movie) trigger one refresh.
    const schedule = () => { clearTimeout(timer); timer = setTimeout(load, 200); };
    load();
    window.addEventListener('wtw-library-change', schedule);
    return () => { active = false; clearTimeout(timer); window.removeEventListener('wtw-library-change', schedule); };
  }, []);
  return counts;
}
