'use client';

interface SparklineProps {
  data: number[];
  height?: number;
  width?: number;
  color?: string;
}

export function Sparkline({ data, height = 24, width = 60, color = 'currentColor' }: SparklineProps) {
  if (data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const padding = 1;
  const graphWidth = width - padding * 2;
  const graphHeight = height - padding * 2;

  const points = data.map((value, idx) => {
    const x = padding + (idx / (data.length - 1)) * graphWidth;
    const y = padding + graphHeight - ((value - min) / range) * graphHeight;
    return `${x},${y}`;
  }).join(' ');

  const isPositive = data[data.length - 1] >= data[0];

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="inline-block">
      <polyline
        points={points}
        fill="none"
        stroke={isPositive ? '#caff3f' : '#f87171'}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
