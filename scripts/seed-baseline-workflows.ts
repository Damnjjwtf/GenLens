#!/usr/bin/env npx tsx

/**
 * Seed baseline workflows for each vertical
 * These anchor the Score formula: (baseline - signal) / baseline = improvement %
 */

import { neon } from '@neondatabase/serverless';

const DATABASE_URL = process.env.DATABASE_URL;
if (!DATABASE_URL) {
  throw new Error('DATABASE_URL is not set');
}

const sql = neon(DATABASE_URL);

const BASELINES = [
  // PRODUCT PHOTOGRAPHY
  {
    vertical: 'product_photography',
    workflow_stage: 'cad',
    product_category: 'hard_goods',
    description: 'CAD modeling for hard goods (pots, cookware, tools)',
    traditional_time_hours: 12,
    traditional_cost_dollars: 800,
    ai_accelerated_time_hours: 8,
    ai_accelerated_cost_dollars: 400,
    baseline_year: 2024,
    source: 'Industry interviews, studio estimates',
  },
  {
    vertical: 'product_photography',
    workflow_stage: 'render',
    product_category: 'hard_goods',
    description: 'Rendering hard goods with photorealistic materials',
    traditional_time_hours: 14,
    traditional_cost_dollars: 1200,
    ai_accelerated_time_hours: 4,
    ai_accelerated_cost_dollars: 100,
    baseline_year: 2024,
    source: 'KeyShot benchmarks, studio feedback',
  },
  {
    vertical: 'product_photography',
    workflow_stage: 'composite',
    product_category: 'hard_goods',
    description: 'Compositing + background generation for product photos',
    traditional_time_hours: 8,
    traditional_cost_dollars: 600,
    ai_accelerated_time_hours: 2,
    ai_accelerated_cost_dollars: 80,
    baseline_year: 2024,
    source: 'Claid AI, Photoshop user estimates',
  },
  {
    vertical: 'product_photography',
    workflow_stage: 'post',
    product_category: 'soft_goods',
    description: 'Color grading + retouching for soft goods (textiles, apparel)',
    traditional_time_hours: 6,
    traditional_cost_dollars: 450,
    ai_accelerated_time_hours: 2,
    ai_accelerated_cost_dollars: 50,
    baseline_year: 2024,
    source: 'Lightroom AI user feedback',
  },
  {
    vertical: 'product_photography',
    workflow_stage: 'presale',
    product_category: 'soft_goods',
    description: 'Full product photography pipeline: shoot to e-commerce',
    traditional_time_hours: 32,
    traditional_cost_dollars: 2500,
    ai_accelerated_time_hours: 12,
    ai_accelerated_cost_dollars: 400,
    baseline_year: 2024,
    source: 'E-commerce studio aggregates',
  },

  // COMMERCIAL FILMMAKING
  {
    vertical: 'filmmaking',
    workflow_stage: 'preproduction',
    product_category: 'commercial_spot',
    description: 'VFX planning + storyboarding for 30s commercial',
    traditional_time_hours: 40,
    traditional_cost_dollars: 3000,
    ai_accelerated_time_hours: 20,
    ai_accelerated_cost_dollars: 1000,
    baseline_year: 2024,
    source: 'Agency estimates, Shotlist usage',
  },
  {
    vertical: 'filmmaking',
    workflow_stage: 'vfx',
    product_category: 'commercial_spot',
    description: 'VFX compositing for 30s commercial (motion graphics + integration)',
    traditional_time_hours: 120,
    traditional_cost_dollars: 12000,
    ai_accelerated_time_hours: 60,
    ai_accelerated_cost_dollars: 5000,
    baseline_year: 2024,
    source: 'Post-production studio feedback, Runway benchmarks',
  },
  {
    vertical: 'filmmaking',
    workflow_stage: 'color_grade',
    product_category: 'commercial_spot',
    description: 'Color grading + finishing for commercial spot',
    traditional_time_hours: 24,
    traditional_cost_dollars: 2000,
    ai_accelerated_time_hours: 12,
    ai_accelerated_cost_dollars: 800,
    baseline_year: 2024,
    source: 'DaVinci Resolve colorist feedback',
  },
  {
    vertical: 'filmmaking',
    workflow_stage: 'sound_design',
    product_category: 'commercial_spot',
    description: 'Sound design + mixing for 30s commercial',
    traditional_time_hours: 16,
    traditional_cost_dollars: 1200,
    ai_accelerated_time_hours: 6,
    ai_accelerated_cost_dollars: 300,
    baseline_year: 2024,
    source: 'Descript speech removal, audio engineering estimates',
  },
  {
    vertical: 'filmmaking',
    workflow_stage: 'shooting',
    product_category: 'music_video',
    description: 'Live action shooting for music video (not AI-accelerated)',
    traditional_time_hours: 16,
    traditional_cost_dollars: 2000,
    ai_accelerated_time_hours: 16,
    ai_accelerated_cost_dollars: 2000,
    baseline_year: 2024,
    source: 'Industry standard (no acceleration)',
  },

  // DIGITAL HUMANS
  {
    vertical: 'digital_humans',
    workflow_stage: 'character_design',
    product_category: 'talking_head',
    description: 'Create digital avatar for talking head video',
    traditional_time_hours: 40,
    traditional_cost_dollars: 3000,
    ai_accelerated_time_hours: 2,
    ai_accelerated_cost_dollars: 200,
    baseline_year: 2024,
    source: 'MetaHuman Creator, D-ID benchmarks',
  },
  {
    vertical: 'digital_humans',
    workflow_stage: 'voice_gen',
    product_category: 'talking_head',
    description: 'Voice synthesis for talking head (emotional prosody, multilingual)',
    traditional_time_hours: 8,
    traditional_cost_dollars: 1200,
    ai_accelerated_time_hours: 0.25,
    ai_accelerated_cost_dollars: 2,
    baseline_year: 2024,
    source: 'ElevenLabs, Synthesia voice estimates',
  },
  {
    vertical: 'digital_humans',
    workflow_stage: 'lip_sync',
    product_category: 'talking_head',
    description: 'Lip-sync generation from audio (speech-driven animation)',
    traditional_time_hours: 24,
    traditional_cost_dollars: 1500,
    ai_accelerated_time_hours: 1,
    ai_accelerated_cost_dollars: 50,
    baseline_year: 2024,
    source: 'Descript auto-sync, Salsa3D benchmarks',
  },
  {
    vertical: 'digital_humans',
    workflow_stage: 'scene_comp',
    product_category: 'animation_3d',
    description: '3D character animation + rendering (full body synthetic actor)',
    traditional_time_hours: 120,
    traditional_cost_dollars: 8000,
    ai_accelerated_time_hours: 40,
    ai_accelerated_cost_dollars: 2000,
    baseline_year: 2024,
    source: 'Unreal MetaHuman, animation studio estimates',
  },
  {
    vertical: 'digital_humans',
    workflow_stage: 'animation',
    product_category: 'animation_3d',
    description: 'Motion capture → animation pipeline (markerless mocap)',
    traditional_time_hours: 80,
    traditional_cost_dollars: 6000,
    ai_accelerated_time_hours: 12,
    ai_accelerated_cost_dollars: 800,
    baseline_year: 2024,
    source: 'Move.ai, Rokoko mocap benchmarks',
  },
];

async function seed() {
  try {
    console.log('🌱 Seeding baseline workflows...');

    for (const baseline of BASELINES) {
      const result = await sql`
        INSERT INTO baseline_workflows (
          vertical,
          workflow_stage,
          product_category,
          description,
          traditional_time_hours,
          traditional_cost_dollars,
          ai_accelerated_time_hours,
          ai_accelerated_cost_dollars,
          baseline_year,
          source
        )
        VALUES (
          ${baseline.vertical},
          ${baseline.workflow_stage},
          ${baseline.product_category},
          ${baseline.description},
          ${baseline.traditional_time_hours},
          ${baseline.traditional_cost_dollars},
          ${baseline.ai_accelerated_time_hours},
          ${baseline.ai_accelerated_cost_dollars},
          ${baseline.baseline_year},
          ${baseline.source}
        )
        RETURNING id, vertical, workflow_stage, product_category;
      `;

      const row = result[0];
      const timeSavings = baseline.traditional_time_hours - baseline.ai_accelerated_time_hours;
      const costSavings = baseline.traditional_cost_dollars - baseline.ai_accelerated_cost_dollars;

      console.log(
        `✓ ${baseline.vertical} → ${baseline.workflow_stage}: ${timeSavings}h saved, $${costSavings} saved`
      );
    }

    console.log(`\n✅ Seeded ${BASELINES.length} baseline workflows`);
    console.log('\nSample calculations:');
    console.log('- Hard goods rendering: 14h → 4h = 71% faster (with KeyShot AI)');
    console.log('- Talking head creation: 40h → 2h = 95% faster (with D-ID)');
    console.log('- Voice synthesis: 8h → 0.25h = 97% faster (with ElevenLabs)');
  } catch (error) {
    console.error('❌ Seed failed:', error);
    process.exit(1);
  }
}

seed();
