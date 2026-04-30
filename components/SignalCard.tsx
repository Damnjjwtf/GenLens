'use client';

import { DIMENSIONS } from '@/lib/constants';

interface SignalCardProps {
  id: number;
  title: string;
  dimension: number;
  summary: string;
  source: string;
  sourceUrl?: string;
  timeSaved?: number;
  costSaved?: number;
  vertical: 'product_photography' | 'filmmaking' | 'digital_humans';
  tools?: string[];
}

export function SignalCard({
  id,
  title,
  dimension,
  summary,
  source,
  sourceUrl,
  timeSaved,
  costSaved,
  vertical,
  tools = [],
}: SignalCardProps) {
  const dimLabel = DIMENSIONS.find(d => d.id === dimension)?.label || 'Signal';

  // Get dimension color based on number
  const getDimensionColor = (dim: number) => {
    const colors: Record<number, string> = {
      1: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
      2: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
      3: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
      4: 'bg-green-500/20 text-green-300 border-green-500/30',
      5: 'bg-lime-500/20 text-lime-300 border-lime-500/30',
      6: 'bg-red-500/20 text-red-300 border-red-500/30',
      7: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
      8: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
      9: 'bg-pink-500/20 text-pink-300 border-pink-500/30',
      10: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
    };
    return colors[dim] || colors[1];
  };

  return (
    <article className="border border-[var(--border)] bg-[var(--bg2)] p-5 rounded hover:bg-[var(--bg3)] transition-colors">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex-1">
          <h3 className="text-sm font-serif text-[var(--text)] mb-2 leading-tight hover:text-[var(--accent)] cursor-pointer">
            {title}
          </h3>
          <div className="flex gap-2 flex-wrap">
            <span className={`text-xs px-2 py-1 rounded border ${getDimensionColor(dimension)}`}>
              Dim {dimension}
            </span>
            {tools.slice(0, 2).map(tool => (
              <span key={tool} className="text-xs px-2 py-1 rounded border border-[var(--border)] text-[var(--text3)]">
                {tool}
              </span>
            ))}
          </div>
        </div>
      </div>

      <p className="text-xs text-[var(--text2)] mb-4 leading-relaxed">
        {summary}
      </p>

      {(timeSaved || costSaved) && (
        <div className="flex gap-3 mb-4 py-3 border-y border-[var(--border)]">
          {timeSaved && (
            <div className="text-xs">
              <div className="font-mono text-[var(--accent)] font-bold">−{timeSaved}h</div>
              <div className="text-[var(--text3)]">time saved</div>
            </div>
          )}
          {costSaved && (
            <div className="text-xs">
              <div className="font-mono text-[var(--accent)] font-bold">−${costSaved}</div>
              <div className="text-[var(--text3)]">cost saved</div>
            </div>
          )}
        </div>
      )}

      <div className="flex items-center justify-between text-xs">
        <a
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[var(--text3)] hover:text-[var(--blue)]"
        >
          {source}
        </a>
        <button className="text-[var(--text3)] hover:text-[var(--text)] transition-colors">
          ↗
        </button>
      </div>
    </article>
  );
}
