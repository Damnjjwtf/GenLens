/**
 * lib/tools/normalize.ts
 *
 * Maps freeform tool names from signals to canonical tool IDs from the tools table.
 * Uses exact matching on aliases + canonical names, with optional fuzzy fallback.
 */

import { neon } from '@neondatabase/serverless'

const sql = neon(process.env.DATABASE_URL!)

export interface ToolMatch {
  tool_id: number
  canonical_name: string
  confidence: 'high' | 'medium' | 'low'
}

let aliasIndex: Map<string, ToolMatch> | null = null

export async function normalizeToolNames(toolNames: string[]): Promise<Map<string, ToolMatch[]>> {
  if (toolNames.length === 0) return new Map()

  const index = await getAliasIndex()
  const result = new Map<string, ToolMatch[]>()

  for (const name of toolNames) {
    const normalized = name.toLowerCase().trim()
    const match = index.get(normalized)

    if (match) {
      result.set(name, [match])
    } else {
      const fuzzy = fuzzyMatch(normalized, index)
      if (fuzzy.length > 0) {
        result.set(name, fuzzy)
      }
    }
  }

  return result
}

export async function resolveToolIds(toolNames: string[]): Promise<number[]> {
  const matches = await normalizeToolNames(toolNames)
  const ids = new Set<number>()

  Array.from(matches.values()).forEach(toolMatches => {
    toolMatches.forEach(match => {
      if (match.confidence === 'high') {
        ids.add(match.tool_id)
      }
    })
  })

  return Array.from(ids).sort((a, b) => a - b)
}

async function getAliasIndex(): Promise<Map<string, ToolMatch>> {
  if (aliasIndex) return aliasIndex

  try {
    const tools = await sql`
      SELECT id, canonical_name, aliases FROM tools WHERE is_public = true
    ` as Array<{ id: number; canonical_name: string; aliases: string[] }>

    const index = new Map<string, ToolMatch>()

    for (const tool of tools) {
      const canonical = tool.canonical_name.toLowerCase()
      index.set(canonical, {
        tool_id: tool.id,
        canonical_name: tool.canonical_name,
        confidence: 'high',
      })

      if (tool.aliases && Array.isArray(tool.aliases)) {
        for (const alias of tool.aliases) {
          const normalized = alias.toLowerCase().trim()
          if (normalized && !index.has(normalized)) {
            index.set(normalized, {
              tool_id: tool.id,
              canonical_name: tool.canonical_name,
              confidence: 'high',
            })
          }
        }
      }
    }

    aliasIndex = index
    return index
  } catch (err) {
    console.error('[normalize] failed to build alias index:', err)
    return new Map()
  }
}

function fuzzyMatch(name: string, index: Map<string, ToolMatch>): ToolMatch[] {
  const candidates: Array<{ match: ToolMatch; score: number }> = []

  Array.from(index.entries()).forEach(([alias, match]) => {
    const score = levenshteinSimilarity(name, alias)
    if (score > 0.75) {
      candidates.push({ match, score })
    }
  })

  if (candidates.length === 0) return []

  candidates.sort((a, b) => b.score - a.score)
  const topScore = candidates[0].score

  return candidates
    .filter(c => c.score === topScore)
    .map(c => ({
      ...c.match,
      confidence: topScore > 0.85 ? 'high' : 'medium',
    }))
}

function levenshteinSimilarity(a: string, b: string): number {
  const distance = levenshteinDistance(a, b)
  const maxLen = Math.max(a.length, b.length)
  if (maxLen === 0) return 1
  return 1 - distance / maxLen
}

function levenshteinDistance(a: string, b: string): number {
  const m = a.length
  const n = b.length
  const dp: number[][] = Array(m + 1)
    .fill(0)
    .map(() => Array(n + 1).fill(0))

  for (let i = 0; i <= m; i++) dp[i][0] = i
  for (let j = 0; j <= n; j++) dp[0][j] = j

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (a[i - 1] === b[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1]
      } else {
        dp[i][j] = 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
      }
    }
  }

  return dp[m][n]
}

export function invalidateCache(): void {
  aliasIndex = null
}
