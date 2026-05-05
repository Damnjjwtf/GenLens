'use client';

import { useState, useEffect } from 'react';
import { DimensionFilter } from './DimensionFilter';
import { DateRangePicker } from './DateRangePicker';
import { SignalCard } from './SignalCard';
import { VerticalToggle } from './VerticalToggle';

type Vertical = 'product_photography' | 'filmmaking' | 'digital_humans';

interface MainFeedProps {
  defaultVertical?: Vertical;
  signals?: Array<{
    id: number;
    title: string;
    dimension: number;
    summary: string;
    source_name: string;
    source_url: string;
    time_saved_hours: number | null;
    cost_saved_dollars: number | null;
    vertical: Vertical;
    tool_names: string[];
    created_at: string;
  }>;
}

// Fallback demo signals for demo
const DEMO_SIGNALS = [
  {
    id: 1,
    title: 'KeyShot 2026 AI Shots: Glass reflections now 95% match-to-photo',
    dimension: 5,
    summary: 'Material accuracy for hard goods rendering improved dramatically with neural material inference. Users report 2h savings per render batch.',
    source: 'KeyShot Blog',
    sourceUrl: 'https://keyshot.com/blog',
    timeSaved: 2,
    costSaved: 0,
    vertical: 'product_photography' as Vertical,
    tools: ['KeyShot', 'Substance 3D'],
    createdAt: new Date('2026-05-03'),
  },
  {
    id: 2,
    title: 'ElevenLabs emotional prosody now in 29 languages',
    dimension: 1,
    summary: 'Voice synthesis quality expanded with emotion control across nearly all major languages. Affects voice-over and digital human workflows.',
    source: 'ElevenLabs Changelog',
    sourceUrl: 'https://elevenlabs.io/changelog',
    timeSaved: 0,
    costSaved: 180,
    vertical: 'digital_humans' as Vertical,
    tools: ['ElevenLabs'],
    createdAt: new Date('2026-05-02'),
  },
  {
    id: 3,
    title: 'Runway Gen-3 inference 40% faster on motion-only prompts',
    dimension: 5,
    summary: 'Faster generation time for motion transfer and video composition. Reduces iteration time in VFX workflows.',
    source: 'Runway Release Notes',
    sourceUrl: 'https://runwayml.com/blog',
    timeSaved: 1.5,
    costSaved: 240,
    vertical: 'filmmaking' as Vertical,
    tools: ['Runway Gen-3'],
    createdAt: new Date('2026-05-01'),
  },
  {
    id: 4,
    title: 'SAG-AFTRA expands digital replica guidelines',
    dimension: 6,
    summary: 'New disclosure requirements for synthetic actor work. Affects licensing and production workflows for digital humans content.',
    source: 'SAG-AFTRA News',
    sourceUrl: 'https://sagaftra.org/news',
    timeSaved: 0,
    costSaved: 0,
    vertical: 'digital_humans' as Vertical,
    tools: [],
    createdAt: new Date('2026-04-30'),
  },
  {
    id: 5,
    title: 'Claid AI background generation adds style transfer',
    dimension: 2,
    summary: 'AI-powered background generation now supports style matching. Enables faster lifestyle product photography workflows.',
    source: 'Claid AI Blog',
    sourceUrl: 'https://claid.ai/blog',
    timeSaved: 1,
    costSaved: 350,
    vertical: 'product_photography' as Vertical,
    tools: ['Claid', 'KeyShot'],
    createdAt: new Date('2026-04-28'),
  },
];

export function MainFeed({ defaultVertical = 'product_photography', signals: propsSignals }: MainFeedProps) {
  const [vertical, setVertical] = useState<Vertical>(defaultVertical);
  const [dimensions, setDimensions] = useState<number[]>([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
  const [daysBack, setDaysBack] = useState(0);

  // Convert real signals to display format, or fall back to demo
  const signals = propsSignals?.map(s => ({
    ...s,
    source: s.source_name,
    sourceUrl: s.source_url,
    timeSaved: s.time_saved_hours,
    costSaved: s.cost_saved_dollars,
    tools: s.tool_names || [],
    createdAt: new Date(s.created_at),
  })) || DEMO_SIGNALS;

  const filteredSignals = signals.filter(signal => {
    const matchesVertical = signal.vertical === vertical;
    const matchesDimension = dimensions.includes(signal.dimension);
    return matchesVertical && matchesDimension;
  });

  return (
    <div className="flex-1">
      {/* Filter bar */}
      <div className="mb-6 space-y-4">
        <div className="flex items-center justify-between">
          <VerticalToggle vertical={vertical} onChange={setVertical} />
          <DateRangePicker onDateChange={setDaysBack} selectedDays={daysBack} />
        </div>

        <div>
          <div className="text-xs uppercase tracking-widest text-[var(--text3)] mb-2">Filter by dimension</div>
          <DimensionFilter selected={dimensions} onChange={setDimensions} />
        </div>
      </div>

      {/* Signals feed */}
      <div className="space-y-4">
        {filteredSignals.length > 0 ? (
          filteredSignals.map(signal => (
            <SignalCard key={signal.id} {...signal} />
          ))
        ) : (
          <div className="border border-[var(--border)] bg-[var(--bg2)] p-6 rounded text-center">
            <p className="text-[var(--text3)]">No signals match your filters.</p>
          </div>
        )}
      </div>
    </div>
  );
}
