'use client';

import { useState } from 'react';

interface DateRangePickerProps {
  onDateChange: (days: number) => void;
  selectedDays?: number;
}

export function DateRangePicker({ onDateChange, selectedDays = 0 }: DateRangePickerProps) {
  const [isOpen, setIsOpen] = useState(false);

  const presets = [
    { label: 'Today', days: 0 },
    { label: 'Last 7 days', days: 7 },
    { label: 'Last 14 days', days: 14 },
    { label: 'Last 30 days', days: 30 },
  ];

  const today = new Date();
  const selectedDate = new Date(today);
  selectedDate.setDate(selectedDate.getDate() - selectedDays);

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-3 py-1.5 border border-[var(--border)] rounded bg-[var(--bg2)] text-xs uppercase tracking-widest text-[var(--text2)] hover:border-[var(--text2)] transition-colors"
      >
        {formatDate(selectedDate)} — {formatDate(today)}
      </button>

      {isOpen && (
        <div className="absolute top-full mt-2 left-0 border border-[var(--border)] bg-[var(--bg2)] rounded p-3 z-10 w-48">
          <div className="text-xs uppercase tracking-widest text-[var(--text3)] mb-2">Quick select</div>
          <div className="flex flex-col gap-2">
            {presets.map(preset => (
              <button
                key={preset.days}
                onClick={() => {
                  onDateChange(preset.days);
                  setIsOpen(false);
                }}
                className={`text-left px-2 py-1 rounded text-xs ${
                  selectedDays === preset.days
                    ? 'bg-[var(--bg3)] text-[var(--accent)]'
                    : 'text-[var(--text2)] hover:text-[var(--text)]'
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
