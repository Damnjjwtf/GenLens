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

async function normalizeToolName(toolName: string): Promise<number | null> {
  if (!toolName) return null;

  const normalized = toolName.toLowerCase().trim();

  // Try alias lookup first
  const aliasResult = await sql`
    SELECT t.id
    FROM tools t
    JOIN tool_aliases ta ON t.id = ta.tool_id
    WHERE LOWER(ta.alias) = ${normalized}
    LIMIT 1
  ` as Array<{ id: number }>;

  if (aliasResult.length > 0) {
    return aliasResult[0].id;
  }

  // Try canonical name
  const canonicalResult = await sql`
    SELECT id
    FROM tools
    WHERE LOWER(canonical_name) = ${normalized}
    LIMIT 1
  ` as Array<{ id: number }>;

  if (canonicalResult.length > 0) {
    return canonicalResult[0].id;
  }

  return null;
}

async function run() {
  try {
    console.log('🔧 Normalizing signal tool names...');

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
        const toolId = await normalizeToolName(toolName);
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
