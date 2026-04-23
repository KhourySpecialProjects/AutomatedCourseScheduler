import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import type { SelectOption } from './SearchableSelect';

interface Props<T> {
  options: SelectOption<T>[];
  value: T[];
  onChange: (values: T[]) => void;
  placeholder?: string;
  disabled?: boolean;
  filterFn?: (opt: SelectOption<T>, query: string) => boolean;
}

export default function MultiSearchableSelect<T>({
  options,
  value,
  onChange,
  placeholder = 'Select…',
  disabled = false,
  filterFn,
}: Props<T>) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const triggerRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const [dropdownStyle, setDropdownStyle] = useState<React.CSSProperties>({});

  const selectedSet = new Set(value);
  const selectedOptions = options.filter((o) => selectedSet.has(o.value));

  const filtered = options.filter((o) => {
    if (!query.trim()) return true;
    if (filterFn) return filterFn(o, query);
    const q = query.toLowerCase();
    return o.label.toLowerCase().includes(q) || (o.sublabel?.toLowerCase().includes(q) ?? false);
  });

  function openDropdown() {
    if (disabled) return;
    const rect = triggerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const spaceBelow = window.innerHeight - rect.bottom;
    const dropdownH = Math.min(filtered.length * 44 + 52, 280);
    const openUpward = spaceBelow < dropdownH && rect.top > dropdownH;
    setDropdownStyle({
      position: 'fixed',
      left: rect.left,
      width: Math.max(rect.width, 240),
      ...(openUpward
        ? { bottom: window.innerHeight - rect.top + 4 }
        : { top: rect.bottom + 4 }),
      zIndex: 9999,
    });
    setOpen(true);
    setQuery('');
  }

  useEffect(() => {
    if (open) searchRef.current?.focus();
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function onMouseDown(e: MouseEvent) {
      if (!triggerRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', onMouseDown);
    return () => document.removeEventListener('mousedown', onMouseDown);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function update() {
      const rect = triggerRef.current?.getBoundingClientRect();
      if (!rect) return;
      setDropdownStyle((prev) => ({
        ...prev,
        left: rect.left,
        width: Math.max(rect.width, 240),
        ...(!('bottom' in prev) && { top: rect.bottom + 4 }),
      }));
    }
    window.addEventListener('scroll', update, true);
    window.addEventListener('resize', update);
    return () => {
      window.removeEventListener('scroll', update, true);
      window.removeEventListener('resize', update);
    };
  }, [open]);

  function toggle(opt: SelectOption<T>) {
    if (selectedSet.has(opt.value)) {
      onChange(value.filter((v) => v !== opt.value));
    } else {
      onChange([...value, opt.value]);
    }
  }

  function remove(val: T, e: React.MouseEvent) {
    e.stopPropagation();
    onChange(value.filter((v) => v !== val));
  }

  return (
    <div className="relative">
      {/* Trigger / chip area */}
      <div
        ref={triggerRef}
        onClick={() => (open ? setOpen(false) : openDropdown())}
        className={`min-h-[2.375rem] w-full flex flex-wrap items-center gap-1.5 border rounded-lg px-2.5 py-1.5 transition-colors ${
          disabled
            ? 'bg-gray-50 border-gray-200 cursor-not-allowed'
            : 'bg-white border-gray-200 hover:border-gray-300 cursor-pointer'
        } ${open ? 'ring-2 ring-burgundy-500 border-transparent' : ''}`}
      >
        {selectedOptions.length === 0 ? (
          <span className="text-sm text-gray-400 py-0.5">{placeholder}</span>
        ) : (
          selectedOptions.map((opt, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium bg-burgundy-50 text-burgundy-700 border border-burgundy-200"
            >
              {opt.label}
              {!disabled && (
                <button
                  type="button"
                  onClick={(e) => remove(opt.value, e)}
                  className="text-burgundy-400 hover:text-burgundy-700 transition-colors leading-none"
                  aria-label={`Remove ${opt.label}`}
                >
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </span>
          ))
        )}
        <svg
          className={`w-4 h-4 text-gray-400 shrink-0 ml-auto transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      {open && createPortal(
        <div
          style={dropdownStyle}
          className="bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden flex flex-col"
          onMouseDown={(e) => e.stopPropagation()}
        >
          {/* Search */}
          <div className="p-2 border-b border-gray-100">
            <div className="relative">
              <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                ref={searchRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search…"
                className="w-full pl-8 pr-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-burgundy-500"
              />
            </div>
          </div>

          {/* Options */}
          <div className="overflow-y-auto max-h-52">
            {filtered.length === 0 ? (
              <p className="px-3 py-3 text-sm text-gray-400 text-center">No results</p>
            ) : (
              filtered.map((opt, i) => {
                const checked = selectedSet.has(opt.value);
                return (
                  <button
                    key={i}
                    type="button"
                    onClick={() => toggle(opt)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 text-left hover:bg-burgundy-50 transition-colors ${
                      checked ? 'bg-burgundy-50/60' : ''
                    }`}
                  >
                    <span className={`flex items-center justify-center w-4 h-4 rounded border shrink-0 transition-colors ${
                      checked
                        ? 'bg-burgundy-600 border-burgundy-600'
                        : 'border-gray-300'
                    }`}>
                      {checked && (
                        <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </span>
                    <span className="min-w-0">
                      <span className={`block text-sm truncate ${checked ? 'font-medium text-burgundy-700' : 'text-gray-900'}`}>
                        {opt.label}
                      </span>
                      {opt.sublabel && (
                        <span className="block text-xs text-gray-400 truncate">{opt.sublabel}</span>
                      )}
                    </span>
                  </button>
                );
              })
            )}
          </div>

          {/* Footer with count */}
          {selectedOptions.length > 0 && (
            <div className="px-3 py-2 border-t border-gray-100 bg-gray-50 flex items-center justify-between">
              <span className="text-xs text-gray-500">{selectedOptions.length} selected</span>
              <button
                type="button"
                onClick={() => onChange([])}
                className="text-xs text-gray-400 hover:text-gray-700 transition-colors"
              >
                Clear all
              </button>
            </div>
          )}
        </div>,
        document.body,
      )}
    </div>
  );
}
