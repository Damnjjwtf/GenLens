/**
 * lib/scraper/sources.ts
 *
 * Active source registry for the GenLens scraper.
 * Verticals currently active: product_photography, filmmaking, digital_humans.
 * Deferred verticals (motion_graphics, fashion, music_production) live in sources-deferred.ts.
 *
 * Source URLs MUST be verified before first deploy. Spot-check 10–15 randomly.
 * High-risk URLs to verify first:
 *   - YouTube channel IDs (Corridor Crew especially)
 *   - Substack /feed paths (Latent Space, Bilawal Sidhu)
 *   - Trade press RSS paths (/feed/ vs /rss/ vs /feed/rss/ varies)
 *   - arXiv format (https://arxiv.org/rss/cs.GR not /list/)
 */

export type SourceType =
  | 'rss'        // RSS/Atom — covers blogs, Reddit, GitHub, YouTube, arXiv, Substacks
  | 'html'       // Direct HTML scrape (no feed available)
  | 'discord'    // Manual / invite-required (not scraped)
  | 'conference' // Annual / irregular HTML scrape

export type Vertical =
  | 'product_photography'
  | 'filmmaking'
  | 'digital_humans'
  | 'motion_graphics'
  | 'fashion'
  | 'music_production'

export interface Source {
  name: string
  url: string
  type: SourceType
  verticals: Vertical[]
  dimensions: number[]      // 1–10, see lib/constants.ts DIMENSIONS
  scrape_interval: number   // hours between scrapes
  notes?: string
}

// ─── Tool blogs + vendor feeds ────────────────────────────────

const TOOL_BLOGS: Source[] = [
  { name: 'KeyShot Blog', url: 'https://www.keyshot.com/blog/feed/', type: 'rss', verticals: ['product_photography'], dimensions: [1, 2, 5], scrape_interval: 24 },
  { name: 'Adobe Blog', url: 'https://blog.adobe.com/en/publish/rss', type: 'rss', verticals: ['product_photography', 'filmmaking'], dimensions: [1, 5, 8], scrape_interval: 24 },
  { name: 'Figma Blog', url: 'https://www.figma.com/blog/rss.xml', type: 'rss', verticals: ['product_photography'], dimensions: [1, 4, 8], scrape_interval: 24 },
  { name: 'Runway Blog', url: 'https://runwayml.com/blog/feed/', type: 'rss', verticals: ['filmmaking', 'digital_humans'], dimensions: [1, 5], scrape_interval: 24 },
  { name: 'ElevenLabs Blog', url: 'https://elevenlabs.io/blog/rss.xml', type: 'rss', verticals: ['digital_humans', 'filmmaking'], dimensions: [1, 2, 5, 7], scrape_interval: 24 },
  { name: 'HeyGen Blog', url: 'https://www.heygen.com/blog/rss.xml', type: 'rss', verticals: ['digital_humans'], dimensions: [1, 5], scrape_interval: 24 },
  { name: 'Synthesia Blog', url: 'https://www.synthesia.io/blog/rss.xml', type: 'rss', verticals: ['digital_humans'], dimensions: [1, 2, 5, 7], scrape_interval: 24 },
  { name: 'D-ID Blog', url: 'https://www.d-id.com/blog/rss.xml', type: 'rss', verticals: ['digital_humans', 'filmmaking'], dimensions: [1, 2, 5], scrape_interval: 24 },
  { name: 'Move.ai Blog', url: 'https://www.move.ai/blog', type: 'html', verticals: ['digital_humans', 'filmmaking'], dimensions: [1, 5], scrape_interval: 48 },
  { name: 'Luma AI Blog', url: 'https://lumalabs.ai/blog', type: 'html', verticals: ['filmmaking', 'product_photography'], dimensions: [1, 5], scrape_interval: 24 },
  { name: 'Descript Blog', url: 'https://www.descript.com/blog/rss.xml', type: 'rss', verticals: ['filmmaking', 'digital_humans'], dimensions: [1, 5, 8], scrape_interval: 24 },
  { name: 'Black Forest Labs / FLUX', url: 'https://bfl.ai/blog', type: 'html', verticals: ['product_photography', 'digital_humans'], dimensions: [1, 5], scrape_interval: 48 },
  { name: 'fal.ai Blog', url: 'https://fal.ai/blog', type: 'html', verticals: ['product_photography', 'filmmaking', 'digital_humans'], dimensions: [1, 8], scrape_interval: 24 },
  { name: 'Beeble AI Blog', url: 'https://beeble.ai/blog', type: 'html', verticals: ['product_photography', 'filmmaking'], dimensions: [1, 5], scrape_interval: 48 },
  { name: 'OpenAI Blog', url: 'https://openai.com/blog/rss.xml', type: 'rss', verticals: ['filmmaking', 'digital_humans'], dimensions: [1, 5, 6], scrape_interval: 24 },
  { name: 'Google AI Blog', url: 'https://blog.google/technology/ai/rss/', type: 'rss', verticals: ['filmmaking', 'digital_humans'], dimensions: [1, 5], scrape_interval: 24 },
  { name: 'Anthropic Blog', url: 'https://www.anthropic.com/blog/rss.xml', type: 'rss', verticals: ['product_photography', 'filmmaking', 'digital_humans'], dimensions: [1], scrape_interval: 24 },
  { name: 'Unreal Engine Blog', url: 'https://www.unrealengine.com/en-US/rss', type: 'rss', verticals: ['filmmaking', 'digital_humans'], dimensions: [1, 5, 8], scrape_interval: 24 },
  { name: 'Substance 3D Blog', url: 'https://substance3d.adobe.com/blog/rss.xml', type: 'rss', verticals: ['product_photography'], dimensions: [1, 2, 5], scrape_interval: 48 },
  { name: 'V-Ray / Chaos Blog', url: 'https://www.chaos.com/blog/feed', type: 'rss', verticals: ['product_photography', 'filmmaking'], dimensions: [1, 5], scrape_interval: 48 },
  { name: 'OctaneRender Forum', url: 'https://render.otoy.com/forum/rss.php', type: 'rss', verticals: ['product_photography'], dimensions: [1, 5], scrape_interval: 48 },
  { name: 'PhotoRoom Blog', url: 'https://www.photoroom.com/blog/rss.xml', type: 'rss', verticals: ['product_photography'], dimensions: [1, 5], scrape_interval: 24 },
  { name: 'Claid AI Blog', url: 'https://claid.ai/blog/rss.xml', type: 'rss', verticals: ['product_photography'], dimensions: [1, 5], scrape_interval: 24 },
]

// ─── Trade press ──────────────────────────────────────────────

const TRADE_PRESS: Source[] = [
  { name: 'fxguide', url: 'https://www.fxguide.com/feed/', type: 'rss', verticals: ['filmmaking'], dimensions: [1, 3, 4, 8], scrape_interval: 24, notes: 'VFX supervisors read this before general press' },
  { name: 'fxguidetv', url: 'https://www.fxguide.com/category/fxguidetv/feed/', type: 'rss', verticals: ['filmmaking'], dimensions: [1, 4, 9], scrape_interval: 48 },
  { name: 'befores & afters', url: 'https://beforesandafters.com/feed/', type: 'rss', verticals: ['filmmaking'], dimensions: [1, 3, 4, 5], scrape_interval: 24 },
  { name: 'VFX Voice', url: 'https://vfxvoice.com/feed/', type: 'rss', verticals: ['filmmaking'], dimensions: [1, 3, 7], scrape_interval: 24 },
  { name: 'Studio Daily', url: 'https://www.studiodaily.com/feed/', type: 'rss', verticals: ['filmmaking', 'product_photography'], dimensions: [1, 3, 5], scrape_interval: 24 },
  { name: 'Cinefex', url: 'https://cinefex.com/blog/feed/', type: 'rss', verticals: ['filmmaking'], dimensions: [4, 9], scrape_interval: 72, notes: 'Irregular, high craft value when it publishes' },
  { name: 'A Photo Editor', url: 'https://www.aphotoeditor.com/feed/', type: 'rss', verticals: ['product_photography'], dimensions: [7, 9], scrape_interval: 48, notes: 'Hiring + market signal for photography industry' },
]

// ─── Reddit ───────────────────────────────────────────────────

const REDDIT: Source[] = [
  { name: 'r/vfx', url: 'https://www.reddit.com/r/vfx/.rss', type: 'rss', verticals: ['filmmaking'], dimensions: [1, 3, 4, 7, 8], scrape_interval: 12, notes: 'Working VFX artists discuss rate cards, unionization, pipeline failures' },
  { name: 'r/keyshot', url: 'https://www.reddit.com/r/keyshot/.rss', type: 'rss', verticals: ['product_photography'], dimensions: [1, 2, 4, 5], scrape_interval: 24 },
  { name: 'r/productphotography', url: 'https://www.reddit.com/r/productphotography/.rss', type: 'rss', verticals: ['product_photography'], dimensions: [1, 2, 4], scrape_interval: 12 },
  { name: 'r/cinematography', url: 'https://www.reddit.com/r/cinematography/.rss', type: 'rss', verticals: ['filmmaking'], dimensions: [1, 4, 9], scrape_interval: 12 },
  { name: 'r/3Dmodeling', url: 'https://www.reddit.com/r/3Dmodeling/.rss', type: 'rss', verticals: ['product_photography', 'filmmaking'], dimensions: [1, 4], scrape_interval: 12 },
  { name: 'r/comfyui', url: 'https://www.reddit.com/r/comfyui/.rss', type: 'rss', verticals: ['product_photography', 'filmmaking', 'digital_humans'], dimensions: [1, 4, 8], scrape_interval: 12, notes: 'Advanced node-graph sharing, ControlNet, latent space manipulation' },
]

// ─── GitHub release feeds ─────────────────────────────────────

const GITHUB: Source[] = [
  { name: 'Houdini Engine for Unreal', url: 'https://github.com/sideeffects/HoudiniEngineForUnreal/releases.atom', type: 'rss', verticals: ['filmmaking'], dimensions: [1, 8], scrape_interval: 48 },
  { name: 'Demucs (stem separation)', url: 'https://github.com/facebookresearch/demucs/releases.atom', type: 'rss', verticals: ['digital_humans'], dimensions: [1, 5], scrape_interval: 72, notes: 'DH now via voice separation. Move to MP when vertical activates' },
  { name: 'p5.js', url: 'https://github.com/processing/p5.js/releases.atom', type: 'rss', verticals: ['filmmaking'], dimensions: [1, 8], scrape_interval: 72, notes: 'Generative/creative coding, light signal' },

  // Open-source pipeline + Stable Diffusion ecosystem
  { name: 'ComfyUI Custom Nodes Tracker', url: 'https://github.com/ltdrdata/ComfyUI-Manager/releases.atom', type: 'rss', verticals: ['product_photography', 'filmmaking', 'digital_humans'], dimensions: [1, 8], scrape_interval: 24, notes: 'Tracks undocumented node updates 48h before YouTube tutorials' },
  { name: 'AUTOMATIC1111 Stable Diffusion WebUI', url: 'https://github.com/AUTOMATIC1111/stable-diffusion-webui/releases.atom', type: 'rss', verticals: ['product_photography', 'filmmaking'], dimensions: [1, 5, 8], scrape_interval: 48, notes: 'Foundational SD repo, performance + sampler additions' },
  { name: 'Auto-Photoshop-StableDiffusion Plugin', url: 'https://github.com/AbdullahAlfaraj/Auto-Photoshop-StableDiffusion-Plugin/commits/master.atom', type: 'rss', verticals: ['product_photography', 'filmmaking'], dimensions: [1, 8], scrape_interval: 72, notes: 'SD bridge into Photoshop, raster-environment integration' },
  { name: 'Awesome Nano Banana Pro Prompts', url: 'https://github.com/YouMind-OpenLab/awesome-nano-banana-pro-prompts/commits/main.atom', type: 'rss', verticals: ['product_photography'], dimensions: [4], scrape_interval: 168, notes: 'JSON-ready prompt structures for hyper-realistic 3D render aesthetics' },
  { name: 'PixiEditor Releases', url: 'https://github.com/PixiEditor/PixiEditor/releases.atom', type: 'rss', verticals: ['product_photography', 'filmmaking'], dimensions: [1, 8], scrape_interval: 168, notes: 'Open-source raster + vector + node-based DCC' },

  // VFX pipeline
  { name: 'Gaffer (node-based pipeline)', url: 'https://github.com/GafferHQ/gaffer/releases.atom', type: 'rss', verticals: ['filmmaking'], dimensions: [1, 4, 8], scrape_interval: 168, notes: 'Studio backbone for lookdev/OSL; pipeline TD-grade' },
  { name: 'Meshroom / AliceVision', url: 'https://github.com/alicevision/meshroom/releases.atom', type: 'rss', verticals: ['filmmaking', 'product_photography'], dimensions: [1, 5], scrape_interval: 168, notes: 'Photogrammetry + 3D Gaussian Splatting integrations' },
  { name: 'ZENO Physics Solvers', url: 'https://github.com/zenustech/zeno/releases.atom', type: 'rss', verticals: ['filmmaking'], dimensions: [1, 8], scrape_interval: 168, notes: 'High-efficiency cinematic physics, OpenVDB' },
  { name: 'Fileseq Library', url: 'https://github.com/sqlboy/fileseq/releases.atom', type: 'rss', verticals: ['filmmaking'], dimensions: [8], scrape_interval: 168, notes: 'Frame range / file sequence parsing for animation pipelines' },
  { name: 'NodeGraphQt Framework', url: 'https://github.com/jchanvfx/NodeGraphQt/releases.atom', type: 'rss', verticals: ['filmmaking'], dimensions: [8], scrape_interval: 168, notes: 'Python/Qt framework for proprietary studio node-graph UIs' },
  { name: 'OpenToonz', url: 'https://github.com/opentoonz/opentoonz/releases.atom', type: 'rss', verticals: ['filmmaking'], dimensions: [1, 8], scrape_interval: 168, notes: '2D animation software customized by Studio Ghibli' },

  // Digital humans / mocap / capture
  { name: 'Awesome 3D Human (curated papers)', url: 'https://github.com/lijiaman/awesome-3d-human/commits/master.atom', type: 'rss', verticals: ['digital_humans'], dimensions: [1, 5], scrape_interval: 168, notes: 'SMPL, PIFu, clothed-human digitization research' },
  { name: 'FreeMoCap', url: 'https://github.com/freemocap/freemocap/releases.atom', type: 'rss', verticals: ['digital_humans', 'filmmaking'], dimensions: [1, 5], scrape_interval: 168, notes: 'Markerless mocap from webcams/phones, research-grade' },
]

// ─── YouTube channels ─────────────────────────────────────────
// VERIFY channel IDs before first deploy

const YOUTUBE: Source[] = [
  { name: 'Two Minute Papers', url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCbfYPyITQ-7l4u8H4mG7Z9g', type: 'rss', verticals: ['filmmaking', 'product_photography', 'digital_humans'], dimensions: [1, 5, 10], scrape_interval: 48, notes: 'Graphics/CV paper breakdowns before mainstream AI press' },
  { name: 'Corridor Crew', url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCSpFnDQr88xCZ80N-X7t0nQ', type: 'rss', verticals: ['filmmaking'], dimensions: [4, 9, 10], scrape_interval: 48, notes: 'VERIFY channel ID before deploy. VFX breakdowns + cultural trend signal' },
  { name: 'Will Gibbons (KeyShot masterclasses)', url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UC-DNKzN1Piv6D4uQeZpL3Wg', type: 'rss', verticals: ['product_photography'], dimensions: [1, 4, 5], scrape_interval: 48, notes: 'Deep technical KeyShot material + lighting tutorials' },
]

// ─── arXiv ────────────────────────────────────────────────────

const ARXIV: Source[] = [
  { name: 'arXiv cs.CV (Computer Vision)', url: 'https://arxiv.org/rss/cs.CV', type: 'rss', verticals: ['product_photography', 'filmmaking', 'digital_humans'], dimensions: [1, 5], scrape_interval: 24 },
  { name: 'arXiv cs.GR (Graphics)', url: 'https://arxiv.org/rss/cs.GR', type: 'rss', verticals: ['filmmaking', 'product_photography'], dimensions: [1, 5], scrape_interval: 24 },
  { name: 'arXiv eess.AS (Audio/Speech)', url: 'https://arxiv.org/rss/eess.AS', type: 'rss', verticals: ['digital_humans'], dimensions: [1, 5], scrape_interval: 24, notes: 'Voice synthesis research. DH now, MP later' },
  { name: 'arXiv cs.SD (Sound/Music)', url: 'https://arxiv.org/rss/cs.SD', type: 'rss', verticals: ['digital_humans'], dimensions: [1, 5], scrape_interval: 24, notes: 'Active for DH voice crossover; primary use is MP when activated' },
]

// ─── Substacks / niche newsletters ────────────────────────────

const SUBSTACKS: Source[] = [
  { name: 'Latent Space', url: 'https://www.latent.space/feed', type: 'rss', verticals: ['filmmaking', 'digital_humans'], dimensions: [1, 3, 8], scrape_interval: 48 },
  { name: 'Bilawal Sidhu (Spatial Intelligence)', url: 'https://www.spatialintelligence.ai/feed', type: 'rss', verticals: ['filmmaking', 'digital_humans'], dimensions: [1, 9], scrape_interval: 72 },
  { name: 'CrowdCraver Substack', url: 'https://crowdcraver.substack.com/feed', type: 'rss', verticals: ['filmmaking'], dimensions: [1, 3], scrape_interval: 168, notes: 'Insider tracking of Kling, Runway Gen-4, Seedance — pipeline viability' },
  { name: 'Sebastian Raschka', url: 'https://magazine.sebastianraschka.com/feed', type: 'rss', verticals: ['product_photography', 'filmmaking', 'digital_humans'], dimensions: [1, 8], scrape_interval: 168, notes: 'Foundational ML architecture explanations driving creative AI tools' },
  { name: 'audEERING (audio AI research)', url: 'https://www.audeering.com/feed/', type: 'rss', verticals: ['digital_humans'], dimensions: [1, 5], scrape_interval: 168, notes: 'Voice biomarker / expression recognition research consortium' },
  { name: 'Sprout Studios Tech Blog', url: 'https://sprout.cc/blog/feed/', type: 'rss', verticals: ['product_photography'], dimensions: [3, 5], scrape_interval: 168, notes: 'CGI vs traditional photography ROI for e-commerce' },
]

// ─── Legal + trade orgs ───────────────────────────────────────

const LEGAL_ORGS: Source[] = [
  { name: 'SAG-AFTRA AI Updates', url: 'https://www.sagaftra.org/contracts-industry-relations/artificial-intelligence', type: 'html', verticals: ['filmmaking', 'digital_humans'], dimensions: [6], scrape_interval: 48, notes: 'AI policy page; critical for Dimension 6' },
  { name: 'SAG-AFTRA Newsroom', url: 'https://www.sagaftra.org/newsroom/rss', type: 'rss', verticals: ['filmmaking', 'digital_humans'], dimensions: [6, 7], scrape_interval: 48, notes: 'Contract negotiations, digital replica riders, federal AI legislation' },
  { name: 'Visual Effects Society', url: 'https://www.visualeffectssociety.com/news/', type: 'html', verticals: ['filmmaking'], dimensions: [6, 7], scrape_interval: 48 },
  { name: 'Visual Effects Society (VFX Voice)', url: 'https://vfxvoice.com/feed/', type: 'rss', verticals: ['filmmaking'], dimensions: [3, 6, 7], scrape_interval: 48, notes: 'Already in trade press; cross-listed for legal awareness' },
  { name: 'RIAA', url: 'https://www.riaa.com/feed/', type: 'rss', verticals: ['digital_humans'], dimensions: [6], scrape_interval: 168, notes: 'Suno/Udio litigation, training-data copyright policy' },
  { name: 'The Voice Foundation', url: 'https://voicefoundation.org/feed/', type: 'rss', verticals: ['digital_humans'], dimensions: [6, 7], scrape_interval: 168, notes: 'Clinical voice science, voice actor IP advocacy' },
]

// ─── Hiring boards (Dimension 7) ──────────────────────────────

const HIRING_BOARDS: Source[] = [
  { name: 'Motionographer Jobs', url: 'https://jobs.motionographer.com/feed/', type: 'rss', verticals: ['filmmaking'], dimensions: [7], scrape_interval: 24, notes: 'Required software stacks + rate cards for motion designers' },
  { name: 'VES Job Board', url: 'https://vesglobal.org/jobboard/feed/', type: 'rss', verticals: ['filmmaking', 'digital_humans'], dimensions: [7], scrape_interval: 48, notes: 'Senior VFX roles, AI-pipeline specialist demand' },
]

// ─── Conferences (yearly / irregular) ─────────────────────────

const CONFERENCES: Source[] = [
  { name: 'NAB Show BEIT', url: 'https://www.nab.org/news/RSSFeeds.asp', type: 'rss', verticals: ['filmmaking'], dimensions: [1, 8], scrape_interval: 168, notes: 'Broadcast Engineering + IT papers, cloud virtualization' },
  { name: 'SIGGRAPH', url: 'https://www.siggraph.org/feed/', type: 'rss', verticals: ['filmmaking', 'product_photography', 'digital_humans'], dimensions: [1, 5], scrape_interval: 168, notes: 'Computer graphics research authority' },
]

// ─── Combined export ──────────────────────────────────────────

export const SOURCES: Source[] = [
  ...TOOL_BLOGS,
  ...TRADE_PRESS,
  ...REDDIT,
  ...GITHUB,
  ...YOUTUBE,
  ...ARXIV,
  ...SUBSTACKS,
  ...LEGAL_ORGS,
  ...HIRING_BOARDS,
  ...CONFERENCES,
]

// ─── Filtered helpers ─────────────────────────────────────────

export function sourcesByType(type: SourceType): Source[] {
  return SOURCES.filter(s => s.type === type)
}

export function sourcesByVertical(vertical: Vertical): Source[] {
  return SOURCES.filter(s => s.verticals.includes(vertical))
}

export function sourcesDueForScrape(now = new Date()): Source[] {
  // Caller checks last_scraped_at from scrape_log. This is the registry side.
  // Return all and let the orchestrator filter against scrape_log.
  return SOURCES
}
