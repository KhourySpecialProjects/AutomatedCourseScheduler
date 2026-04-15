import { useCallback, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import type { SectionRichResponse } from '../api/generated';

function formatSectionLabel(s: SectionRichResponse): string {
  return `${s.course.name} §${s.section_number}`;
}

/** "{A} §n is crosslisted with {B} §m" */
function crosslistedTooltip(section: SectionRichResponse, allSections: SectionRichResponse[]): string | null {
  const sid = section.crosslisted_section_id ?? null;
  if (sid != null) {
    const partner = allSections.find((s) => s.section_id === sid);
    if (!partner) return null;
    return `${formatSectionLabel(section)} is crosslisted with ${formatSectionLabel(partner)}`;
  }
  const pointer = allSections.find((s) => s.crosslisted_section_id === section.section_id);
  if (pointer) {
    return `${formatSectionLabel(section)} is crosslisted with ${formatSectionLabel(pointer)}`;
  }
  return null;
}

const TOOLTIP_MAX_W = 280;
const HIDE_MS = 180;


export default function CrosslistSectionHint({
  section,
  allSections,
}: {
  section: SectionRichResponse;
  allSections: SectionRichResponse[];
}) {
  const tip = crosslistedTooltip(section, allSections);
  const triggerRef = useRef<HTMLSpanElement>(null);
  const [open, setOpen] = useState(false);
  const [anchor, setAnchor] = useState<{ top: number; left: number } | null>(null);
  const hideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearHideTimer = useCallback(() => {
    if (hideTimerRef.current != null) {
      clearTimeout(hideTimerRef.current);
      hideTimerRef.current = null;
    }
  }, []);

  const show = useCallback(() => {
    clearHideTimer();
    const el = triggerRef.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    setAnchor({ top: r.bottom, left: r.left + r.width / 2 });
    setOpen(true);
  }, [clearHideTimer]);

  const scheduleHide = useCallback(() => {
    clearHideTimer();
    hideTimerRef.current = setTimeout(() => {
      setOpen(false);
      setAnchor(null);
      hideTimerRef.current = null;
    }, HIDE_MS);
  }, [clearHideTimer]);

  useEffect(() => () => clearHideTimer(), [clearHideTimer]);

  if (!tip) return null;

  const vw = typeof window !== 'undefined' ? window.innerWidth : 800;
  const w = Math.min(TOOLTIP_MAX_W, vw - 16);
  const left = anchor
    ? Math.max(8, Math.min(anchor.left - w / 2, vw - w - 8))
    : 0;
  const top = anchor ? anchor.top + 6 : 0;

  const portal =
    open &&
    anchor &&
    typeof document !== 'undefined' &&
    createPortal(
      <div
        role="tooltip"
        className="pointer-events-none fixed z-[10000] rounded-md bg-gray-900 px-3 py-2 text-left text-xs font-normal leading-snug text-white shadow-xl"
        style={{
          top,
          left,
          width: w,
          maxWidth: w,
        }}
      >
        <span className="block whitespace-normal break-words">{tip}</span>
      </div>,
      document.body,
    );

  return (
    <>
      <span
        ref={triggerRef}
        className="relative inline-flex shrink-0 cursor-default items-center justify-center align-middle p-1.5 -m-1.5 text-indigo-600 hover:text-indigo-800 pointer-events-auto z-10"
        aria-label={tip}
        onMouseEnter={show}
        onMouseLeave={scheduleHide}
      >
        <svg
          className="h-3.5 w-3.5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden
        >
          <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19A4 4 0 0117 6.84L7.71 16.12a2 2 0 002.83 2.83L19.07 9.9" />
        </svg>
      </span>
      {portal}
    </>
  );
}
