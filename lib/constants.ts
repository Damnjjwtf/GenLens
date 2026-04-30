export const VERTICALS = ['product_photography', 'filmmaking', 'digital_humans'] as const;
export type Vertical = (typeof VERTICALS)[number];

export const VERTICAL_LABELS: Record<Vertical, string> = {
  product_photography: 'Product Photography',
  filmmaking: 'Filmmaking',
  digital_humans: 'Digital Humans',
};

export const VERTICAL_ACCENT: Record<Vertical, string> = {
  product_photography: 'var(--accent)',
  filmmaking: 'var(--accent2)',
  digital_humans: 'var(--purple)',
};

export const DIMENSIONS = [
  { id: 1, label: 'Workflow Stage Signals' },
  { id: 2, label: 'Product Category Deep Dive' },
  { id: 3, label: 'Competitive Intelligence' },
  { id: 4, label: 'Workflow Templates' },
  { id: 5, label: 'Cost & Time Delta' },
  { id: 6, label: 'Regulatory / IP / Ethical' },
  { id: 7, label: 'Talent + Hiring' },
  { id: 8, label: 'Integration + Compatibility' },
  { id: 9, label: 'Cultural / Trend Signals' },
  { id: 10, label: 'Benchmark + Leaderboard' },
] as const;

export const SIGNAL_TYPES = [
  'tool_release', 'competitive_move', 'template', 'benchmark',
  'trend', 'hiring', 'legal', 'integration', 'aesthetic', 'leaderboard',
] as const;

export const WORKFLOW_STAGES = [
  'sketch', 'cad', 'render', 'composite', 'video', 'presale',
  'character_design', 'voice_gen', 'animation', 'lip_sync',
  'scene_comp', 'color_grade', 'concept', 'preproduction',
  'shooting', 'vfx', 'sound_design',
] as const;

export const PRODUCT_CATEGORIES = [
  'hard_goods', 'soft_goods', 'hybrid', 'accessories',
  'commercial_spot', 'music_video', 'short_film', 'feature',
  'documentary', 'educational', 'synthetic_film', 'hybrid_film',
  'talking_head', 'animation_2d', 'animation_3d',
  'deepfake_ethical', 'voiceover',
] as const;

// Model selection — claude-sonnet-4-20250514 is deprecated (Apr 2026).
// Classifier uses Haiku for speed/cost at batch scale; agents use Sonnet.
export const ANTHROPIC_MODEL_CLASSIFIER = 'claude-haiku-4-5-20251001';
export const ANTHROPIC_MODEL_AGENT = 'claude-sonnet-4-6';
// Back-compat alias for any older imports.
export const ANTHROPIC_MODEL = ANTHROPIC_MODEL_CLASSIFIER;

export const INVITE_COOKIE = 'genlens_invite';
export const INVITE_COOKIE_TTL_SECONDS = 60 * 30;

// TOOL TAXONOMY
export const PRICING_TIERS = ['free', 'freemium', 'paid', 'enterprise'] as const;
export type PricingTier = (typeof PRICING_TIERS)[number];

export const TOOL_CATEGORIES = [
  'CAD / 3D Modeling',
  'Rendering',
  'Texturing / Materials',
  'AI Texture Generation',
  'AI Image Generation',
  'Background Generation / Compositing',
  'Background Removal',
  'AI Compositing',
  'Compositing / Motion',
  'Color Grading / Post',
  'Editing / Color Grading',
  'Editing',
  'VFX / Compositing',
  'VFX / Procedural',
  'VFX / Animation',
  'Motion Design',
  'Interactive Motion',
  'Audio / Video Editing',
  'Real-time Rendering / Engine',
  'Video Generation / Synthesis',
  'Video Synthesis',
  'Digital Character',
  'Talking Head Avatar',
  'Video Avatar',
  'Voice Synthesis',
  'Motion Capture',
  'Music Generation',
  'Audio Enhancement',
  'Image Generation',
  'Garment Simulation',
  'Design / Prototyping',
  'Suite',
  'AI Model',
] as const;
export type ToolCategory = (typeof TOOL_CATEGORIES)[number];

// X accounts monitored via web search fallback (not RSS-scraped).
// Twitter API v2 free tier rate limits make direct scraping impractical.
// Verify handles are still active before adding more.
export const MONITORED_X_ACCOUNTS = {
  product_photography: [
    'claid_ai',
    'photoroomapp',
  ],
  filmmaking: [
    'runwayml',
    'wonderdynamics',
    'davinciresolve',
  ],
  digital_humans: [
    'elevenlabsio',
    'heygen_official',
    'descript',
  ],
  practitioners: [
    'karenxcheng',
    'bilawal',
  ],
} as const;
