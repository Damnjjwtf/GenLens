import { sql } from './db';

export function canonicalNameToSlug(name: string): string {
  return name.toLowerCase().replace(/\s+/g, '-');
}

export function slugToCanonicalName(tools: Tool[], slug: string): Tool | undefined {
  return tools.find(t => canonicalNameToSlug(t.canonical_name) === slug);
}

export interface Tool {
  id: number;
  canonical_name: string;
  aliases: string[];
  category: string;
  vendor_name: string;
  pricing_tier: string;
  verticals: string[];
  dimensions: number[];
}

/**
 * Normalize a tool name to its canonical form via alias lookup
 */
export async function normalizeTool(rawName: string): Promise<{ id: number; canonical: string } | null> {
  if (!sql) return null;

  const normalized = rawName.toLowerCase().trim();

  // Try exact alias match first
  const result = await sql`
    SELECT t.id, t.canonical_name
    FROM tools t
    JOIN tool_aliases ta ON t.id = ta.tool_id
    WHERE LOWER(ta.alias) = ${normalized}
    LIMIT 1
  ` as Array<{ id: number; canonical_name: string }>;

  if (result.length > 0) {
    return { id: result[0].id, canonical: result[0].canonical_name };
  }

  // Fallback: try canonical name match
  const canonical = await sql`
    SELECT id, canonical_name
    FROM tools
    WHERE LOWER(canonical_name) = ${normalized}
    LIMIT 1
  ` as Array<{ id: number; canonical_name: string }>;

  if (canonical.length > 0) {
    return { id: canonical[0].id, canonical: canonical[0].canonical_name };
  }

  return null;
}

/**
 * Get a tool by ID
 */
export async function getTool(toolId: number): Promise<Tool | null> {
  if (!sql) return null;

  const result = await sql`
    SELECT id, canonical_name, aliases, category, vendor_name, pricing_tier, verticals, dimensions
    FROM tools
    WHERE id = ${toolId}
    LIMIT 1
  ` as Tool[];

  return result[0] || null;
}

/**
 * Get multiple tools by IDs
 */
export async function getTools(toolIds: number[]): Promise<Tool[]> {
  if (!sql || toolIds.length === 0) return [];

  const result = await sql`
    SELECT id, canonical_name, aliases, category, vendor_name, pricing_tier, verticals, dimensions
    FROM tools
    WHERE id = ANY(${toolIds}::int[])
    ORDER BY canonical_name
  ` as Tool[];

  return result;
}

/**
 * Get all tools in a category
 */
export async function getToolsByCategory(category: string): Promise<Tool[]> {
  if (!sql) return [];

  const result = await sql`
    SELECT id, canonical_name, aliases, category, vendor_name, pricing_tier, verticals, dimensions
    FROM tools
    WHERE LOWER(category) LIKE ${`%${category.toLowerCase()}%`}
    ORDER BY canonical_name
  ` as Tool[];

  return result;
}

/**
 * Get all tools for a vertical
 */
export async function getToolsByVertical(vertical: string): Promise<Tool[]> {
  if (!sql) return [];

  const result = await sql`
    SELECT id, canonical_name, aliases, category, vendor_name, pricing_tier, verticals, dimensions
    FROM tools
    WHERE ${vertical} = ANY(verticals)
    ORDER BY canonical_name
  ` as Tool[];

  return result;
}

/**
 * Get all tools (with optional pagination)
 */
export async function getAllTools(limit?: number, offset?: number): Promise<Tool[]> {
  if (!sql) return [];

  const query = limit
    ? sql`SELECT id, canonical_name, aliases, category, vendor_name, pricing_tier, verticals, dimensions FROM tools ORDER BY canonical_name LIMIT ${limit} OFFSET ${offset || 0}`
    : sql`SELECT id, canonical_name, aliases, category, vendor_name, pricing_tier, verticals, dimensions FROM tools ORDER BY canonical_name`;

  const result = await query as Tool[];
  return result;
}

/**
 * Normalize all tool names in a raw signal
 * Returns array of tool IDs
 */
export async function normalizeSignalTools(rawToolNames: string[]): Promise<number[]> {
  const toolIds: number[] = [];

  for (const name of rawToolNames) {
    const normalized = await normalizeTool(name);
    if (normalized) {
      toolIds.push(normalized.id);
    }
  }

  return [...new Set(toolIds)]; // Remove duplicates
}

/**
 * Get tool name for display (prefers canonical name)
 */
export async function getDisplayName(toolId: number): Promise<string | null> {
  const tool = await getTool(toolId);
  return tool?.canonical_name || null;
}
