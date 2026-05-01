import { neon, Pool } from '@neondatabase/serverless';

const connectionString = process.env.DATABASE_URL;

export const sql = connectionString ? neon(connectionString) : null;

export const pool: Pool | null = connectionString
  ? new Pool({ connectionString })
  : null;

function requireSql() {
  if (!sql) throw new Error('DATABASE_URL is not set');
  return sql;
}

export type UserPreferences = {
  user_id: string;
  active_verticals: string[];
  workflow_stage_focus: string[] | null;
  product_categories_focus: string[] | null;
  tools_tracking: string[] | null;
  competitors_watching: string[] | null;
  delivery_frequency: string;
  delivery_time: string;
  delivery_timezone: string;
  output_formats: string[];
  dimensions_visible: number[];
};

export async function getUserPreferences(userId: string): Promise<UserPreferences | null> {
  const rows = (await requireSql()`
    SELECT user_id, active_verticals, workflow_stage_focus, product_categories_focus,
           tools_tracking, competitors_watching, delivery_frequency,
           delivery_time::text AS delivery_time, delivery_timezone,
           output_formats, dimensions_visible
    FROM user_preferences WHERE user_id = ${userId}::uuid LIMIT 1
  `) as UserPreferences[];
  return rows[0] ?? null;
}

export async function upsertUserPreferences(
  userId: string,
  prefs: Partial<UserPreferences>,
): Promise<void> {
  const existing = await getUserPreferences(userId);
  if (!existing) {
    await requireSql()`
      INSERT INTO user_preferences (user_id, active_verticals, delivery_frequency, output_formats, dimensions_visible)
      VALUES (
        ${userId}::uuid,
        ${prefs.active_verticals ?? ['product_photography', 'filmmaking', 'digital_humans']},
        ${prefs.delivery_frequency ?? 'daily'},
        ${prefs.output_formats ?? ['email', 'dashboard']},
        ${prefs.dimensions_visible ?? [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}
      )
    `;
    return;
  }
  await requireSql()`
    UPDATE user_preferences SET
      active_verticals = COALESCE(${prefs.active_verticals ?? null}::text[], active_verticals),
      workflow_stage_focus = COALESCE(${prefs.workflow_stage_focus ?? null}::text[], workflow_stage_focus),
      product_categories_focus = COALESCE(${prefs.product_categories_focus ?? null}::text[], product_categories_focus),
      tools_tracking = COALESCE(${prefs.tools_tracking ?? null}::text[], tools_tracking),
      competitors_watching = COALESCE(${prefs.competitors_watching ?? null}::text[], competitors_watching),
      delivery_frequency = COALESCE(${prefs.delivery_frequency ?? null}, delivery_frequency),
      delivery_timezone = COALESCE(${prefs.delivery_timezone ?? null}, delivery_timezone),
      output_formats = COALESCE(${prefs.output_formats ?? null}::text[], output_formats),
      dimensions_visible = COALESCE(${prefs.dimensions_visible ?? null}::int[], dimensions_visible),
      updated_at = NOW()
    WHERE user_id = ${userId}::uuid
  `;
}
