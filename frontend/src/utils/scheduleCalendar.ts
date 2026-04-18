/** Shared helpers for calendar / row views (extracted to satisfy react-refresh). */

export function parseTimeToMinutes(raw: string): number {
  const s = raw.trim();
  const m = s.match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM|am|pm)?$/);
  if (!m) return Number.POSITIVE_INFINITY;
  let h = Number(m[1]);
  const mins = Number(m[2]);
  const ampm = m[4]?.toLowerCase();
  if (ampm) {
    if (h === 12) h = 0;
    if (ampm === 'pm') h += 12;
  }
  return h * 60 + mins;
}

export function expandDays(days: string): string[] {
  const result: string[] = [];
  for (const ch of days) {
    if ('MTWRF'.includes(ch)) result.push(ch);
  }
  return result;
}
