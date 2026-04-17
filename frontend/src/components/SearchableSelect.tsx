import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

export interface SelectOption<T> {
  value: T;
  label: string;
  sublabel?: string;
}

interface Props<T> {
  options: SelectOption<T>[];
  value: T | null;
  onChange: (value: T | null) => void;
  placeholder?: string;
  disabled?: boolean;
  /** Called with the current query; return true to include the option */
  filterFn?: (opt: SelectOption<T>, query: string) => boolean;
}

export default function SearchableSelect<T>({
  options,
  value,
  onChange,
  placeholder = 'Select…',
  disabled = false,
  filterFn,
}: Props<T>) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const triggerRef = useRef<HTMLButtonElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const [dropdownStyle, setDropdownStyle] = useState<React.CSSProperties>({});

  const selected = options.find((o) => o.value === value) ?? null;

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
      width: rect.width,
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

  // Recalculate position on scroll/resize
  useEffect(() => {
    if (!open) return;
    function update() {
      const rect = triggerRef.current?.getBoundingClientRect();
      if (!rect) return;
      setDropdownStyle((prev) => ({
        ...prev,
        left: rect.left,
        width: rect.width,
        top: 'bottom' in prev ? undefined : rect.bottom + 4,
      }));
    }
    window.addEventListener('scroll', update, true);
    window.addEventListener('resize', update);
    return () => {
      window.removeEventListener('scroll', update, true);
      window.removeEventListener('resize', update);
    };
  }, [open]);

  function select(opt: SelectOption<T>) {
    onChange(opt.value);
    setOpen(false);
  }

  return (
    <div className="relative">
      <button
        ref={triggerRef}
        type="button"
        disabled={disabled}
        onClick={() => (open ? setOpen(false) : openDropdown())}
        className={`w-full flex items-center justify-between gap-2 text-sm border rounded-lg px-3 py-2 text-left transition-colors focus:outline-none focus:ring-2 focus:ring-burgundy-500 ${
          disabled
            ? 'bg-gray-50 text-gray-400 border-gray-200 cursor-not-allowed'
            : 'bg-white border-gray-200 text-gray-900 hover:border-gray-300 cursor-pointer'
        }`}
      >
        <span className={selected ? 'text-gray-900' : 'text-gray-400'}>
          {selected ? selected.label : placeholder}
        </span>
        <svg
          className={`w-4 h-4 text-gray-400 shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

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
                const isSelected = opt.value === value;
                return (
                  <button
                    key={i}
                    type="button"
                    onClick={() => select(opt)}
                    className={`w-full flex items-center justify-between gap-2 px-3 py-2.5 text-left hover:bg-burgundy-50 transition-colors ${
                      isSelected ? 'bg-burgundy-50' : ''
                    }`}
                  >
                    <span className="min-w-0">
                      <span className={`block text-sm truncate ${isSelected ? 'font-medium text-burgundy-700' : 'text-gray-900'}`}>
                        {opt.label}
                      </span>
                      {opt.sublabel && (
                        <span className="block text-xs text-gray-400 truncate">{opt.sublabel}</span>
                      )}
                    </span>
                    {isSelected && (
                      <svg className="w-4 h-4 text-burgundy-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </button>
                );
              })
            )}
          </div>
        </div>,
        document.body,
      )}
    </div>
  );
}
