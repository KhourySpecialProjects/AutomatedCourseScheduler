import { useState } from 'react';
import { Severity, type WarningResponse } from '../api/generated';

interface Props {
  warnings: WarningResponse[];
}

export default function AlgorithmWarningsBanner({ warnings }: Props) {
  const [expanded, setExpanded] = useState(false);

  if (warnings.length === 0) return null;

  const maxSev = warnings.reduce((m, w) => Math.max(m, w.SeverityRank), 0);
  const hasHigh = maxSev === Severity.NUMBER_3;

  const containerClass = hasHigh
    ? 'bg-red-50 border border-red-200 text-red-800'
    : 'bg-amber-50 border border-amber-200 text-amber-800';

  const badgeClass = hasHigh
    ? 'text-red-700 bg-red-100 border border-red-200'
    : 'text-amber-700 bg-amber-100 border border-amber-200';

  const severityLabel = (sev: number) =>
    sev === Severity.NUMBER_3 ? 'High' : sev === Severity.NUMBER_2 ? 'Medium' : 'Low';

  const severityBadge = (sev: number) => {
    const cls =
      sev === Severity.NUMBER_3
        ? 'text-red-700 bg-red-50 border border-red-200'
        : sev === Severity.NUMBER_2
          ? 'text-amber-700 bg-amber-50 border border-amber-200'
          : 'text-yellow-700 bg-yellow-50 border border-yellow-200';
    return (
      <span className={`shrink-0 px-1.5 py-0.5 rounded-full text-xs font-medium ${cls}`}>
        {severityLabel(sev)}
      </span>
    );
  };

  return (
    <div className={`rounded-lg px-4 py-3 mb-4 ${containerClass}`}>
      <button
        className="w-full flex items-center justify-between gap-2 text-sm font-medium"
        onClick={() => setExpanded((e) => !e)}
      >
        <span className="flex items-center gap-2">
          <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
          </svg>
          Algorithm warnings ({warnings.length})
        </span>
        <span className="flex items-center gap-2">
          <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium border ${badgeClass}`}>
            {severityLabel(maxSev)} severity
          </span>
          <svg
            className={`w-4 h-4 shrink-0 transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </span>
      </button>

      {expanded && (
        <ul className="mt-3 space-y-2 border-t border-current/10 pt-3">
          {warnings.map((w) => (
            <li key={w.warning_id} className="flex items-start justify-between gap-2 text-xs">
              <span>{w.Message}</span>
              {severityBadge(w.SeverityRank)}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
