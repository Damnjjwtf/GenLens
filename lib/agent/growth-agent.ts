/**
 * lib/agent/growth-agent.ts
 *
 * The Growth Agent. Runs after every scrape cycle.
 * Reads today's classified signals → produces social drafts,
 * GEO content blocks, public signal pages, and Index posts.
 * ALL output lands in growth_agent_queue with status=draft.
 * Nothing publishes without human approval.
 */

import { db as sql } from '@/lib/db'
import Anthropic from '@anthropic-ai/sdk'
import { ANTHROPIC_MODEL_AGENT } from '@/lib/constants'

const claude = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY! })

// ─── Types ────────────────────────────────────────────────────

export type OutputType =
  | 'social_x'
  | 'social_linkedin'
  | 'social_discord'
  | 'geo_block'
  | 'index_post'
  | 'signal_page'
  | 'comparison_page'
  | 'template_geo'

interface Signal {
  id: number
  title: string
  description: string
  summary: string
  vertical: string
  dimension: number
  signal_type: string
  tool_names: string[]
  time_saved_hours: number | null
  cost_saved_dollars: number | null
  trending_score: number
  source_url: string
  source_name: string
  created_at: string
}

interface AgentOutput {
  output_type: OutputType
  title: string
  content: string
  target_url?: string
  meta_description?: string
  faq_schema?: object
  signal_ids: number[]
  tool_slug?: string
  vertical?: string
  briefing_date: string
  scheduled_for?: string
}

// ─── Main entry point ─────────────────────────────────────────

export async function runGrowthAgent(runType: 'daily' | 'weekly_index' | 'on_demand' = 'daily') {
  // Log the run start
  const [run] = await sql`
    INSERT INTO agent_runs (run_type, triggered_by, status)
    VALUES (${runType}, 'cron', 'running')
    RETURNING id
  `
  const runId = run.id
  const log: string[] = []
  let signalsProcessed = 0
  let outputsGenerated = 0
  let geoBlocksWritten = 0
  let toolsUpdated = 0

  try {
    const today = new Date().toISOString().split('T')[0]

    // 1. Fetch today's top signals (classified, not yet drafted)
    const signals = await sql`
      SELECT * FROM signals
      WHERE DATE(created_at) = ${today}
        AND status IN ('classified', 'synthesized')
      ORDER BY trending_score DESC, dimension ASC
      LIMIT 40
    ` as Signal[]

    signalsProcessed = signals.length
    log.push(`Loaded ${signals.length} signals for ${today}`)

    if (signals.length === 0) {
      log.push('No signals found — agent exiting early')
      await finalizeRun(runId, 'completed', { signalsProcessed, outputsGenerated, geoBlocksWritten, toolsUpdated, log })
      return { success: true, outputs: 0 }
    }

    const outputs: AgentOutput[] = []

    // 2. Social drafts (X + LinkedIn) — top 3 signals
    const topSignals = signals.slice(0, 3)
    const socialDrafts = await generateSocialDrafts(topSignals, today)
    outputs.push(...socialDrafts)
    outputsGenerated += socialDrafts.length
    log.push(`Generated ${socialDrafts.length} social drafts`)

    // 3. GEO blocks — for each tool mentioned in today's signals
    const toolsInSignals = extractUniqueTools(signals)
    log.push(`Found ${toolsInSignals.length} unique tools in today's signals`)

    for (const toolSlug of toolsInSignals.slice(0, 10)) { // cap at 10 per run
      const toolSignals = signals.filter(s => s.tool_names?.includes(toolSlug))
      if (toolSignals.length === 0) continue

      const geoBlock = await generateGeoBlock(toolSlug, toolSignals, today)
      if (geoBlock) {
        outputs.push(geoBlock)
        geoBlocksWritten++
        outputsGenerated++

        // Also update the tool record's geo content
        await updateToolGeoContent(toolSlug, geoBlock)
        toolsUpdated++
      }
    }
    log.push(`Wrote ${geoBlocksWritten} GEO blocks, updated ${toolsUpdated} tool records`)

    // 4. Comparison pages — if two competing tools appear in same signals
    const comparisons = await detectComparisonOpportunities(signals)
    for (const pair of comparisons.slice(0, 3)) {
      const comparisonOutput = await generateComparisonPage(pair.toolA, pair.toolB, signals, today)
      if (comparisonOutput) {
        outputs.push(comparisonOutput)
        outputsGenerated++
      }
    }
    log.push(`Generated ${comparisons.length} comparison page drafts`)

    // 5. Public signal pages — top 5 signals get shareable URLs
    const signalPages = await generateSignalPages(topSignals.slice(0, 5), today)
    outputs.push(...signalPages)
    outputsGenerated += signalPages.length
    log.push(`Generated ${signalPages.length} signal page drafts`)

    // 6. Weekly Index post (only on Sunday runs, or weekly_index type)
    if (runType === 'weekly_index' || new Date().getDay() === 0) {
      const indexPost = await generateIndexPost(signals, today)
      if (indexPost) {
        outputs.push(indexPost)
        outputsGenerated++
        log.push('Generated weekly Index post')
      }
    }

    // 7. Write all outputs to queue
    for (const output of outputs) {
      await sql`
        INSERT INTO growth_agent_queue (
          output_type, title, content, target_url, meta_description,
          faq_schema, signal_ids, tool_slug, vertical, briefing_date,
          scheduled_for, status, updated_at
        ) VALUES (
          ${output.output_type},
          ${output.title},
          ${output.content},
          ${output.target_url ?? null},
          ${output.meta_description ?? null},
          ${output.faq_schema ? JSON.stringify(output.faq_schema) : null},
          ${output.signal_ids},
          ${output.tool_slug ?? null},
          ${output.vertical ?? null},
          ${output.briefing_date},
          ${output.scheduled_for ?? null},
          'draft',
          NOW()
        )
      `
    }

    log.push(`Wrote ${outputs.length} items to growth_agent_queue`)

    await finalizeRun(runId, 'completed', { signalsProcessed, outputsGenerated, geoBlocksWritten, toolsUpdated, log })
    return { success: true, outputs: outputsGenerated }

  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    log.push(`FATAL ERROR: ${msg}`)
    await finalizeRun(runId, 'failed', { signalsProcessed, outputsGenerated, geoBlocksWritten, toolsUpdated, log }, msg)
    throw err
  }
}

// ─── Output generators ────────────────────────────────────────

async function generateSocialDrafts(signals: Signal[], date: string): Promise<AgentOutput[]> {
  const signalContext = signals.map(s =>
    `SIGNAL [${s.id}] — Vertical: ${s.vertical} | Dimension: ${s.dimension} | Type: ${s.signal_type} | Tools: ${(s.tool_names || []).join(', ')}
Title: ${s.title}
Summary: ${s.summary || s.description}
Time saved: ${s.time_saved_hours ? `${s.time_saved_hours}h` : 'N/A'} | Cost saved: ${s.cost_saved_dollars ? `$${s.cost_saved_dollars}` : 'N/A'}
Source: ${s.source_name}`
  ).join('\n\n')

  const response = await claude.messages.create({
    model: ANTHROPIC_MODEL_AGENT,
    max_tokens: 2400,
    messages: [{
      role: 'user',
      content: `You are the Growth Agent for GenLens — an intelligence platform for creative technologists working in AI-accelerated visual production.

Generate social drafts from today's top signals. All drafts in GenLens's voice: warm, expert, direct. Not corporate. Not academic. Like a smart friend who's also a working creative.

TODAY'S SIGNALS:
${signalContext}

OUTPUT FORMAT — respond with valid JSON only, no markdown:
{
  "x_post": {
    "content": "Post text, max 280 chars. Hook first. Stat if available. End with: Full briefing → genlens.app",
    "signal_ids": [1, 2]
  },
  "linkedin_post": {
    "content": "2-3 short paragraphs. Professional but warm. Same signal, more context. Link to Index or tool page. No hashtag spam — max 3 relevant ones.",
    "signal_ids": [1, 2]
  },
  "discord_posts": [
    {
      "signal_id": 1,
      "title": "Punchy headline. Max 80 chars. Becomes the embed title.",
      "content": "1-3 short paragraphs. Conversational. Channel-native — community is reading, not scrolling. Lead with the stat or change. Add a question at the end to invite reply. Max 1500 chars."
    }
  ]
}

Rules:
- Never hype without a number to back it up
- Declarative headlines. Active voice.
- If there's a time/cost saving, lead with it
- X post must be under 280 chars
- LinkedIn post 150-300 words max
- Discord: one entry per provided signal (preserve the signal_id from input). Discord readers want detail and context, not slogans — give them the so-what
- Add confidence label (high/medium/low) on any specific claim`
    }]
  })

  const text = response.content[0].type === 'text' ? response.content[0].text : ''
  let parsed: {
    x_post: { content: string; signal_ids: number[] }
    linkedin_post: { content: string; signal_ids: number[] }
    discord_posts?: Array<{ signal_id: number; title: string; content: string }>
  }

  try {
    parsed = JSON.parse(text.replace(/```json|```/g, '').trim())
  } catch {
    return [] // Agent parse failure — skip gracefully
  }

  const topSignal = signals[0]
  const outputs: AgentOutput[] = []

  if (parsed.x_post?.content) {
    outputs.push({
      output_type: 'social_x',
      title: `X post — ${date} — ${topSignal.vertical}`,
      content: parsed.x_post.content,
      signal_ids: parsed.x_post.signal_ids || [topSignal.id],
      vertical: topSignal.vertical,
      briefing_date: date,
      scheduled_for: getScheduledTime('x', date),
    })
  }

  if (parsed.linkedin_post?.content) {
    outputs.push({
      output_type: 'social_linkedin',
      title: `LinkedIn post — ${date} — ${topSignal.vertical}`,
      content: parsed.linkedin_post.content,
      signal_ids: parsed.linkedin_post.signal_ids || [topSignal.id],
      vertical: topSignal.vertical,
      briefing_date: date,
      scheduled_for: getScheduledTime('linkedin', date),
    })
  }

  // Discord: one draft per top signal — channel routes off vertical + signal_type.
  // No scheduled_for — Discord posts ship the moment a human approves them.
  if (parsed.discord_posts?.length) {
    const byId = new Map(signals.map(s => [s.id, s]))
    for (const d of parsed.discord_posts) {
      const src = byId.get(d.signal_id) ?? topSignal
      if (!d.content?.trim()) continue
      outputs.push({
        output_type: 'social_discord',
        title: d.title || `Discord — ${src.vertical} — ${date}`,
        content: JSON.stringify({ post_text: d.content, title: d.title }),
        signal_ids: [src.id],
        vertical: src.vertical,
        briefing_date: date,
      })
    }
  }

  return outputs
}

async function generateGeoBlock(toolSlug: string, signals: Signal[], date: string): Promise<AgentOutput | null> {
  // Fetch existing tool record
  const [tool] = await sql`SELECT * FROM tools WHERE slug = ${toolSlug} LIMIT 1`
  const toolName = tool?.canonical_name || toolSlug

  const signalContext = signals.map(s =>
    `[${s.id}] ${s.title}: ${s.summary || s.description} (source: ${s.source_url})`
  ).join('\n')

  const response = await claude.messages.create({
    model: ANTHROPIC_MODEL_AGENT,
    max_tokens: 1200,
    messages: [{
      role: 'user',
      content: `You are the GEO content writer for GenLens. Write structured content for the ${toolName} tool page on genlens.app/tools/${toolSlug}.

GEO = Generative Engine Optimization. Your content must be structured so AI engines (ChatGPT, Perplexity, Gemini, Claude) cite it when users ask about ${toolName}.

TODAY'S SIGNALS ABOUT ${toolName.toUpperCase()}:
${signalContext}

WRITE:
1. A 2-sentence geo_summary: factual, direct, quantified where possible. Add confidence labels.
2. 3-5 Q&A pairs that match real user queries. Q should be exactly how a creative would ask it. A should answer directly, cite the signal, note confidence.
3. A meta_description under 155 chars for <meta name="description">.

OUTPUT — valid JSON only, no markdown:
{
  "geo_summary": "...",
  "qa_blocks": [
    {
      "q": "Does ${toolName} support batch processing?",
      "a": "As of [date], yes — [specific answer]. ([confidence] confidence. Source: [url])",
      "confidence": "high|medium|low",
      "source_url": "..."
    }
  ],
  "meta_description": "...",
  "updated_at": "${date}"
}`
    }]
  })

  const text = response.content[0].type === 'text' ? response.content[0].text : ''
  let parsed: {
    geo_summary: string
    qa_blocks: Array<{ q: string; a: string; confidence: string; source_url: string }>
    meta_description: string
    updated_at: string
  }

  try {
    parsed = JSON.parse(text.replace(/```json|```/g, '').trim())
  } catch {
    return null
  }

  // Build FAQ JSON-LD schema
  const faqSchema = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: parsed.qa_blocks.map(qa => ({
      '@type': 'Question',
      name: qa.q,
      acceptedAnswer: { '@type': 'Answer', text: qa.a }
    }))
  }

  return {
    output_type: 'geo_block',
    title: `GEO block — ${toolName} — ${date}`,
    content: JSON.stringify({ geo_summary: parsed.geo_summary, qa_blocks: parsed.qa_blocks }),
    target_url: `genlens.app/tools/${toolSlug}`,
    meta_description: parsed.meta_description,
    faq_schema: faqSchema,
    signal_ids: signals.map(s => s.id),
    tool_slug: toolSlug,
    briefing_date: date,
  }
}

async function generateSignalPages(signals: Signal[], date: string): Promise<AgentOutput[]> {
  const outputs: AgentOutput[] = []

  for (const signal of signals) {
    const response = await claude.messages.create({
      model: ANTHROPIC_MODEL_AGENT,
      max_tokens: 400,
      messages: [{
        role: 'user',
        content: `Write a public preview for this GenLens signal. It will appear at genlens.app/signals/${signal.id}.

The preview shows: headline, 2-sentence geo_summary, hook_sentence for social sharing.
The action_item is gated behind signup (freemium hook).

SIGNAL:
Title: ${signal.title}
Summary: ${signal.summary || signal.description}
Vertical: ${signal.vertical}
Dimension: ${signal.dimension}
Tools: ${(signal.tool_names || []).join(', ')}
Time saved: ${signal.time_saved_hours ? signal.time_saved_hours + 'h' : 'unknown'}

OUTPUT — valid JSON only:
{
  "geo_summary": "2 sentences. Direct. Quantified. For AI engine citation.",
  "hook_sentence": "One punchy sentence for social sharing. Number first if available. Max 100 chars.",
  "og_headline": "Open graph headline. Max 60 chars. Declarative."
}`
      }]
    })

    const text = response.content[0].type === 'text' ? response.content[0].text : ''
    let parsed: { geo_summary: string; hook_sentence: string; og_headline: string }

    try {
      parsed = JSON.parse(text.replace(/```json|```/g, '').trim())
    } catch {
      continue
    }

    // Also update the signal record with geo content
    await sql`
      UPDATE signals
      SET geo_summary = ${parsed.geo_summary},
          hook_sentence = ${parsed.hook_sentence},
          is_public = true,
          updated_at = NOW()
      WHERE id = ${signal.id}
    `

    outputs.push({
      output_type: 'signal_page',
      title: parsed.og_headline || signal.title,
      content: JSON.stringify(parsed),
      target_url: `genlens.app/signals/${signal.id}`,
      signal_ids: [signal.id],
      vertical: signal.vertical,
      briefing_date: date,
    })
  }

  return outputs
}

async function generateIndexPost(signals: Signal[], date: string): Promise<AgentOutput | null> {
  // Group by vertical, get top tools
  const byVertical: Record<string, Signal[]> = {}
  for (const s of signals) {
    if (!byVertical[s.vertical]) byVertical[s.vertical] = []
    byVertical[s.vertical].push(s)
  }

  const verticalSummaries = Object.entries(byVertical).map(([v, sigs]) => {
    const tools = extractUniqueTools(sigs).slice(0, 5)
    return `${v.toUpperCase()}: Top tools this week — ${tools.join(', ')}`
  }).join('\n')

  const response = await claude.messages.create({
    model: ANTHROPIC_MODEL_AGENT,
    max_tokens: 800,
    messages: [{
      role: 'user',
      content: `You are drafting the weekly GenLens Index post. This publishes every Monday at 8am. It is the public distribution play — designed to be screenshot-shared and quoted by press.

Tone: Bloomberg Terminal meets creative studio. Authoritative, terse, data-first. Not hype.

THIS WEEK'S INTELLIGENCE:
${verticalSummaries}

Total signals processed: ${signals.length}

WRITE:
1. x_post: The Monday Index announcement. Under 280 chars. "GenLens Index — [date]" style. Top mover. Link.
2. email_subject: Subject line for the Monday email. Under 60 chars.
3. index_headline: The big headline for the Index page itself. Under 80 chars.
4. index_lede: 2-sentence lede for the Index page. What mattered this week?

OUTPUT — valid JSON only:
{
  "x_post": "...",
  "email_subject": "...",
  "index_headline": "...",
  "index_lede": "..."
}`
    }]
  })

  const text = response.content[0].type === 'text' ? response.content[0].text : ''
  let parsed: { x_post: string; email_subject: string; index_headline: string; index_lede: string }

  try {
    parsed = JSON.parse(text.replace(/```json|```/g, '').trim())
  } catch {
    return null
  }

  // Schedule for Monday 8am
  const monday = getNextMonday()

  return {
    output_type: 'index_post',
    title: `Weekly Index — ${parsed.index_headline}`,
    content: JSON.stringify(parsed),
    target_url: `genlens.app/index/${date}`,
    signal_ids: signals.map(s => s.id),
    briefing_date: date,
    scheduled_for: monday,
  }
}

async function generateComparisonPage(
  toolA: string,
  toolB: string,
  signals: Signal[],
  date: string
): Promise<AgentOutput | null> {
  const relevantSignals = signals.filter(s =>
    s.tool_names?.includes(toolA) || s.tool_names?.includes(toolB)
  )

  if (relevantSignals.length < 2) return null

  const slug = `${toolA}-vs-${toolB}`

  const response = await claude.messages.create({
    model: ANTHROPIC_MODEL_AGENT,
    max_tokens: 800,
    messages: [{
      role: 'user',
      content: `Write GEO content for a comparison page: genlens.app/compare/${slug}

This page answers "should I use ${toolA} or ${toolB}?" for AI creatives.

SIGNALS:
${relevantSignals.map(s => `[${s.id}] ${s.title}: ${s.summary || s.description}`).join('\n')}

OUTPUT — valid JSON only:
{
  "summary": "2-3 sentence direct comparison. Quantified where possible. No hedging.",
  "qa_blocks": [
    {"q": "Which is better for [use case]?", "a": "Direct answer with evidence.", "confidence": "high|medium|low"},
    {"q": "How do ${toolA} and ${toolB} differ in price?", "a": "...", "confidence": "..."},
    {"q": "Can I use ${toolA} and ${toolB} together?", "a": "...", "confidence": "..."}
  ],
  "meta_description": "Under 155 chars. For <meta name=description>."
}`
    }]
  })

  const text = response.content[0].type === 'text' ? response.content[0].text : ''
  let parsed: {
    summary: string
    qa_blocks: Array<{ q: string; a: string; confidence: string }>
    meta_description: string
  }

  try {
    parsed = JSON.parse(text.replace(/```json|```/g, '').trim())
  } catch {
    return null
  }

  const faqSchema = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: parsed.qa_blocks.map(qa => ({
      '@type': 'Question',
      name: qa.q,
      acceptedAnswer: { '@type': 'Answer', text: qa.a }
    }))
  }

  return {
    output_type: 'comparison_page',
    title: `${toolA} vs ${toolB} — ${date}`,
    content: JSON.stringify(parsed),
    target_url: `genlens.app/compare/${slug}`,
    meta_description: parsed.meta_description,
    faq_schema: faqSchema,
    signal_ids: relevantSignals.map(s => s.id),
    briefing_date: date,
  }
}

// ─── Helpers ─────────────────────────────────────────────────

function extractUniqueTools(signals: Signal[]): string[] {
  const counts: Record<string, number> = {}
  for (const s of signals) {
    for (const tool of s.tool_names || []) {
      counts[tool] = (counts[tool] || 0) + 1
    }
  }
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .map(([tool]) => tool)
}

async function detectComparisonOpportunities(signals: Signal[]): Promise<{ toolA: string; toolB: string }[]> {
  // Find tool pairs that co-appear in signals (competitive context)
  const coAppearances: Record<string, number> = {}
  for (const s of signals) {
    const tools = s.tool_names || []
    for (let i = 0; i < tools.length; i++) {
      for (let j = i + 1; j < tools.length; j++) {
        const key = [tools[i], tools[j]].sort().join('__')
        coAppearances[key] = (coAppearances[key] || 0) + 1
      }
    }
  }
  return Object.entries(coAppearances)
    .filter(([, count]) => count >= 2)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([key]) => {
      const [toolA, toolB] = key.split('__')
      return { toolA, toolB }
    })
}

async function updateToolGeoContent(toolSlug: string, output: AgentOutput): Promise<void> {
  const content = JSON.parse(output.content)
  await sql`
    UPDATE tools SET
      geo_summary = ${content.geo_summary},
      geo_qa_blocks = ${JSON.stringify(content.qa_blocks)},
      faq_schema = ${output.faq_schema ? JSON.stringify(output.faq_schema) : null},
      meta_description = ${output.meta_description ?? null},
      updated_at = NOW()
    WHERE slug = ${toolSlug}
  `
}

async function finalizeRun(
  runId: number,
  status: 'completed' | 'failed',
  stats: { signalsProcessed: number; outputsGenerated: number; geoBlocksWritten: number; toolsUpdated: number; log: string[] },
  errorMessage?: string
): Promise<void> {
  await sql`
    UPDATE agent_runs SET
      status = ${status},
      signals_processed = ${stats.signalsProcessed},
      outputs_generated = ${stats.outputsGenerated},
      geo_blocks_written = ${stats.geoBlocksWritten},
      tools_updated = ${stats.toolsUpdated},
      completed_at = NOW(),
      duration_ms = EXTRACT(EPOCH FROM (NOW() - started_at)) * 1000,
      error_message = ${errorMessage ?? null},
      run_log = ${JSON.stringify(stats.log)}
    WHERE id = ${runId}
  `
}

function getScheduledTime(platform: 'x' | 'linkedin', date: string): string {
  // X: 9am, LinkedIn: 10am next business day
  const d = new Date(date)
  d.setDate(d.getDate() + 1) // next day
  const hour = platform === 'x' ? 9 : 10
  d.setHours(hour, 0, 0, 0)
  return d.toISOString()
}

function getNextMonday(): string {
  const d = new Date()
  const day = d.getDay()
  const daysUntilMonday = day === 0 ? 1 : 8 - day
  d.setDate(d.getDate() + daysUntilMonday)
  d.setHours(8, 0, 0, 0)
  return d.toISOString()
}
