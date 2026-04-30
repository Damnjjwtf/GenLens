'use client';

import { VERTICAL_LABELS, VERTICAL_ACCENT } from '@/lib/constants';

type Vertical = 'product_photography' | 'filmmaking' | 'digital_humans';

interface VerticalToggleProps {
  vertical: Vertical;
  onChange: (vertical: Vertical) => void;
}

export function VerticalToggle({ vertical, onChange }: VerticalToggleProps) {
  const verticals: Vertical[] = ['product_photography', 'filmmaking', 'digital_humans'];

  return (
    <div className="flex gap-2">
      {verticals.map(v => (
        <button
          key={v}
          onClick={() => onChange(v)}
          className={`
            px-3 py-1.5 rounded border text-xs uppercase tracking-widest font-mono
            transition-all duration-200
            ${vertical === v
              ? `border-[var(--accent)] bg-[var(--bg3)] text-[var(--accent)]`
              : 'border-[var(--border)] bg-transparent text-[var(--text2)] hover:border-[var(--text2)]'
            }
          `}
        >
          {VERTICAL_LABELS[v]}
        </button>
      ))}
    </div>
  );
}
