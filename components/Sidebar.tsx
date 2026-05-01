'use client';

import { Sparkline } from './Sparkline';

interface SidebarStats {
  trendingScore?: number;
  recentSignals?: number;
  topTools?: Array<{ name: string; score: number; change: number; trend: number[] }>;
  topTemplates?: Array<{ name: string; adoption: number }>;
}

interface SidebarProps {
  stats?: SidebarStats;
}

export function Sidebar({ stats }: SidebarProps) {
  const defaultStats: SidebarStats = {
    trendingScore: 342,
    recentSignals: 24,
    topTools: [
      { name: 'KeyShot 2026', score: 87, change: +12, trend: [40, 50, 65, 70, 85, 87] },
      { name: 'ElevenLabs', score: 84, change: +8, trend: [45, 55, 70, 78, 82, 84] },
      { name: 'Runway Gen-3', score: 81, change: -2, trend: [85, 83, 82, 81, 81, 81] },
    ],
    topTemplates: [
      { name: 'KeyShot + Claid Workflow', adoption: 156 },
      { name: 'ElevenLabs Voice Pipeline', adoption: 128 },
      { name: 'Runway Composite Stack', adoption: 94 },
    ],
  };

  const displayStats = stats || defaultStats;

  return (
    <aside className="w-72 flex-shrink-0 space-y-6">
      {/* Quick Stats */}
      <div className="border border-[var(--border)] bg-[var(--bg2)] p-4 rounded">
        <div className="text-xs uppercase tracking-widest text-[var(--text3)] mb-4">Quick Stats</div>

        <div className="space-y-3">
          <div>
            <div className="text-2xl font-serif text-[var(--accent)]">{displayStats.trendingScore}</div>
            <div className="text-xs text-[var(--text3)]">Overall trending score</div>
          </div>

          <div className="pt-2 border-t border-[var(--border)]">
            <div className="text-lg text-[var(--text)]">{displayStats.recentSignals}</div>
            <div className="text-xs text-[var(--text3)]">Signals this week</div>
          </div>
        </div>
      </div>

      {/* Top Tools */}
      <div className="border border-[var(--border)] bg-[var(--bg2)] p-4 rounded">
        <div className="text-xs uppercase tracking-widest text-[var(--text3)] mb-4">Top Tools</div>

        <div className="space-y-3">
          {displayStats.topTools?.map((tool, idx) => (
            <div key={idx} className="text-xs">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[var(--text)] font-mono">{tool.name}</span>
                <span className={`font-mono ${tool.change >= 0 ? 'text-[#22c55e]' : 'text-[#f87171]'}`}>
                  {tool.change >= 0 ? '+' : ''}{tool.change}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[var(--text3)]">Score: {tool.score}</span>
                <Sparkline data={tool.trend} width={50} height={16} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Top Templates */}
      <div className="border border-[var(--border)] bg-[var(--bg2)] p-4 rounded">
        <div className="text-xs uppercase tracking-widest text-[var(--text3)] mb-4">Trending Templates</div>

        <div className="space-y-2">
          {displayStats.topTemplates?.map((template, idx) => (
            <div key={idx} className="text-xs">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[var(--text)] line-clamp-2">{template.name}</span>
              </div>
              <div className="text-[var(--text3)]">{template.adoption} adopters</div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
