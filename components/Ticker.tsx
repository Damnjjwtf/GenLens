'use client';

interface TickerItem {
  headline: string;
  vertical: 'product_photography' | 'filmmaking' | 'digital_humans';
  timestamp: string;
}

interface TickerProps {
  items?: TickerItem[];
}

export function Ticker({ items = [] }: TickerProps) {
  // Placeholder items for demo
  const placeholderItems: TickerItem[] = [
    {
      headline: 'KeyShot 2026 AI Shots drops, glass accuracy +95%',
      vertical: 'product_photography',
      timestamp: '2m ago'
    },
    {
      headline: 'ElevenLabs emotional prosody now in 29 languages',
      vertical: 'digital_humans',
      timestamp: '14m ago'
    },
    {
      headline: 'Runway Gen-3 motion transfer: faster inference',
      vertical: 'filmmaking',
      timestamp: '47m ago'
    },
  ];

  const displayItems = items.length > 0 ? items : placeholderItems;

  return (
    <div className="border-b border-[var(--border)] bg-[var(--bg)] mb-6">
      <div className="flex gap-4 overflow-x-auto py-3 px-6 max-w-6xl mx-auto">
        <div className="text-xs uppercase tracking-widest text-[var(--text2)] whitespace-nowrap pt-1">
          Live ticker
        </div>
        <div className="flex gap-6 flex-1 overflow-x-auto pb-2">
          {displayItems.map((item, idx) => (
            <div key={idx} className="flex items-center gap-3 whitespace-nowrap text-xs">
              <span className="text-[var(--text2)]">·</span>
              <span className="text-[var(--text)]">{item.headline}</span>
              <span className="text-[var(--text3)]">{item.timestamp}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
