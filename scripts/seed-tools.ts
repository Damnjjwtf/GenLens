/**
 * scripts/seed-tools.ts
 *
 * Populates the tools table from the canonical TOOLS_MANIFEST.
 * Run once after migration 004:
 *   npx tsx scripts/seed-tools.ts
 *
 * This is the affiliate revenue layer from day one.
 * Every tool record = one affiliate link on a public SEO/GEO page.
 */

import { neon } from '@neondatabase/serverless'

const sql = neon(process.env.DATABASE_URL!)

// Canonical tool registry — sourced from TOOLS_MANIFEST.md
// Add affiliate URLs as you sign up for each program.
// Most programs: Runway, ElevenLabs, HeyGen, Synthesia, Figma have active affiliate/referral programs.
const TOOLS = [
  // ── PRODUCT PHOTOGRAPHY ──────────────────────────────────
  {
    slug: 'keyshot',
    canonical_name: 'KeyShot',
    aliases: ['key shot', 'KeyShot 2026'],
    verticals: ['product_photography'],
    categories: ['3d_rendering', 'visualization'],
    workflow_stages: ['render', 'composite'],
    website_url: 'https://www.keyshot.com',
    affiliate_url: null, // TODO: apply at keyshot.com/partners
    affiliate_program: null,
  },
  {
    slug: 'claid',
    canonical_name: 'Claid AI',
    aliases: ['claid.ai', 'Claid'],
    verticals: ['product_photography'],
    categories: ['image_enhancement', 'background_removal'],
    workflow_stages: ['composite', 'presale'],
    website_url: 'https://claid.ai',
    affiliate_url: null, // TODO: check claid.ai/affiliates
    affiliate_program: null,
  },
  {
    slug: 'figma-weave',
    canonical_name: 'Figma Weave',
    aliases: ['Figma AI', 'figma weave'],
    verticals: ['product_photography'],
    categories: ['design', 'concept'],
    workflow_stages: ['sketch', 'concept'],
    website_url: 'https://figma.com',
    affiliate_url: null, // Figma has a referral program
    affiliate_program: 'Figma Referral',
  },
  {
    slug: 'clo3d',
    canonical_name: 'CLO3D',
    aliases: ['CLO 3D', 'Clo3d'],
    verticals: ['product_photography'],
    categories: ['3d_fashion', 'cloth_simulation'],
    workflow_stages: ['cad', 'render'],
    website_url: 'https://www.clo3d.com',
    affiliate_url: null,
    affiliate_program: null,
  },
  {
    slug: 'photoroom',
    canonical_name: 'PhotoRoom',
    aliases: ['photo room', 'photoroom ai'],
    verticals: ['product_photography'],
    categories: ['background_removal', 'image_editing'],
    workflow_stages: ['composite'],
    website_url: 'https://www.photoroom.com',
    affiliate_url: null, // TODO: check photoroom.com/affiliates
    affiliate_program: null,
  },
  {
    slug: 'flux',
    canonical_name: 'FLUX',
    aliases: ['Black Forest Labs FLUX', 'flux.1', 'FLUX.1'],
    verticals: ['product_photography', 'digital_humans'],
    categories: ['image_generation'],
    workflow_stages: ['concept', 'render'],
    website_url: 'https://bfl.ai',
    affiliate_url: null,
    affiliate_program: null,
  },
  {
    slug: 'adobe-firefly',
    canonical_name: 'Adobe Firefly',
    aliases: ['firefly', 'adobe firefly ai'],
    verticals: ['product_photography', 'filmmaking'],
    categories: ['image_generation', 'generative_fill'],
    workflow_stages: ['concept', 'composite'],
    website_url: 'https://firefly.adobe.com',
    affiliate_url: null, // Adobe has a referral program
    affiliate_program: 'Adobe Referral',
  },
  {
    slug: 'midjourney',
    canonical_name: 'Midjourney',
    aliases: ['mid journey', 'MJ'],
    verticals: ['product_photography', 'digital_humans', 'filmmaking'],
    categories: ['image_generation'],
    workflow_stages: ['concept', 'moodboard'],
    website_url: 'https://midjourney.com',
    affiliate_url: null,
    affiliate_program: null,
  },

  // ── FILMMAKING ───────────────────────────────────────────
  {
    slug: 'runway',
    canonical_name: 'Runway',
    aliases: ['runwayml', 'Runway ML', 'runway gen-3'],
    verticals: ['filmmaking', 'digital_humans'],
    categories: ['video_generation', 'vfx', 'motion'],
    workflow_stages: ['vfx', 'composite', 'scene_comp'],
    website_url: 'https://runwayml.com',
    affiliate_url: 'https://runwayml.com?ref=genlens', // TODO: replace with real affiliate URL
    affiliate_program: 'Runway Affiliate',
    affiliate_commission_pct: 20,
  },
  {
    slug: 'davinci-resolve',
    canonical_name: 'DaVinci Resolve',
    aliases: ['DaVinci', 'resolve', 'davinci resolve studio'],
    verticals: ['filmmaking'],
    categories: ['editing', 'color_grading', 'vfx'],
    workflow_stages: ['color_grade', 'vfx', 'sound_design'],
    website_url: 'https://www.blackmagicdesign.com/products/davinciresolve',
    affiliate_url: null,
    affiliate_program: null,
  },
  {
    slug: 'luma-ai',
    canonical_name: 'Luma AI',
    aliases: ['luma', 'luma dream machine'],
    verticals: ['filmmaking', 'product_photography'],
    categories: ['3d_capture', 'video_generation'],
    workflow_stages: ['vfx', 'render', 'scene_comp'],
    website_url: 'https://lumalabs.ai',
    affiliate_url: null,
    affiliate_program: null,
  },
  {
    slug: 'descript',
    canonical_name: 'Descript',
    aliases: ['descript ai'],
    verticals: ['filmmaking', 'digital_humans'],
    categories: ['editing', 'transcription', 'voice_editing'],
    workflow_stages: ['sound_design', 'voice_gen'],
    website_url: 'https://www.descript.com',
    affiliate_url: null,
    affiliate_program: null,
  },
  {
    slug: 'after-effects',
    canonical_name: 'After Effects',
    aliases: ['AE', 'adobe after effects'],
    verticals: ['filmmaking'],
    categories: ['motion_graphics', 'vfx', 'compositing'],
    workflow_stages: ['vfx', 'composite'],
    website_url: 'https://www.adobe.com/products/aftereffects.html',
    affiliate_url: null,
    affiliate_program: 'Adobe Referral',
  },
  {
    slug: 'unreal-engine',
    canonical_name: 'Unreal Engine',
    aliases: ['unreal', 'UE5', 'Unreal Engine 5'],
    verticals: ['filmmaking'],
    categories: ['real_time_rendering', 'virtual_production'],
    workflow_stages: ['scene_comp', 'vfx', 'render'],
    website_url: 'https://www.unrealengine.com',
    affiliate_url: null,
    affiliate_program: null,
  },
  {
    slug: 'comfyui',
    canonical_name: 'ComfyUI',
    aliases: ['comfy ui', 'comfy'],
    verticals: ['product_photography', 'filmmaking', 'digital_humans'],
    categories: ['workflow_builder', 'image_generation'],
    workflow_stages: ['render', 'concept'],
    website_url: 'https://github.com/Comfy-Org/ComfyUI',
    affiliate_url: null,
    affiliate_program: null,
  },

  // ── DIGITAL HUMANS ───────────────────────────────────────
  {
    slug: 'elevenlabs',
    canonical_name: 'ElevenLabs',
    aliases: ['eleven labs', 'Eleven Labs', '11labs', 'elevenlabs ai'],
    verticals: ['digital_humans', 'filmmaking'],
    categories: ['voice_synthesis', 'text_to_speech', 'voice_cloning'],
    workflow_stages: ['voice_gen', 'sound_design'],
    website_url: 'https://elevenlabs.io',
    affiliate_url: 'https://elevenlabs.io?ref=genlens', // TODO: replace with real affiliate URL
    affiliate_program: 'ElevenLabs Affiliate',
    affiliate_commission_pct: 22,
  },
  {
    slug: 'heygen',
    canonical_name: 'HeyGen',
    aliases: ['hey gen', 'Heygen AI'],
    verticals: ['digital_humans'],
    categories: ['avatar', 'video_generation', 'lip_sync'],
    workflow_stages: ['character_design', 'lip_sync', 'animation'],
    website_url: 'https://www.heygen.com',
    affiliate_url: 'https://www.heygen.com?ref=genlens', // TODO: replace with real affiliate URL
    affiliate_program: 'HeyGen Affiliate',
    affiliate_commission_pct: 25,
  },
  {
    slug: 'synthesia',
    canonical_name: 'Synthesia',
    aliases: ['synthesia ai', 'synthesia.io'],
    verticals: ['digital_humans'],
    categories: ['avatar', 'video_generation', 'multilingual'],
    workflow_stages: ['character_design', 'voice_gen', 'lip_sync'],
    website_url: 'https://www.synthesia.io',
    affiliate_url: 'https://www.synthesia.io?ref=genlens', // TODO: replace with real affiliate URL
    affiliate_program: 'Synthesia Affiliate',
    affiliate_commission_pct: 20,
  },
  {
    slug: 'd-id',
    canonical_name: 'D-ID',
    aliases: ['did', 'D ID', 'did.ai'],
    verticals: ['digital_humans', 'filmmaking'],
    categories: ['avatar', 'animation', 'synthetic_actors'],
    workflow_stages: ['character_design', 'animation', 'lip_sync'],
    website_url: 'https://www.d-id.com',
    affiliate_url: null,
    affiliate_program: null,
  },
  {
    slug: 'stable-diffusion',
    canonical_name: 'Stable Diffusion',
    aliases: ['SD', 'stable diffusion xl', 'SDXL'],
    verticals: ['product_photography', 'digital_humans', 'filmmaking'],
    categories: ['image_generation'],
    workflow_stages: ['concept', 'render'],
    website_url: 'https://stability.ai',
    affiliate_url: null,
    affiliate_program: null,
  },
  {
    slug: 'blender',
    canonical_name: 'Blender',
    aliases: ['blender 3d'],
    verticals: ['product_photography', 'filmmaking'],
    categories: ['3d_modeling', 'animation', 'rendering'],
    workflow_stages: ['cad', 'render', 'animation'],
    website_url: 'https://www.blender.org',
    affiliate_url: null, // Open source, no affiliate
    affiliate_program: null,
  },
]

async function seedTools() {
  console.log(`Seeding ${TOOLS.length} tools...`)
  let inserted = 0
  let updated = 0

  for (const tool of TOOLS) {
    try {
      const existing = await sql`SELECT id FROM tools WHERE slug = ${tool.slug} LIMIT 1`

      if (existing.length === 0) {
        await sql`
          INSERT INTO tools (
            slug, canonical_name, aliases, verticals, categories, workflow_stages,
            website_url, affiliate_url, affiliate_program, affiliate_commission_pct,
            is_public, is_featured
          ) VALUES (
            ${tool.slug},
            ${tool.canonical_name},
            ${tool.aliases},
            ${tool.verticals},
            ${tool.categories || []},
            ${tool.workflow_stages || []},
            ${tool.website_url || null},
            ${tool.affiliate_url || null},
            ${tool.affiliate_program || null},
            ${(tool as { affiliate_commission_pct?: number }).affiliate_commission_pct || null},
            true,
            false
          )
        `
        inserted++
        console.log(`  ✓ Inserted: ${tool.canonical_name}`)
      } else {
        // Update affiliate URL + program if changed
        await sql`
          UPDATE tools SET
            canonical_name = ${tool.canonical_name},
            aliases = ${tool.aliases},
            verticals = ${tool.verticals},
            affiliate_url = ${tool.affiliate_url || null},
            affiliate_program = ${tool.affiliate_program || null},
            updated_at = NOW()
          WHERE slug = ${tool.slug}
        `
        updated++
        console.log(`  → Updated: ${tool.canonical_name}`)
      }
    } catch (err) {
      console.error(`  ✕ Failed: ${tool.canonical_name}`, err)
    }
  }

  console.log(`\nDone. ${inserted} inserted, ${updated} updated.`)
  console.log(`\nTools with affiliate URLs:`)
  TOOLS.filter(t => t.affiliate_url).forEach(t => {
    console.log(`  ${t.canonical_name}: ${t.affiliate_program} (~${(t as { affiliate_commission_pct?: number }).affiliate_commission_pct}% commission)`)
  })
  console.log(`\nTools needing affiliate programs (check their websites):`)
  TOOLS.filter(t => !t.affiliate_url).forEach(t => {
    console.log(`  ${t.canonical_name}: ${t.website_url}`)
  })
}

seedTools().catch(console.error)
