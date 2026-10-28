import { useEffect, useState } from 'react';

export type LibraryCounts = { favorites?: number; watchlist?: number; lists?: number };

// Counts for the Library tabs. A failed request just leaves that count out.
export default function useLibraryCounts(): LibraryCounts {
  const [counts, setCounts] = useState<LibraryCounts>({});
  useEffect(() => {
    let active = true;
    const load = () => {
      const total = (url: string) => fetch(url).then(response => (response.ok ? response.json() : null))
        .then(body => (body && typeof body.totalElements === 'number' ? body.totalElements : undefined)).catch(() => undefined);
      void Promise.all([
        total('/api/library/favorites?page=1'),
        total('/api/library/watchlist?page=1'),
        fetch('/api/watchlists').then(response => (response.ok ? response.json() : null))
          .then(body => (Array.isArray(body) ? body.length : undefined)).catch(() => undefined)
      ]).then(([favorites, watchlist, lists]) => { if (active) setCounts({ favorites, watchlist, lists }); });
    };
    load();
    window.addEventListener('wtw-library-change', load);
    return () => { active = false; window.removeEventListener('wtw-library-change', load); };
  }, []);
  return counts;
}
