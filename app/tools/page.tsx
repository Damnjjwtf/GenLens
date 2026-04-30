import { getAllTools } from '@/lib/tools';
import Link from 'next/link';

export const metadata = {
  title: 'Tool Directory | GenLens',
  description: 'Browse 130+ AI tools for creative technologists. Find tools by vertical, category, and pricing.',
};

export default async function ToolsPage() {
  const tools = await getAllTools();

  // Group by vertical
  const byVertical = {
    product_photography: tools.filter(t => t.verticals?.includes('product_photography')),
    filmmaking: tools.filter(t => t.verticals?.includes('filmmaking')),
    digital_humans: tools.filter(t => t.verticals?.includes('digital_humans')),
  };

  // Group by category
  const byCategory = tools.reduce((acc, tool) => {
    const cat = tool.category || 'Other';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(tool);
    return acc;
  }, {} as Record<string, typeof tools>);

  const verticalLabels = {
    product_photography: 'Product Photography',
    filmmaking: 'Commercial Filmmaking',
    digital_humans: 'Digital Humans',
  };

  return (
    <main className="min-h-screen bg-[var(--bg)]">
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--bg)]">
        <div className="px-6 py-8 max-w-7xl mx-auto">
          <Link href="/" className="text-xs uppercase tracking-widest text-[var(--text3)] hover:text-[var(--text2)] mb-4 inline-block">
            ← Back
          </Link>
          <h1 className="font-serif text-4xl text-[var(--text)] mb-2">Tool Directory</h1>
          <p className="text-sm text-[var(--text2)] max-w-2xl">
            Browse {tools.length}+ AI tools tracked across product photography, commercial filmmaking, and digital humans.
          </p>
        </div>
      </header>

      <div className="px-6 py-12 max-w-7xl mx-auto space-y-12">
        {/* By Vertical */}
        <section>
          <h2 className="font-serif text-2xl text-[var(--text)] mb-6">By Vertical</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {Object.entries(byVertical).map(([vertical, verticalTools]) => (
              <div key={vertical} className="border border-[var(--border)] bg-[var(--bg2)] p-6 rounded">
                <h3 className="font-serif text-lg text-[var(--text)] mb-3">
                  {verticalLabels[vertical as keyof typeof verticalLabels]}
                </h3>
                <p className="text-xs text-[var(--text3)] mb-4">{verticalTools.length} tools</p>
                <div className="space-y-2">
                  {verticalTools.slice(0, 8).map(tool => (
                    <Link
                      key={tool.id}
                      href={`/tools/${tool.canonical_name.toLowerCase().replace(/\s+/g, '-')}`}
                      className="block text-sm text-[var(--text2)] hover:text-[var(--accent)] transition-colors"
                    >
                      {tool.canonical_name}
                    </Link>
                  ))}
                  {verticalTools.length > 8 && (
                    <p className="text-xs text-[var(--text3)] pt-2">
                      +{verticalTools.length - 8} more
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* By Category */}
        <section>
          <h2 className="font-serif text-2xl text-[var(--text)] mb-6">By Category</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(byCategory)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([category, categoryTools]) => (
                <div key={category} className="border border-[var(--border)] bg-[var(--bg2)] p-6 rounded">
                  <h3 className="font-mono text-sm text-[var(--text)] mb-3 uppercase tracking-widest">
                    {category}
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {categoryTools.map(tool => (
                      <Link
                        key={tool.id}
                        href={`/tools/${tool.canonical_name.toLowerCase().replace(/\s+/g, '-')}`}
                        className="px-2 py-1 text-xs border border-[var(--border)] rounded text-[var(--text2)] hover:border-[var(--accent)] hover:text-[var(--accent)] transition-colors"
                      >
                        {tool.canonical_name}
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
          </div>
        </section>

        {/* All Tools (searchable list) */}
        <section>
          <h2 className="font-serif text-2xl text-[var(--text)] mb-6">All Tools</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tools
              .sort((a, b) => a.canonical_name.localeCompare(b.canonical_name))
              .map(tool => (
                <Link
                  key={tool.id}
                  href={`/tools/${tool.canonical_name.toLowerCase().replace(/\s+/g, '-')}`}
                  className="border border-[var(--border)] bg-[var(--bg2)] p-4 rounded hover:bg-[var(--bg3)] transition-colors"
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <h3 className="font-mono text-sm text-[var(--text)]">{tool.canonical_name}</h3>
                    <span className="text-xs px-2 py-1 rounded bg-[var(--bg3)] text-[var(--text3)]">
                      {tool.pricing_tier}
                    </span>
                  </div>
                  <p className="text-xs text-[var(--text3)] mb-2">{tool.vendor_name}</p>
                  <p className="text-xs text-[var(--text3)] mb-3">{tool.category}</p>
                  <div className="flex gap-1 flex-wrap">
                    {tool.verticals?.map(v => (
                      <span key={v} className="text-xs px-2 py-0.5 rounded border border-[var(--border)] text-[var(--text3)]">
                        {v === 'product_photography' ? 'PP' : v === 'filmmaking' ? 'FM' : 'DH'}
                      </span>
                    ))}
                  </div>
                </Link>
              ))}
          </div>
        </section>

        {/* Footer CTA */}
        <section className="border-t border-[var(--border)] pt-12">
          <div className="bg-[var(--bg2)] border border-[var(--border)] p-8 rounded text-center">
            <h3 className="font-serif text-xl text-[var(--text)] mb-2">Get Daily Intelligence</h3>
            <p className="text-sm text-[var(--text2)] mb-4">
              See how these tools are trending, what creators are shipping, and how much time & money they save.
            </p>
            <Link
              href="/#early-access"
              className="inline-block px-4 py-2 bg-[var(--accent)] text-[var(--bg)] text-xs uppercase tracking-widest font-mono rounded hover:opacity-80 transition-opacity"
            >
              Join Beta
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
