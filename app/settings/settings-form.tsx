'use client';

import { useState } from 'react';
import { VERTICALS, VERTICAL_LABELS, DIMENSIONS, type Vertical } from '@/lib/constants';
import type { UserPreferences } from '@/lib/db';

const TIMEZONES = [
  'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
  'Europe/London', 'Europe/Berlin', 'Asia/Tokyo', 'UTC',
];

export default function SettingsForm({ initial }: { initial: UserPreferences | null }) {
  const [verticals, setVerticals] = useState<Vertical[]>(
    (initial?.active_verticals as Vertical[]) ?? [...VERTICALS],
  );
  const [dims, setDims] = useState<number[]>(
    initial?.dimensions_visible ?? DIMENSIONS.map((d) => d.id),
  );
  const [frequency, setFrequency] = useState(initial?.delivery_frequency ?? 'daily');
  const [timezone, setTimezone] = useState(initial?.delivery_timezone ?? 'America/New_York');
  const [outputs, setOutputs] = useState<string[]>(
    initial?.output_formats ?? ['email', 'dashboard'],
  );
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  function toggle<T>(arr: T[], value: T): T[] {
    return arr.includes(value) ? arr.filter((v) => v !== value) : [...arr, value];
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setSaved(false);
    await fetch('/api/settings', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        active_verticals: verticals,
        dimensions_visible: dims,
        delivery_frequency: frequency,
        delivery_timezone: timezone,
        output_formats: outputs,
      }),
    });
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <form onSubmit={save} className="space-y-8">
      <section>
        <h2 className="text-xs text-[var(--text2)] uppercase tracking-widest mb-3">Verticals</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {VERTICALS.map((v) => (
            <label
              key={v}
              className={`border px-3 py-2 cursor-pointer text-sm ${
                verticals.includes(v)
                  ? 'border-[var(--accent)] text-[var(--text)]'
                  : 'border-[var(--border)] text-[var(--text2)]'
              }`}
            >
              <input
                type="checkbox"
                checked={verticals.includes(v)}
                onChange={() => setVerticals(toggle(verticals, v))}
                className="mr-2 accent-[var(--accent)]"
              />
              {VERTICAL_LABELS[v]}
            </label>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xs text-[var(--text2)] uppercase tracking-widest mb-3">
          Dimensions visible
        </h2>
        <div className="grid grid-cols-2 gap-2">
          {DIMENSIONS.map((d) => (
            <label
              key={d.id}
              className={`border px-3 py-2 cursor-pointer text-xs ${
                dims.includes(d.id)
                  ? 'border-[var(--accent)] text-[var(--text)]'
                  : 'border-[var(--border)] text-[var(--text2)]'
              }`}
            >
              <input
                type="checkbox"
                checked={dims.includes(d.id)}
                onChange={() => setDims(toggle(dims, d.id))}
                className="mr-2 accent-[var(--accent)]"
              />
              <span className="text-[var(--text3)]">D{d.id}</span> {d.label}
            </label>
          ))}
        </div>
      </section>

      <section className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div>
          <h2 className="text-xs text-[var(--text2)] uppercase tracking-widest mb-3">
            Delivery frequency
          </h2>
          <select
            value={frequency}
            onChange={(e) => setFrequency(e.target.value)}
            className="w-full bg-[var(--bg2)] border border-[var(--border2)] px-3 py-2 text-[var(--text)]"
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
          </select>
        </div>
        <div>
          <h2 className="text-xs text-[var(--text2)] uppercase tracking-widest mb-3">Timezone</h2>
          <select
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            className="w-full bg-[var(--bg2)] border border-[var(--border2)] px-3 py-2 text-[var(--text)]"
          >
            {TIMEZONES.map((tz) => (
              <option key={tz} value={tz}>{tz}</option>
            ))}
          </select>
        </div>
      </section>

      <section>
        <h2 className="text-xs text-[var(--text2)] uppercase tracking-widest mb-3">Output formats</h2>
        <div className="flex gap-2 flex-wrap">
          {['email', 'dashboard', 'slack'].map((o) => (
            <label
              key={o}
              className={`border px-3 py-2 cursor-pointer text-sm ${
                outputs.includes(o)
                  ? 'border-[var(--accent)] text-[var(--text)]'
                  : 'border-[var(--border)] text-[var(--text2)]'
              }`}
            >
              <input
                type="checkbox"
                checked={outputs.includes(o)}
                onChange={() => setOutputs(toggle(outputs, o))}
                className="mr-2 accent-[var(--accent)]"
              />
              {o}
            </label>
          ))}
        </div>
      </section>

      <div className="flex items-center gap-4 pt-4 border-t border-[var(--border)]">
        <button
          type="submit"
          disabled={saving}
          className="bg-[var(--accent)] text-[var(--bg)] px-6 py-2 font-mono text-sm uppercase tracking-widest disabled:opacity-50"
        >
          {saving ? 'Saving…' : 'Save preferences'}
        </button>
        {saved && <span className="text-xs text-[var(--accent)]">Saved.</span>}
      </div>
    </form>
  );
}
