import { sql } from './db';

export interface BaselineWorkflow {
  id: number;
  vertical: string;
  workflow_stage: string;
  product_category: string;
  traditional_time_hours: number;
  traditional_cost_dollars: number;
  ai_accelerated_time_hours: number;
  ai_accelerated_cost_dollars: number;
}

/**
 * Get baseline workflow for a specific vertical + stage + category
 */
export async function getBaseline(
  vertical: string,
  workflowStage: string,
  productCategory?: string
): Promise<BaselineWorkflow | null> {
  if (!sql) return null;

  const query = productCategory
    ? sql`
      SELECT id, vertical, workflow_stage, product_category,
             traditional_time_hours, traditional_cost_dollars,
             ai_accelerated_time_hours, ai_accelerated_cost_dollars
      FROM baseline_workflows
      WHERE vertical = ${vertical}
        AND workflow_stage = ${workflowStage}
        AND product_category = ${productCategory}
      LIMIT 1
    `
    : sql`
      SELECT id, vertical, workflow_stage, product_category,
             traditional_time_hours, traditional_cost_dollars,
             ai_accelerated_time_hours, ai_accelerated_cost_dollars
      FROM baseline_workflows
      WHERE vertical = ${vertical}
        AND workflow_stage = ${workflowStage}
      LIMIT 1
    `;

  const result = (await query) as BaselineWorkflow[];
  return result[0] || null;
}

/**
 * Calculate improvement percentage from baseline
 * Formula: (baseline - actual) / baseline * 100
 */
export function calculateImprovement(baseline: number, actual: number): number {
  if (baseline === 0) return 0;
  return ((baseline - actual) / baseline) * 100;
}

/**
 * Calculate time savings improvement
 */
export function calculateTimeSavingsImprovement(
  baseline: BaselineWorkflow,
  signalTimeHours: number
): number {
  return calculateImprovement(baseline.traditional_time_hours, signalTimeHours);
}

/**
 * Calculate cost savings improvement
 */
export function calculateCostSavingsImprovement(
  baseline: BaselineWorkflow,
  signalCostDollars: number
): number {
  return calculateImprovement(baseline.traditional_cost_dollars, signalCostDollars);
}

/**
 * Get all baselines for a vertical
 */
export async function getBaselinesByVertical(vertical: string): Promise<BaselineWorkflow[]> {
  if (!sql) return [];

  const result = await sql`
    SELECT id, vertical, workflow_stage, product_category,
           traditional_time_hours, traditional_cost_dollars,
           ai_accelerated_time_hours, ai_accelerated_cost_dollars
    FROM baseline_workflows
    WHERE vertical = ${vertical}
    ORDER BY workflow_stage, product_category
  ` as BaselineWorkflow[];

  return result;
}

/**
 * Snapshot current baselines for historical analysis
 */
export async function snapshotBaselines(): Promise<void> {
  if (!sql) return;

  const today = new Date().toISOString().split('T')[0];

  await sql`
    INSERT INTO baseline_snapshots (
      baseline_id, vertical, workflow_stage,
      traditional_time_hours, traditional_cost_dollars, snapshot_date
    )
    SELECT id, vertical, workflow_stage,
           traditional_time_hours, traditional_cost_dollars,
           ${today}::date
    FROM baseline_workflows
    ON CONFLICT DO NOTHING
  `;
}
