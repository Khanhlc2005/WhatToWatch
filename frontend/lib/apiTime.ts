// The backend sends zone-less LocalDateTime values (e.g. "2026-10-28T05:40:18.92") from a UTC server
// (docs/backend-requests.md). Read them as UTC; values that already carry a zone are left alone.
export function parseApiDate(value?: string | null): Date | null {
  if (!value) return null;
  const hasZone = /(Z|[+-]\d{2}:?\d{2})$/.test(value);
  const date = new Date(hasZone ? value : value + 'Z');
  return Number.isNaN(date.getTime()) ? null : date;
}

// Clock time for a message ("21:02").
export function formatClock(iso?: string): string | undefined {
  const date = parseApiDate(iso);
  return date ? date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false }) : undefined;
}

// Relative label for a conversation ("2H AGO", "YESTERDAY", "OCT 19").
export function formatWhen(iso: string, now: Date = new Date()): string | undefined {
  const date = parseApiDate(iso);
  if (!date) return undefined;
  const minutes = Math.max(0, Math.floor((now.getTime() - date.getTime()) / 60000));
  if (minutes < 1) return 'JUST NOW';
  if (minutes < 60) return `${minutes}M AGO`;
  if (minutes < 60 * 24 && date.getDate() === now.getDate()) return `${Math.floor(minutes / 60)}H AGO`;
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (date.toDateString() === yesterday.toDateString()) return 'YESTERDAY';
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }).toUpperCase();
}
