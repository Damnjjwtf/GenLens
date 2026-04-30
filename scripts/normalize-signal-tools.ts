#!/usr/bin/env npx tsx

/**
 * Batch normalize tool names in signals to canonical tool IDs
 * Scans all signals with raw tool_names, looks up canonical IDs,
 * and populates tool_ids column
 */

import { neon } from '@neondatabase/serverless';

const DATABASE_URL = process.env.DATABASE_URL;
if (!DATABASE_URL) {
  throw new Error('DATABASE_URL is not set');
}

const sql = neon(DATABASE_URL);

async function buildLookupMap(): Promise<Map<string, number>> {
  const map = new Map<string, number>();

  // Load all tools and aliases into memory
  const tools = await sql`
    SELECT id, canonical_name
    FROM tools
  ` as Array<{ id: number; canonical_name: string }>;

  const aliases = await sql`
    SELECT alias, tool_id
    FROM tool_aliases
  ` as Array<{ alias: string; tool_id: number }>;

  // Index canonical names
  for (const tool of tools) {
    map.set(tool.canonical_name.toLowerCase(), tool.id);
  }

  // Index aliases
  for (const alias of aliases) {
    map.set(alias.toLowerCase(), alias.tool_id);
  }

  return map;
}

function normalizeToolName(toolName: string, lookupMap: Map<string, number>): number | null {
  if (!toolName) return null;
  const normalized = toolName.toLowerCase().trim();
  return lookupMap.get(normalized) || null;
}

async function run() {
  try {
    console.log('🔧 Normalizing signal tool names...');

    // Build in-memory lookup map
    console.log('📚 Loading tools and aliases into memory...');
    const lookupMap = await buildLookupMap();
    console.log(`Loaded ${lookupMap.size} tool entries`);

    // Get all signals with tool_names but no tool_ids
    const signals = await sql`
      SELECT id, tool_names
      FROM signals
      WHERE tool_names IS NOT NULL
        AND tool_names != '{}'::text[]
        AND (tool_ids IS NULL OR tool_ids = '{}'::int[])
      LIMIT 1000
    ` as Array<{ id: number; tool_names: string[] }>;

    console.log(`Found ${signals.length} signals to normalize`);

    let normalized = 0;
    let skipped = 0;

    for (const signal of signals) {
      const toolIds: number[] = [];

      for (const toolName of signal.tool_names) {
        const toolId = normalizeToolName(toolName, lookupMap);
        if (toolId) {
          toolIds.push(toolId);
        }
      }

      if (toolIds.length > 0) {
        // Deduplicate
        const uniqueIds = [...new Set(toolIds)];

        // Update signal
        await sql`
          UPDATE signals
          SET tool_ids = ${uniqueIds}
          WHERE id = ${signal.id}
        `;

        normalized++;
        console.log(`✓ Signal ${signal.id}: ${signal.tool_names.join(', ')} → [${uniqueIds.join(', ')}]`);
      } else {
        skipped++;
        console.log(`✗ Signal ${signal.id}: No tools matched for ${signal.tool_names.join(', ')}`);
      }
    }

    console.log(`\n✅ Normalization complete: ${normalized} updated, ${skipped} skipped`);
  } catch (error) {
    console.error('❌ Normalization failed:', error);
    process.exit(1);
  }
}

run();
