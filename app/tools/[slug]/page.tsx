import { getAllTools, canonicalNameToSlug, slugToCanonicalName } from '@/lib/tools';
import Link from 'next/link';
import { notFound } from 'next/navigation';

const cachedGetAllTools = async () => getAllTools();

export async function generateStaticParams() {
  const tools = await cachedGetAllTools();
  return tools.map(tool => ({
    slug: canonicalNameToSlug(tool.canonical_name),
  }));
}

export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}) {
  const tools = await cachedGetAllTools();
  const tool = slugToCanonicalName(tools, params.slug);

  if (!tool) return { title: 'Tool Not Found' };

  return {
    title: `${tool.canonical_name} | GenLens`,
    description: `Learn about ${tool.canonical_name} for ${tool.category}. Discover how creators are using this tool.`,
  };
}

export default async function ToolPage({
  params,
}: {
  params: { slug: string };
}) {
  const tools = await cachedGetAllTools();
  const tool = slugToCanonicalName(tools, params.slug);

  if (!tool) {
    notFound();
  }

  const relatedTools = tools.filter(
    t =>
      t.id !== tool.id &&
      t.category === tool.category &&
      t.verticals?.some(v => tool.verticals?.includes(v))
  );

  return (
    <main className="min-h-screen bg-[var(--bg)]">
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--bg)]">
        <div className="px-6 py-8 max-w-4xl mx-auto">
          <Link href="/tools" className="text-xs uppercase tracking-widest text-[var(--text3)] hover:text-[var(--text2)] mb-4 inline-block">
            ← All Tools
          </Link>
          <div className="flex items-start justify-between gap-6 mb-6">
            <div className="flex-1">
              <h1 className="font-serif text-4xl text-[var(--text)] mb-2">{tool.canonical_name}</h1>
              <p className="text-sm text-[var(--text2)]">{tool.vendor_name}</p>
            </div>
            <span className="px-3 py-1 rounded bg-[var(--bg2)] border border-[var(--border)] text-xs uppercase tracking-widest text-[var(--text3)]">
              {tool.pricing_tier}
            </span>
          </div>

          {/* Metadata */}
          <div className="flex flex-wrap gap-4 py-4 border-t border-[var(--border)]">
            <div>
              <div className="text-xs uppercase tracking-widest text-[var(--text3)] mb-1">Category</div>
              <div className="text-sm text-[var(--text)]">{tool.category}</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-widest text-[var(--text3)] mb-1">Verticals</div>
              <div className="flex gap-2">
                {tool.verticals?.map(v => (
                  <span
                    key={v}
                    className="px-2 py-1 rounded bg-[var(--bg2)] border border-[var(--border)] text-xs text-[var(--text)]"
                  >
                    {v === 'product_photography'
                      ? 'Product Photography'
                      : v === 'filmmaking'
                      ? 'Filmmaking'
                      : 'Digital Humans'}
                  </span>
                ))}
              </div>
            </div>
            {tool.website && (
              <div>
                <div className="text-xs uppercase tracking-widest text-[var(--text3)] mb-1">Website</div>
                <a
                  href={tool.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-[var(--accent)] hover:underline"
                >
                  {tool.website.replace(/^https?:\/\/(www\.)?/, '')}
                </a>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="px-6 py-12 max-w-4xl mx-auto">
        {/* Aliases */}
        {tool.aliases && tool.aliases.length > 0 && (
          <section className="mb-12 border border-[var(--border)] bg-[var(--bg2)] p-6 rounded">
            <h2 className="text-xs uppercase tracking-widest text-[var(--text3)] mb-3">Also known as</h2>
            <div className="flex flex-wrap gap-2">
              {tool.aliases.map(alias => (
                <span
                  key={alias}
                  className="px-2 py-1 rounded bg-[var(--bg)] border border-[var(--border)] text-xs text-[var(--text2)]"
                >
                  {alias}
                </span>
              ))}
            </div>
          </section>
        )}

        {/* Dimensions */}
        {tool.dimensions && tool.dimensions.length > 0 && (
          <section className="mb-12 border border-[var(--border)] bg-[var(--bg2)] p-6 rounded">
            <h2 className="text-xs uppercase tracking-widest text-[var(--text3)] mb-3">Intelligence dimensions</h2>
            <p className="text-sm text-[var(--text2)] mb-4">
              This tool appears in signals about:
            </p>
            <div className="flex flex-wrap gap-2">
              {tool.dimensions.map(dim => {
                const labels: Record<number, string> = {
                  1: 'Workflow Stages',
                  2: 'Product Categories',
                  3: 'Competitive',
                  4: 'Templates',
                  5: 'Cost/Time',
                  6: 'Legal/Ethics',
                  7: 'Hiring',
                  8: 'Integration',
                  9: 'Trends',
                  10: 'Leaderboard',
                };
                return (
                  <span
                    key={dim}
                    className="px-3 py-1 rounded border border-[var(--border)] text-xs font-mono text-[var(--text)]"
                  >
                    {dim}. {labels[dim]}
                  </span>
                );
              })}
            </div>
          </section>
        )}

        {/* Description */}
        <section className="mb-12">
          <h2 className="font-serif text-2xl text-[var(--text)] mb-4">About</h2>
          <div className="border border-[var(--border)] bg-[var(--bg2)] p-6 rounded text-sm text-[var(--text2)]">
            <p className="mb-4">
              {tool.canonical_name} is a {tool.pricing_tier} {tool.category.toLowerCase()} tool used in{' '}
              {tool.verticals?.join(', ').replace(/_/g, ' ')} workflows.
            </p>
            <p>
              Sign up for GenLens to see how creators are using {tool.canonical_name}, latest releases, cost/time savings, and more.
            </p>
          </div>
        </section>

        {/* Related tools */}
        {relatedTools.length > 0 && (
          <section className="mb-12">
            <h2 className="font-serif text-2xl text-[var(--text)] mb-6">Related Tools</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {relatedTools.slice(0, 4).map(related => (
                <Link
                  key={related.id}
                  href={`/tools/${canonicalNameToSlug(related.canonical_name)}`}
                  className="border border-[var(--border)] bg-[var(--bg2)] p-4 rounded hover:bg-[var(--bg3)] transition-colors"
                >
                  <h3 className="font-mono text-sm text-[var(--text)] mb-1">{related.canonical_name}</h3>
                  <p className="text-xs text-[var(--text3)]">{related.category}</p>
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* CTA */}
        <section className="border-t border-[var(--border)] pt-12">
          <div className="bg-[var(--bg2)] border border-[var(--border)] p-8 rounded text-center">
            <h3 className="font-serif text-xl text-[var(--text)] mb-2">
              See {tool.canonical_name} in Daily Intelligence
            </h3>
            <p className="text-sm text-[var(--text2)] mb-4 max-w-md mx-auto">
              Get notified when {tool.canonical_name} releases updates, see how it's trending among creators, and discover cost/time savings.
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
