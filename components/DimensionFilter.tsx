'use client';

import { DIMENSIONS } from '@/lib/constants';

interface DimensionFilterProps {
  selected: number[];
  onChange: (dimensions: number[]) => void;
}

export function DimensionFilter({ selected, onChange }: DimensionFilterProps) {
  const toggleDimension = (id: number) => {
    if (selected.includes(id)) {
      onChange(selected.filter(d => d !== id));
    } else {
      onChange([...selected, id].sort());
    }
  };

  return (
    <div className="flex gap-2 flex-wrap mb-6">
      {DIMENSIONS.map(dim => (
        <button
          key={dim.id}
          onClick={() => toggleDimension(dim.id)}
          className={`
            px-3 py-1.5 rounded border text-xs uppercase tracking-widest
            transition-all duration-200
            ${selected.includes(dim.id)
              ? 'border-[var(--accent)] bg-[var(--bg3)] text-[var(--accent)]'
              : 'border-[var(--border)] bg-transparent text-[var(--text2)] hover:border-[var(--text2)]'
            }
          `}
        >
          {dim.id}
        </button>
      ))}
    </div>
  );
}
