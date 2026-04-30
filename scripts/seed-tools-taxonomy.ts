#!/usr/bin/env npx tsx

import { neon } from '@neondatabase/serverless';

const DATABASE_URL = process.env.DATABASE_URL;
if (!DATABASE_URL) {
  throw new Error('DATABASE_URL is not set');
}

const sql = neon(DATABASE_URL);

// Define all tools with canonical names, aliases, and metadata
const TOOLS = [
  // PRODUCT PHOTOGRAPHY - CAD
  {
    canonical: 'Figma Weave',
    aliases: ['figma weave', 'figma-weave', 'weave'],
    vendor: 'Figma',
    category: 'CAD / 3D Mockup',
    pricing: 'freemium',
    verticals: ['product_photography'],
    dimensions: [1, 4, 8],
  },
  {
    canonical: 'Fusion 360',
    aliases: ['fusion 360', 'fusion360', 'autodesk fusion'],
    vendor: 'Autodesk',
    category: 'CAD / 3D Modeling',
    pricing: 'freemium',
    verticals: ['product_photography'],
    dimensions: [1, 8],
  },
  {
    canonical: 'Solidworks',
    aliases: ['solidworks', 'sw'],
    vendor: 'Dassault Systèmes',
    category: 'CAD / 3D Modeling',
    pricing: 'paid',
    verticals: ['product_photography'],
    dimensions: [1, 8],
  },
  {
    canonical: 'Blender',
    aliases: ['blender', 'blender3d'],
    vendor: 'Blender Foundation',
    category: 'CAD / 3D Modeling / Rendering',
    pricing: 'free',
    verticals: ['product_photography', 'filmmaking', 'digital_humans'],
    dimensions: [1, 8],
  },
  {
    canonical: 'Rhino',
    aliases: ['rhino', 'rhinoceros', 'rhino 7'],
    vendor: 'Robert McNeel & Associates',
    category: 'CAD / 3D Modeling',
    pricing: 'paid',
    verticals: ['product_photography'],
    dimensions: [1, 8],
  },

  // PRODUCT PHOTOGRAPHY - RENDERING
  {
    canonical: 'KeyShot',
    aliases: ['keyshot', 'key shot', 'keyshot 2026', 'keyshot2026'],
    vendor: 'Luxion',
    category: 'Rendering',
    pricing: 'paid',
    verticals: ['product_photography'],
    dimensions: [1, 5],
  },
  {
    canonical: 'Octane Render',
    aliases: ['octane', 'octane render', 'otoy octane'],
    vendor: 'OTOY',
    category: 'Rendering',
    pricing: 'paid',
    verticals: ['product_photography', 'filmmaking'],
    dimensions: [1, 5],
  },
  {
    canonical: 'V-Ray',
    aliases: ['vray', 'v-ray', 'chaos vray'],
    vendor: 'Chaos',
    category: 'Rendering',
    pricing: 'paid',
    verticals: ['product_photography', 'filmmaking'],
    dimensions: [1, 5],
  },
  {
    canonical: 'Arnold',
    aliases: ['arnold', 'arnold renderer', 'solidangle arnold'],
    vendor: 'Solid Angle / Autodesk',
    category: 'Rendering',
    pricing: 'paid',
    verticals: ['product_photography', 'filmmaking'],
    dimensions: [1, 5],
  },
  {
    canonical: 'Redshift',
    aliases: ['redshift', 'redshift renderer', 'maxon redshift'],
    vendor: 'Maxon',
    category: 'Rendering',
    pricing: 'paid',
    verticals: ['product_photography', 'filmmaking'],
    dimensions: [1, 5],
  },

  // PRODUCT PHOTOGRAPHY - TEXTURING
  {
    canonical: 'Substance 3D',
    aliases: ['substance 3d', 'substance designer', 'adobe substance'],
    vendor: 'Adobe',
    category: 'Texturing / Materials',
    pricing: 'freemium',
    verticals: ['product_photography', 'filmmaking'],
    dimensions: [1, 2, 8],
  },
  {
    canonical: 'Adobe Firefly',
    aliases: ['firefly', 'adobe firefly', 'firefly ai'],
    vendor: 'Adobe',
    category: 'AI Texture Generation',
    pricing: 'freemium',
    verticals: ['product_photography'],
    dimensions: [1, 5],
  },
  {
    canonical: 'Stable Diffusion XL',
    aliases: ['stable diffusion', 'sdxl', 'stable diffusion xl'],
    vendor: 'Stability AI',
    category: 'AI Image Generation',
    pricing: 'free',
    verticals: ['product_photography', 'filmmaking', 'digital_humans'],
    dimensions: [1, 5],
  },

  // PRODUCT PHOTOGRAPHY - BACKGROUND / COMPOSITING
  {
    canonical: 'Claid AI',
    aliases: ['claid', 'claid.ai', 'claid ai'],
    vendor: 'Claid',
    category: 'Background Generation / Compositing',
    pricing: 'freemium',
    verticals: ['product_photography'],
    dimensions: [1, 2, 5],
  },
  {
    canonical: 'Remove.bg',
    aliases: ['remove.bg', 'removebg', 'remove bg'],
    vendor: 'Remove.bg',
    category: 'Background Removal',
    pricing: 'freemium',
    verticals: ['product_photography'],
    dimensions: [1, 5],
  },
  {
    canonical: 'Photoshop Generative Fill',
    aliases: ['photoshop generative fill', 'photoshop firefly', 'generative fill'],
    vendor: 'Adobe',
    category: 'AI Compositing',
    pricing: 'paid',
    verticals: ['product_photography'],
    dimensions: [1, 5],
  },
  {
    canonical: 'After Effects',
    aliases: ['after effects', 'ae', 'adobe after effects'],
    vendor: 'Adobe',
    category: 'Compositing / Motion',
    pricing: 'paid',
    verticals: ['filmmaking'],
    dimensions: [1, 8],
  },

  // PRODUCT PHOTOGRAPHY - COLOR GRADING
  {
    canonical: 'Lightroom',
    aliases: ['lightroom', 'adobe lightroom', 'lr'],
    vendor: 'Adobe',
    category: 'Color Grading / Post',
    pricing: 'freemium',
    verticals: ['product_photography'],
    dimensions: [1, 5],
  },
  {
    canonical: 'Capture One',
    aliases: ['capture one', 'captureone'],
    vendor: 'Phase One',
    category: 'Color Grading / Post',
    pricing: 'paid',
    verticals: ['product_photography'],
    dimensions: [1, 5],
  },

  // FILMMAKING - EDITING
  {
    canonical: 'DaVinci Resolve',
    aliases: ['davinci resolve', 'davinci', 'resolve', 'dci davinci'],
    vendor: 'Blackmagic Design',
    category: 'Editing / Color Grading',
    pricing: 'freemium',
    verticals: ['filmmaking'],
    dimensions: [1, 5, 8],
  },
  {
    canonical: 'Premiere Pro',
    aliases: ['premiere pro', 'premiere', 'ppro', 'adobe premiere'],
    vendor: 'Adobe',
    category: 'Editing',
    pricing: 'paid',
    verticals: ['filmmaking'],
    dimensions: [1, 8],
  },
  {
    canonical: 'Final Cut Pro',
    aliases: ['final cut pro', 'fcp', 'final cut'],
    vendor: 'Apple',
    category: 'Editing',
    pricing: 'paid',
    verticals: ['filmmaking'],
    dimensions: [1, 8],
  },

  // FILMMAKING - VFX / COMPOSITING
  {
    canonical: 'Nuke',
    aliases: ['nuke', 'nukex', 'foundry nuke'],
    vendor: 'Foundry',
    category: 'VFX / Compositing',
    pricing: 'paid',
    verticals: ['filmmaking'],
    dimensions: [1, 8],
  },
  {
    canonical: 'Houdini',
    aliases: ['houdini', 'sesiware houdini'],
    vendor: 'SideFX',
    category: 'VFX / Procedural',
    pricing: 'paid',
    verticals: ['filmmaking'],
    dimensions: [1, 8],
  },
  {
    canonical: 'Maya',
    aliases: ['maya', 'autodesk maya'],
    vendor: 'Autodesk',
    category: 'VFX / Animation',
    pricing: 'paid',
    verticals: ['filmmaking', 'digital_humans'],
    dimensions: [1, 8],
  },

  // FILMMAKING - MOTION DESIGN
  {
    canonical: 'Cavalry',
    aliases: ['cavalry', 'cavalry.app'],
    vendor: 'Cavalry',
    category: 'Motion Design',
    pricing: 'paid',
    verticals: ['filmmaking'],
    dimensions: [1, 4],
  },
  {
    canonical: 'Rive',
    aliases: ['rive', 'rive.app'],
    vendor: 'Rive',
    category: 'Interactive Motion',
    pricing: 'freemium',
    verticals: ['filmmaking'],
    dimensions: [1, 4, 8],
  },

  // FILMMAKING - SOUND DESIGN
  {
    canonical: 'Descript',
    aliases: ['descript', 'overdub'],
    vendor: 'Descript',
    category: 'Audio / Video Editing',
    pricing: 'freemium',
    verticals: ['filmmaking', 'digital_humans'],
    dimensions: [1, 5, 8],
  },

  // FILMMAKING - RENDERING / VIDEO GEN
  {
    canonical: 'Unreal Engine 5',
    aliases: ['unreal engine 5', 'ue5', 'unreal', 'nanite', 'lumen'],
    vendor: 'Epic Games',
    category: 'Real-time Rendering / Engine',
    pricing: 'freemium',
    verticals: ['filmmaking', 'digital_humans'],
    dimensions: [1, 8],
  },
  {
    canonical: 'Runway Gen-3',
    aliases: ['runway', 'runway gen-3', 'runway ml', 'runwayml'],
    vendor: 'Runway',
    category: 'Video Generation / Synthesis',
    pricing: 'freemium',
    verticals: ['filmmaking', 'digital_humans'],
    dimensions: [1, 5],
  },
  {
    canonical: 'Luma AI',
    aliases: ['luma ai', 'lumalabs', 'luma'],
    vendor: 'Luma AI',
    category: 'Video Synthesis',
    pricing: 'freemium',
    verticals: ['filmmaking'],
    dimensions: [1, 5],
  },
  {
    canonical: 'Sora',
    aliases: ['sora', 'openai sora'],
    vendor: 'OpenAI',
    category: 'Video Generation',
    pricing: 'paid',
    verticals: ['filmmaking'],
    dimensions: [1, 5],
  },

  // DIGITAL HUMANS - CHARACTER DESIGN
  {
    canonical: 'MetaHuman Creator',
    aliases: ['metahuman', 'metahuman creator', 'unreal metahuman'],
    vendor: 'Epic Games',
    category: 'Digital Character',
    pricing: 'free',
    verticals: ['digital_humans'],
    dimensions: [1, 2],
  },
  {
    canonical: 'D-ID',
    aliases: ['d-id', 'did.ai', 'deid', 'd-id studio'],
    vendor: 'D-ID',
    category: 'Talking Head Avatar',
    pricing: 'freemium',
    verticals: ['digital_humans'],
    dimensions: [1, 2, 5],
  },
  {
    canonical: 'Synthesia',
    aliases: ['synthesia', 'synthesia.io'],
    vendor: 'Synthesia',
    category: 'Video Avatar',
    pricing: 'freemium',
    verticals: ['digital_humans'],
    dimensions: [1, 2, 5],
  },
  {
    canonical: 'HeyGen',
    aliases: ['heygen', 'hey gen'],
    vendor: 'HeyGen',
    category: 'Video Avatar',
    pricing: 'freemium',
    verticals: ['digital_humans'],
    dimensions: [1, 2, 5],
  },

  // DIGITAL HUMANS - VOICE
  {
    canonical: 'ElevenLabs',
    aliases: ['elevenlabs', 'eleven labs', 'el', 'elevenlabs.io'],
    vendor: 'ElevenLabs',
    category: 'Voice Synthesis',
    pricing: 'freemium',
    verticals: ['digital_humans', 'filmmaking'],
    dimensions: [1, 5, 7],
  },
  {
    canonical: 'Resemble AI',
    aliases: ['resemble ai', 'resemble', 'resemble.ai'],
    vendor: 'Resemble AI',
    category: 'Voice Synthesis',
    pricing: 'freemium',
    verticals: ['digital_humans'],
    dimensions: [1, 5],
  },

  // DIGITAL HUMANS - ANIMATION / MOCAP
  {
    canonical: 'Move.ai',
    aliases: ['move.ai', 'moveai', 'move ai'],
    vendor: 'Move.ai',
    category: 'Motion Capture',
    pricing: 'freemium',
    verticals: ['digital_humans', 'filmmaking'],
    dimensions: [1, 2, 5],
  },
  {
    canonical: 'Rokoko',
    aliases: ['rokoko', 'rokoko studio'],
    vendor: 'Rokoko',
    category: 'Motion Capture',
    pricing: 'freemium',
    verticals: ['digital_humans'],
    dimensions: [1, 2, 5],
  },

  // MUSIC / AUDIO
  {
    canonical: 'Suno AI',
    aliases: ['suno', 'suno.ai', 'suno ai'],
    vendor: 'Suno',
    category: 'Music Generation',
    pricing: 'freemium',
    verticals: ['product_photography', 'filmmaking'],
    dimensions: [1, 5],
  },
  {
    canonical: 'Udio',
    aliases: ['udio', 'udio.com'],
    vendor: 'Udio',
    category: 'Music Generation',
    pricing: 'freemium',
    verticals: ['filmmaking'],
    dimensions: [1, 5],
  },
  {
    canonical: 'iZotope RX',
    aliases: ['izotope rx', 'izotope', 'rx'],
    vendor: 'iZotope',
    category: 'Audio Enhancement',
    pricing: 'paid',
    verticals: ['filmmaking'],
    dimensions: [1, 5, 8],
  },

  // IMAGE GENERATION / DESIGN
  {
    canonical: 'Midjourney',
    aliases: ['midjourney', 'mj'],
    vendor: 'Midjourney',
    category: 'Image Generation',
    pricing: 'paid',
    verticals: ['product_photography', 'filmmaking'],
    dimensions: [1, 5, 9],
  },
  {
    canonical: 'DALL-E 3',
    aliases: ['dalle', 'dall-e', 'dall-e 3', 'openai dalle'],
    vendor: 'OpenAI',
    category: 'Image Generation',
    pricing: 'paid',
    verticals: ['product_photography', 'filmmaking'],
    dimensions: [1, 5],
  },

  // FASHION / APPAREL
  {
    canonical: 'CLO 3D',
    aliases: ['clo3d', 'clo 3d'],
    vendor: 'CLO',
    category: 'Garment Simulation',
    pricing: 'paid',
    verticals: ['product_photography'],
    dimensions: [1, 2, 5],
  },
  {
    canonical: 'Marvelous Designer',
    aliases: ['marvelous designer', 'marvelous', 'md'],
    vendor: 'Marvelous Software',
    category: 'Garment Simulation',
    pricing: 'paid',
    verticals: ['product_photography'],
    dimensions: [1, 2, 5],
  },

  // GENERIC / CROSS-VERTICAL
  {
    canonical: 'Figma',
    aliases: ['figma', 'figma.com'],
    vendor: 'Figma',
    category: 'Design / Prototyping',
    pricing: 'freemium',
    verticals: ['product_photography', 'filmmaking'],
    dimensions: [1, 4, 8],
  },
  {
    canonical: 'Adobe Creative Cloud',
    aliases: ['adobe cc', 'adobe', 'creative cloud'],
    vendor: 'Adobe',
    category: 'Suite',
    pricing: 'paid',
    verticals: ['product_photography', 'filmmaking', 'digital_humans'],
    dimensions: [1, 8],
  },
  {
    canonical: 'Anthropic Claude',
    aliases: ['claude', 'claude api', 'anthropic'],
    vendor: 'Anthropic',
    category: 'AI Model',
    pricing: 'freemium',
    verticals: ['product_photography', 'filmmaking', 'digital_humans'],
    dimensions: [1, 5],
  },
] as const;

async function seed() {
  try {
    console.log('🌱 Seeding tool taxonomy...');

    // Batch insert tools
    const toolResults = await sql`
      INSERT INTO tools (canonical_name, aliases, category, vendor_name, pricing_tier, verticals, dimensions)
      VALUES
      ${sql(
        TOOLS.map(t => [
          t.canonical,
          t.aliases,
          t.category,
          t.vendor,
          t.pricing,
          t.verticals,
          t.dimensions,
        ])
      )}
      ON CONFLICT (canonical_name) DO UPDATE SET
        aliases = EXCLUDED.aliases,
        updated_at = NOW()
      RETURNING id, canonical_name;
    `;

    // Log inserted tools
    for (const result of toolResults) {
      console.log(`✓ ${result.canonical_name} (ID: ${result.id})`);
    }

    // Build aliases list with tool IDs
    const aliases: Array<[string, number]> = [];
    for (let i = 0; i < TOOLS.length; i++) {
      const tool = TOOLS[i];
      const toolId = toolResults[i].id;
      for (const alias of tool.aliases) {
        aliases.push([alias, toolId]);
      }
    }

    // Batch insert aliases
    if (aliases.length > 0) {
      await sql`
        INSERT INTO tool_aliases (alias, tool_id)
        VALUES
        ${sql(aliases)}
        ON CONFLICT (alias) DO UPDATE SET tool_id = EXCLUDED.tool_id;
      `;
    }

    const totalAliases = TOOLS.reduce((sum, t) => sum + t.aliases.length, 0);
    console.log(`\n✅ Seeded ${TOOLS.length} tools with ${totalAliases} aliases`);
  } catch (error) {
    console.error('❌ Seed failed:', error);
    process.exit(1);
  }
}

seed();
