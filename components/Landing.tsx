'use client'

import { useState } from 'react'
import type { FormEvent } from 'react'

type Lens = 'genny' | 'marti'

type Example = {
  byline: string
  headline: string
  change: string
  implication: string
  action: string
  source: string
  url: string
}

const examples: Record<Lens, Example> = {
  genny: {
    byline: 'GENNY / CREATIVE TECHNOLOGY',
    headline: 'Legible type enters the image-generation workflow.',
    change: 'On October 12, Runway Dev added Ideogram 4.5, with typography, reference images, and precise editing options.',
    implication: 'More of an advertising layout can be explored in one production flow. Client-quality text and brand fidelity still need testing.',
    action: 'Generate 10 on-brand ad layouts. Score legibility, visual consistency, correction time, and credits used.',
    source: 'Runway Developer Changelog',
    url: 'https://docs.dev.runwayml.com/api-details/api_changelog/',
  },
  marti: {
    byline: 'MARTI / GTM ENGINEERING',
    headline: 'Audience match rates become easier to reconcile.',
    change: 'Clay announced an October 12 update to show ad-platform audience sizes and match rates alongside its own sent-record count.',
    implication: 'A GTM operator can better inspect audience delivery before changing targeting or campaign budgets.',
    action: 'Compare one Clay audience with its destination platform. Document record count, matched size, and mismatches.',
    source: 'Clay Product Roundup, October 12',
    url: 'https://www.clay.com/fr/changelog/product-roundup-week-of-october-5-2026',
  },
}

export default function Landing() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [subscribed, setSubscribed] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lens, setLens] = useState<Lens>('genny')

  async function subscribe(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (loading || subscribed) return
    setLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/waitlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() }),
      })
      if (!response.ok) throw new Error('Request failed')
      setSubscribed(true)
      setEmail('')
    } catch {
      setError('The signup did not go through. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const example = examples[lens]

  return (
    <main className="min-h-screen bg-[#0e110f] font-sans text-[#ecece5] selection:bg-[#cbe983] selection:text-[#0e110f]">
      <div className="mx-auto max-w-[1240px] px-5 sm:px-9 lg:px-12">
        <header className="flex min-h-[84px] items-center justify-between gap-4 border-b border-[#303730] sm:min-h-[96px]">
          <a href="/" aria-label="GenLens home" className="whitespace-nowrap text-[29px] font-semibold tracking-[-0.075em] text-[#efeee9] no-underline hover:text-white sm:text-[34px]">
            GenLens<span className="text-[#c6e681]">.</span>
          </a>
          <nav aria-label="Main navigation" className="flex items-center gap-3 text-[11px] font-medium sm:gap-7 sm:text-xs">
            <a href="#inside" className="hidden text-[#a1a9a0] no-underline transition-colors hover:text-white sm:inline">Inside the brief</a>
            <a href="/auth/invite" className="whitespace-nowrap text-[#cfd5cb] no-underline transition-colors hover:text-white">Sign in</a>
            <a href="#early-access" className="whitespace-nowrap border border-[#c5e77d] px-3 py-2.5 font-semibold text-[#d4ef9e] no-underline transition-colors hover:bg-[#c5e77d] hover:text-[#0d100d] sm:px-4">
              Get access <span aria-hidden="true">↗</span>
            </a>
          </nav>
        </header>

        <section className="grid gap-12 border-b border-[#303730] pb-20 pt-14 lg:grid-cols-[minmax(0,1.06fr)_minmax(0,0.94fr)] lg:items-start lg:gap-14 lg:pb-24 lg:pt-24">
          <div className="max-w-[700px]">
            <div className="mb-8 flex items-center gap-3 font-mono text-[10px] font-medium tracking-[0.18em] text-[#b0b9aa]">
              <span className="inline-block h-[6px] w-[6px] rounded-full bg-[#c5e77d]" aria-hidden="true" />
              INTELLIGENCE FOR SYSTEM BUILDERS
            </div>
            <h1 className="max-w-[690px] text-[clamp(3.5rem,9vw,6.9rem)] font-medium leading-[0.99] tracking-[-0.08em] text-[#f1f0ea]">
              <span className="block">Signal to</span>
              <span className="block">system<span className="text-[#c5e77d]">.</span></span>
            </h1>
            <p className="mt-8 max-w-[570px] text-[17px] leading-[1.65] text-[#b5bdb2] sm:mt-10 sm:text-xl">
              Evidence-backed updates on AI production and go-to-market technology. Understand what changed, where it matters, and what to test next.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-2.5 font-mono text-[10px] uppercase tracking-[0.10em] text-[#a1aaa0]">
              <span className="border border-[#3b463b] px-2.5 py-1.5">Creative technology</span>
              <span className="border border-[#3b463b] px-2.5 py-1.5">GTM engineering</span>
            </div>

            <div id="early-access" className="mt-12 max-w-[550px] scroll-mt-12 border-t border-[#3c4739] pt-6">
              <div className="mb-4 flex items-baseline justify-between gap-3">
                <h2 className="text-sm font-semibold tracking-[-0.015em]">Get the GenLens briefing</h2>
                <span className="font-mono text-[10px] text-[#899487]">EARLY ACCESS</span>
              </div>
              {subscribed ? (
                <p role="status" className="border border-[#687c4d] bg-[#1d271c] px-4 py-3 text-sm text-[#daefb5]">
                  You&apos;re on the waitlist. Thanks for signing up.
                </p>
              ) : (
                <form onSubmit={subscribe} className="flex flex-col gap-2 sm:flex-row">
                  <label htmlFor="landing-email" className="sr-only">Email address</label>
                  <input
                    id="landing-email"
                    type="email"
                    autoComplete="email"
                    inputMode="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    required
                    maxLength={254}
                    placeholder="Email address"
                    className="min-h-[50px] min-w-0 flex-1 rounded-none border border-[#465047] bg-[#171b18] px-4 text-base text-[#f1f0eb] placeholder:text-[#909a8d] focus:border-[#c5e77d] focus:outline-none sm:text-sm"
                  />
                  <button
                    type="submit"
                    disabled={loading}
                    className="min-h-[50px] shrink-0 rounded-none bg-[#c5e77d] px-5 text-sm font-semibold text-[#11170d] transition-colors hover:bg-[#d8f39a] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#c5e77d] disabled:cursor-wait disabled:opacity-60"
                  >
                    {loading ? 'Joining…' : 'Join the list →'}
                  </button>
                </form>
              )}
              {error && <p role="alert" className="mt-3 text-sm text-[#ffbcae]">{error}</p>}
              <p className="mt-3 text-xs leading-relaxed text-[#858e83]">
                A source-linked briefing, built for people who put new technology to work.
              </p>
            </div>
          </div>

          <aside id="inside" aria-label="Sample GenLens editorial signal" className="scroll-mt-7 border border-[#39443b] bg-[#181d19]">
            <div className="flex items-center justify-between gap-4 border-b border-[#39443b] px-5 py-4 font-mono text-[10px] uppercase tracking-[0.10em] text-[#aab7a6] sm:px-6">
              <span>Inside GenLens</span>
              <span className="text-[#c5e77d]">Sample / Oct 12, 2026</span>
            </div>
            <div role="tablist" aria-label="Choose an editorial lens" className="grid grid-cols-2 border-b border-[#39443b]">
              {(['genny', 'marti'] as Lens[]).map((name) => (
                <button
                  id={'tab-' + name}
                  key={name}
                  type="button"
                  role="tab"
                  aria-selected={lens === name}
                  aria-controls="sample-content"
                  onClick={() => setLens(name)}
                  className={
                    'min-h-[51px] border-b-2 px-3 text-left text-[13px] font-semibold transition-colors sm:px-6 ' +
                    (lens === name
                      ? 'border-[#c5e77d] bg-[#222b21] text-[#eff2e9]'
                      : 'border-transparent text-[#8f998d] hover:bg-[#1e241f] hover:text-[#ecf0e9]')
                  }
                >
                  {name === 'genny' ? 'Genny / Production' : 'Marti / GTM'}
                </button>
              ))}
            </div>
            <div id="sample-content" role="tabpanel" aria-labelledby={'tab-' + lens} className="px-5 pb-6 pt-7 sm:px-6 sm:pb-8">
              <p className="font-mono text-[10px] tracking-[0.12em] text-[#c8dfac]">{example.byline}</p>
              <h2 className="mt-4 text-[26px] font-medium leading-[1.2] tracking-[-0.045em] text-[#f1f0eb] sm:text-[30px]">
                {example.headline}
              </h2>
              <div className="mt-6 space-y-5">
                <div>
                  <p className="mb-1.5 font-mono text-[10px] uppercase tracking-[0.13em] text-[#899987]">01 / The change</p>
                  <p className="text-sm leading-[1.6] text-[#d9dfd6]">{example.change}</p>
                </div>
                <div>
                  <p className="mb-1.5 font-mono text-[10px] uppercase tracking-[0.13em] text-[#899987]">02 / The implication</p>
                  <p className="text-sm leading-[1.6] text-[#d9dfd6]">{example.implication}</p>
                </div>
                <div className="border-l-2 border-[#c5e77d] bg-[#21291f] py-3 pl-4 pr-3">
                  <p className="mb-1.5 font-mono text-[10px] uppercase tracking-[0.13em] text-[#c5e77d]">03 / What to test</p>
                  <p className="text-sm leading-[1.6] text-[#edf0e9]">{example.action}</p>
                </div>
              </div>
              <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-[#39443b] pt-4">
                <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-[#abb9a7]">Primary-source reporting</span>
                <a href={example.url} target="_blank" rel="noopener noreferrer" className="text-xs font-medium text-[#c6e681] underline underline-offset-4 hover:text-white">
                  {example.source} ↗
                </a>
              </div>
              <p className="mt-4 text-[11px] leading-relaxed text-[#879385]">
                Illustrative editorial card using a dated public source. Not a live feed or evidence of an automated GenLens run.
              </p>
            </div>
          </aside>
        </section>

        <section className="border-b border-[#303730] py-16 sm:py-20">
          <div className="grid gap-12 lg:grid-cols-[0.78fr_1.22fr] lg:gap-20">
            <div>
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-[#b5c3af]">THE OPERATING IDEA</p>
              <h2 className="mt-4 max-w-[360px] text-[34px] font-medium leading-[1.14] tracking-[-0.06em] sm:text-[43px]">
                Intelligence that leads somewhere.
              </h2>
            </div>
            <div className="divide-y divide-[#354035] border-t border-[#354035]">
              {[
                ['01', 'Know the signal', 'A consequential change, traced to its actual source. Dated, checked, and separated from speculation.'],
                ['02', 'See the impact', 'What changes in your stack, workflow, cost, control, audience, or risk.'],
                ['03', 'Make a move', 'A practical next decision and a way to tell whether the change improved your work.'],
              ].map((item) => (
                <div key={item[0]} className="grid grid-cols-[42px_1fr] gap-3 py-6 sm:grid-cols-[65px_1fr] sm:gap-6">
                  <span className="pt-1 font-mono text-xs text-[#c5e77d]">{item[0]}</span>
                  <div>
                    <h3 className="text-lg font-semibold tracking-[-0.03em]">{item[1]}</h3>
                    <p className="mt-2 max-w-[540px] text-sm leading-[1.7] text-[#aeb8ac]">{item[2]}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-16 sm:py-20">
          <div className="mb-9 flex items-end justify-between gap-4">
            <div>
              <p className="font-mono text-[10px] tracking-[0.18em] text-[#b5c3af]">TWO SPECIALIST LENSES</p>
              <h2 className="mt-4 text-[32px] font-medium leading-[1.16] tracking-[-0.055em] sm:text-[43px]">Built for working operators.</h2>
            </div>
          </div>
          <div className="grid gap-9 sm:grid-cols-2 sm:gap-12">
            <div className="border-t border-[#627c4b] pt-6">
              <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#c5e77d]">01 / Genny</p>
              <h3 className="mt-3 text-xl font-semibold tracking-[-0.04em]">Creative technology</h3>
              <p className="mt-3 max-w-[460px] text-sm leading-[1.75] text-[#aeb8ac]">
                Models, production workflows, creative APIs, image and video, voice, cost, control, and commercial quality.
              </p>
            </div>
            <div className="border-t border-[#627c4b] pt-6">
              <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#c5e77d]">02 / Marti</p>
              <h3 className="mt-3 text-xl font-semibold tracking-[-0.04em]">Go-to-market engineering</h3>
              <p className="mt-3 max-w-[460px] text-sm leading-[1.75] text-[#aeb8ac]">
                Revenue systems, data, distribution, conversion, marketing automation, analytics, and stack economics.
              </p>
            </div>
          </div>
        </section>

        <footer className="flex flex-col gap-4 border-t border-[#303730] py-7 text-xs text-[#929d90] sm:flex-row sm:items-center sm:justify-between">
          <p><span className="font-semibold text-[#e8ede4]">GenLens.</span> Signal to system.</p>
          <div className="flex flex-wrap gap-5">
            <a href="/auth/invite" className="text-inherit no-underline hover:text-white">Sign in</a>
            <a href="https://github.com/Damnjjwtf/GenLens" target="_blank" rel="noopener noreferrer" className="text-inherit no-underline hover:text-white">GitHub</a>
          </div>
        </footer>
      </div>
    </main>
  )
}
