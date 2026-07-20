# GenLens NotebookLM Source Bundle

Generated: 2026-06-01T10:17:49-07:00

This bundle is the seed corpus for Genny, the GenLens intelligence agent. It contains the source registry, canonical tools manifest, vertical backlog, user preferences, and persistent feedback. Use it as NotebookLM grounding material, not as a license to invent fresh news.

## Operating Rules

- Preserve source names and links when answering.
- Treat RSS/manual sources as leads until verified.
- Never fabricate time/cost deltas, product claims, images, or verticals.
- Active verticals: Product Photography, AI Filmmaking, Digital Humans.
- Expanded/on-deck verticals: Advertising / Brand Content, ArchViz, AI Design / Motion Graphics, Music Production / Audio, Fashion / Apparel / Textile.

---

## Jonathan Feedback

# Jonathan Feedback For Genny

Last updated: 2026-05-28

Jonathan's feedback should override vague defaults when interpreting GenLens brief requests.

## What He Wants

- Robust, complete GenLens intelligence artifacts.
- Expanded verticals when asking for a new/robust/beautiful/complete brief.
- Beautiful email delivery with UX, images, headings, source links, and readable hierarchy.
- Article preview images when available.
- Enough source-backed items to feel like a real newsletter, not a tiny sample.
- Direct execution, then concise reporting with IDs/results.

## What He Does Not Want

- Paltry four-item briefs.
- Local-only HTML files as the final delivery.
- Generic source lists presented as finished intelligence.
- Old Schultz or VibeCopy naming.
- Excuses before taking action.
- Claims that an email was sent unless Resend returns an ID.

## Default Interpretation

- "New brief" means compose expanded briefing and email it.
- "Email it" means use Resend visual template.
- "Beautiful" means `genlens-briefing` template, article images, clean headings, chips, and links.
- "Robust", "complete", or "boil the ocean" means expanded mode with on-deck verticals.


---

## Preferences JSON

```json
{
  "owner": "Jonathan",
  "default_recipient": "jj@damnjj.wtf",
  "default_delivery": "email",
  "default_mode": "expanded",
  "default_per_vertical": 4,
  "default_rss_limit": 8,
  "tone": "warm, expert, direct, never corporate",
  "briefing_preferences": [
    "Use expanded coverage for new, robust, complete, beautiful, or email briefs.",
    "Send a designed email by default when a brief is requested.",
    "Use article preview images when available.",
    "Prefer source-backed production impact over generic AI hype.",
    "Include enough items and verticals to feel like a real intelligence product.",
    "Avoid paltry four-item briefs unless source quality is genuinely poor.",
    "Do not send local-only HTML as the final artifact unless explicitly requested.",
    "Do not claim delivery without a Resend response ID."
  ],
  "quality_filters": [
    "Prefer tool releases, workflow changes, production economics, model capability shifts, legal/compliance changes, and pipeline case studies.",
    "Avoid generic brand news, celebrity news, hiring news, listicles, and broad culture pieces unless directly tied to AI creative production.",
    "Treat Reddit/community chatter as leads only; verify with official sources when possible."
  ],
  "visual_preferences": [
    "Dark editorial interface.",
    "Strong heading hierarchy.",
    "Vertical labels.",
    "Metric chips.",
    "Article/source links.",
    "Preview images or vertical fallback images."
  ]
}

```

---

## Source Registry JSON

```json
{
  "source_registry": {
    "name": "GenLens creative production intelligence sources",
    "owner": "Genny",
    "updated": "2026-05-28",
    "notes": [
      "This is Genny's source of truth for external monitoring.",
      "The GenLens digest endpoint is optional and currently treated as an unhealthy upstream until TLS is fixed.",
      "Manual sources require source-backed summarization; do not infer product claims from the source name alone.",
      "Expanded-mode candidate verticals are on deck for robust briefs; daily default remains active GenLens verticals unless requested."
    ]
  },
  "verticals": {
    "Product Photography": [
      {
        "name": "Adobe Blog",
        "url": "https://blog.adobe.com/",
        "rss": "",
        "priority": "high",
        "cadence": "daily",
        "watch_for": [
          "Firefly",
          "commerce",
          "product imagery",
          "Photoshop",
          "Lightroom",
          "creative production"
        ]
      },
      {
        "name": "Photoroom Blog",
        "url": "https://www.photoroom.com/blog",
        "rss": "",
        "priority": "high",
        "cadence": "weekly",
        "watch_for": [
          "product photos",
          "backgrounds",
          "marketplace imagery",
          "AI editing",
          "batch creative"
        ]
      },
      {
        "name": "Creative Force Blog",
        "url": "https://www.creativeforce.io/blog",
        "rss": "",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "studio workflow",
          "ecommerce photography",
          "production operations",
          "shot lists"
        ]
      },
      {
        "name": "Pebblely Blog",
        "url": "https://pebblely.com/blog",
        "rss": "",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "AI product photography",
          "product scenes",
          "lifestyle images"
        ]
      },
      {
        "name": "Booth AI",
        "url": "https://www.booth.ai/",
        "rss": "",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "virtual photoshoots",
          "product campaigns",
          "AI-generated product imagery"
        ]
      },
      {
        "name": "Flair AI",
        "url": "https://flair.ai/",
        "rss": "",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "branded product scenes",
          "AI campaign imagery",
          "ecommerce creative"
        ]
      },
      {
        "name": "Krea",
        "url": "https://www.krea.ai/",
        "rss": "",
        "priority": "high",
        "cadence": "daily",
        "watch_for": [
          "image generation",
          "upscaling",
          "real-time creative tools",
          "brand workflows"
        ]
      },
      {
        "name": "Freepik AI",
        "url": "https://www.freepik.com/ai",
        "rss": "",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "image generation",
          "product mockups",
          "commercial asset production"
        ]
      },
      {
        "name": "Topaz Labs",
        "url": "https://www.topazlabs.com/",
        "rss": "",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "upscaling",
          "denoise",
          "image restoration",
          "delivery quality"
        ]
      }
    ],
    "AI Filmmaking": [
      {
        "name": "Runway Blog",
        "url": "https://runwayml.com/blog",
        "rss": "",
        "priority": "high",
        "cadence": "daily",
        "watch_for": [
          "video generation",
          "Gen-4",
          "filmmaking",
          "commercial workflows",
          "motion control"
        ]
      },
      {
        "name": "Luma AI",
        "url": "https://lumalabs.ai/",
        "rss": "",
        "priority": "high",
        "cadence": "daily",
        "watch_for": [
          "Dream Machine",
          "video generation",
          "3D capture",
          "camera motion",
          "scene consistency"
        ]
      },
      {
        "name": "Pika",
        "url": "https://pika.art/",
        "rss": "",
        "priority": "high",
        "cadence": "daily",
        "watch_for": [
          "video generation",
          "effects",
          "commercial spots",
          "editing"
        ]
      },
      {
        "name": "Seedance 2.0 Official Page",
        "url": "https://seed.bytedance.com/en/seedance2_0",
        "rss": "",
        "priority": "high",
        "cadence": "daily",
        "watch_for": [
          "Seedance",
          "ByteDance Seed",
          "multi-shot video",
          "image-to-video",
          "audio-video generation",
          "commercial licensing"
        ],
        "notes": "Primary Seedance model page. Treat availability, territory, and licensing details as facts only when confirmed from this source or another cited source."
      },
      {
        "name": "Seedance 2.0 Paper",
        "url": "https://arxiv.org/abs/2604.14148",
        "rss": "",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "Seedance",
          "world complexity",
          "generation speed",
          "quality benchmarks",
          "model limitations"
        ]
      },
      {
        "name": "Kling AI",
        "url": "https://kling.ai/",
        "rss": "",
        "priority": "high",
        "cadence": "daily",
        "watch_for": [
          "Kling",
          "AI video",
          "image-to-video",
          "cinematic control",
          "commercial workflows"
        ]
      },
      {
        "name": "Google DeepMind Veo",
        "url": "https://deepmind.google/technologies/veo/",
        "rss": "",
        "priority": "high",
        "cadence": "daily",
        "watch_for": [
          "Veo",
          "native audio",
          "video generation",
          "creative controls",
          "production case studies"
        ]
      },
      {
        "name": "OpenAI Sora Video Generation",
        "url": "https://platform.openai.com/docs/guides/video-generation/",
        "rss": "",
        "priority": "high",
        "cadence": "weekly",
        "watch_for": [
          "Sora",
          "video API",
          "pricing",
          "rights",
          "workflow limits"
        ]
      },
      {
        "name": "Black Forest Labs",
        "url": "https://blackforestlabs.ai/",
        "rss": "",
        "priority": "high",
        "cadence": "weekly",
        "watch_for": [
          "FLUX",
          "image models",
          "video workflows",
          "commercial image generation"
        ]
      },
      {
        "name": "ComfyUI GitHub",
        "url": "https://github.com/comfyanonymous/ComfyUI",
        "rss": "",
        "priority": "high",
        "cadence": "daily",
        "watch_for": [
          "node workflows",
          "video pipelines",
          "model support",
          "production automation"
        ]
      },
      {
        "name": "fal Blog",
        "url": "https://fal.ai/blog",
        "rss": "",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "inference",
          "image models",
          "video models",
          "latency",
          "cost"
        ]
      },
      {
        "name": "fxguide",
        "url": "https://www.fxguide.com/",
        "rss": "https://www.fxguide.com/feed/",
        "priority": "high",
        "cadence": "daily",
        "watch_for": [
          "VFX",
          "virtual production",
          "AI tools",
          "pipeline"
        ]
      },
      {
        "name": "No Film School",
        "url": "https://nofilmschool.com/",
        "rss": "https://nofilmschool.com/rss.xml",
        "priority": "medium",
        "cadence": "daily",
        "watch_for": [
          "filmmaking tools",
          "production",
          "post-production",
          "AI video"
        ]
      },
      {
        "name": "CineD",
        "url": "https://www.cined.com/",
        "rss": "https://www.cined.com/feed/",
        "priority": "medium",
        "cadence": "daily",
        "watch_for": [
          "camera",
          "production gear",
          "workflow",
          "post-production"
        ]
      }
    ],
    "Digital Humans": [
      {
        "name": "ElevenLabs Blog",
        "url": "https://elevenlabs.io/blog",
        "rss": "",
        "priority": "high",
        "cadence": "daily",
        "watch_for": [
          "voice synthesis",
          "dubbing",
          "agents",
          "voice design",
          "licensing"
        ]
      },
      {
        "name": "Synthesia Blog",
        "url": "https://www.synthesia.io/blog",
        "rss": "",
        "priority": "high",
        "cadence": "weekly",
        "watch_for": [
          "AI avatars",
          "digital humans",
          "enterprise video",
          "synthetic presenters"
        ]
      },
      {
        "name": "HeyGen Blog",
        "url": "https://www.heygen.com/blog",
        "rss": "",
        "priority": "high",
        "cadence": "weekly",
        "watch_for": [
          "avatars",
          "video translation",
          "digital actors",
          "UGC-style production"
        ]
      },
      {
        "name": "Tavus",
        "url": "https://www.tavus.io/",
        "rss": "",
        "priority": "high",
        "cadence": "weekly",
        "watch_for": [
          "conversational video",
          "digital twins",
          "personalized video",
          "API workflows"
        ]
      },
      {
        "name": "D-ID",
        "url": "https://www.d-id.com/",
        "rss": "",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "talking avatars",
          "agents",
          "video generation",
          "enterprise rights"
        ]
      },
      {
        "name": "Captions",
        "url": "https://www.captions.ai/",
        "rss": "",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "AI avatars",
          "creator video",
          "editing",
          "commercial social assets"
        ]
      },
      {
        "name": "NVIDIA Blog",
        "url": "https://blogs.nvidia.com/",
        "rss": "https://blogs.nvidia.com/feed/",
        "priority": "medium",
        "cadence": "daily",
        "watch_for": [
          "ACE",
          "digital humans",
          "Omniverse",
          "rendering",
          "simulation"
        ]
      },
      {
        "name": "Unreal Engine News",
        "url": "https://www.unrealengine.com/en-US/news",
        "rss": "",
        "priority": "high",
        "cadence": "weekly",
        "watch_for": [
          "MetaHuman",
          "Unreal Engine",
          "real-time humans",
          "mocap",
          "animation"
        ]
      },
      {
        "name": "Wonder Dynamics",
        "url": "https://wonderdynamics.com/",
        "rss": "",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "character replacement",
          "markerless VFX",
          "live-action to CG",
          "production workflows"
        ]
      },
      {
        "name": "Move AI",
        "url": "https://www.move.ai/",
        "rss": "",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "markerless mocap",
          "body capture",
          "animation pipeline"
        ]
      },
      {
        "name": "DeepMotion",
        "url": "https://www.deepmotion.com/",
        "rss": "",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "AI motion capture",
          "animation",
          "retargeting",
          "avatar motion"
        ]
      },
      {
        "name": "Reallusion Magazine",
        "url": "https://magazine.reallusion.com/",
        "rss": "https://magazine.reallusion.com/feed/",
        "priority": "medium",
        "cadence": "daily",
        "watch_for": [
          "Character Creator",
          "iClone",
          "mocap",
          "facial animation"
        ]
      }
    ],
    "Cross-Vertical Watchlist": [
      {
        "name": "Replicate Blog",
        "url": "https://replicate.com/blog",
        "rss": "https://replicate.com/blog/rss",
        "priority": "high",
        "cadence": "daily",
        "watch_for": [
          "models",
          "image generation",
          "video generation",
          "open-source releases"
        ]
      },
      {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog",
        "rss": "https://huggingface.co/blog/feed.xml",
        "priority": "high",
        "cadence": "daily",
        "watch_for": [
          "models",
          "diffusion",
          "video",
          "audio",
          "agents"
        ]
      },
      {
        "name": "OpenAI News",
        "url": "https://openai.com/news/",
        "rss": "",
        "priority": "high",
        "cadence": "daily",
        "watch_for": [
          "Sora",
          "image generation",
          "video generation",
          "pricing",
          "API changes"
        ]
      },
      {
        "name": "Google DeepMind Blog",
        "url": "https://deepmind.google/discover/blog/",
        "rss": "",
        "priority": "high",
        "cadence": "daily",
        "watch_for": [
          "Veo",
          "Genie",
          "world models",
          "creative AI",
          "licensing"
        ]
      },
      {
        "name": "Anthropic News",
        "url": "https://www.anthropic.com/news",
        "rss": "",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "agents",
          "tool use",
          "computer use",
          "creative operations"
        ]
      },
      {
        "name": "Stability AI News",
        "url": "https://stability.ai/news",
        "rss": "",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "image models",
          "video models",
          "licensing",
          "commercial rights"
        ]
      },
      {
        "name": "CG Channel",
        "url": "https://www.cgchannel.com/",
        "rss": "https://www.cgchannel.com/feed/",
        "priority": "medium",
        "cadence": "daily",
        "watch_for": [
          "CGI",
          "VFX tools",
          "rendering",
          "animation"
        ]
      },
      {
        "name": "SAG-AFTRA AI Resources",
        "url": "https://www.sagaftra.org/contracts-industry-resources/ai-resources",
        "rss": "",
        "priority": "high",
        "cadence": "weekly",
        "watch_for": [
          "likeness rights",
          "digital replica",
          "performer consent",
          "commercial compliance"
        ]
      }
    ],
    "Advertising / Brand Content": [
      {
        "name": "Adweek AI",
        "url": "https://www.adweek.com/category/artificial-intelligence/",
        "rss": "https://www.adweek.com/category/artificial-intelligence/feed/",
        "priority": "high",
        "cadence": "daily",
        "watch_for": [
          "campaign production",
          "brand content",
          "agency AI workflows",
          "asset variant production"
        ]
      },
      {
        "name": "The Drum Creative",
        "url": "https://www.thedrum.com/creative",
        "rss": "https://www.thedrum.com/rss.xml",
        "priority": "medium",
        "cadence": "daily",
        "watch_for": [
          "brand campaigns",
          "creative production",
          "agency workflows"
        ]
      },
      {
        "name": "Canva Newsroom",
        "url": "https://www.canva.com/newsroom/",
        "rss": "https://www.canva.com/newsroom/feed/",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "campaign design",
          "brand kits",
          "AI content tools"
        ]
      },
      {
        "name": "Typeface Blog",
        "url": "https://www.typeface.ai/blog",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "enterprise brand content",
          "campaign generation",
          "marketing asset pipelines"
        ]
      }
    ],
    "ArchViz": [
      {
        "name": "Dezeen",
        "url": "https://www.dezeen.com/",
        "rss": "https://www.dezeen.com/feed/",
        "priority": "medium",
        "cadence": "daily",
        "watch_for": [
          "visualization",
          "interiors",
          "rendering aesthetics",
          "AEC visualization"
        ]
      },
      {
        "name": "ArchDaily",
        "url": "https://www.archdaily.com/",
        "rss": "https://www.archdaily.com/feed",
        "priority": "medium",
        "cadence": "daily",
        "watch_for": [
          "architecture visualization",
          "renders",
          "design tools"
        ]
      },
      {
        "name": "Chaos Blog",
        "url": "https://blog.chaos.com/",
        "rss": "https://blog.chaos.com/rss.xml",
        "priority": "high",
        "cadence": "weekly",
        "watch_for": [
          "V-Ray",
          "Corona",
          "rendering",
          "ArchViz workflows"
        ]
      },
      {
        "name": "Enscape Blog",
        "url": "https://blog.enscape3d.com/",
        "rss": "https://blog.enscape3d.com/rss.xml",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "real-time architectural visualization",
          "design review",
          "AEC rendering"
        ]
      }
    ],
    "AI Design / Motion Graphics": [
      {
        "name": "Motionographer",
        "url": "https://motionographer.com/",
        "rss": "https://motionographer.com/feed/",
        "priority": "high",
        "cadence": "daily",
        "watch_for": [
          "motion design",
          "studio workflows",
          "animation tools"
        ]
      },
      {
        "name": "Figma Blog",
        "url": "https://www.figma.com/blog/",
        "rss": "https://www.figma.com/blog/feed/",
        "priority": "high",
        "cadence": "weekly",
        "watch_for": [
          "AI design tools",
          "Weave",
          "design systems",
          "prototyping"
        ]
      },
      {
        "name": "Framer Blog",
        "url": "https://www.framer.com/blog/",
        "rss": "https://www.framer.com/blog/rss.xml",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "AI site design",
          "interactive design",
          "motion"
        ]
      }
    ],
    "Music Production / Audio": [
      {
        "name": "MusicTech",
        "url": "https://musictech.com/",
        "rss": "https://musictech.com/feed/",
        "priority": "medium",
        "cadence": "daily",
        "watch_for": [
          "AI music",
          "production tools",
          "mastering",
          "stem separation"
        ]
      },
      {
        "name": "LANDR Blog",
        "url": "https://blog.landr.com/",
        "rss": "https://blog.landr.com/feed/",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "mastering",
          "AI music production",
          "creator workflows"
        ]
      },
      {
        "name": "iZotope Learn",
        "url": "https://www.izotope.com/en/learn.html",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "audio repair",
          "mixing",
          "mastering",
          "stem splitting"
        ]
      }
    ],
    "Fashion / Apparel / Textile": [
      {
        "name": "The Interline",
        "url": "https://www.theinterline.com/",
        "rss": "https://www.theinterline.com/feed/",
        "priority": "high",
        "cadence": "weekly",
        "watch_for": [
          "digital fashion",
          "3D garment",
          "supply chain",
          "AI design"
        ]
      },
      {
        "name": "CLO Virtual Fashion Blog",
        "url": "https://www.clovirtualfashion.com/blog",
        "priority": "high",
        "cadence": "weekly",
        "watch_for": [
          "CLO 3D",
          "garment simulation",
          "virtual samples"
        ]
      },
      {
        "name": "WGSN Insight",
        "url": "https://www.wgsn.com/en/blogs",
        "priority": "medium",
        "cadence": "weekly",
        "watch_for": [
          "trend forecasting",
          "color",
          "fashion consumer shifts"
        ]
      }
    ]
  },
  "briefing_rules": [
    "Only use facts present in source output or user-provided material.",
    "Label unverified items as unverified instead of presenting them as signals.",
    "Prefer tool releases, workflow evidence, pricing/licensing changes, production case studies, and measurable time/cost deltas.",
    "Separate product capability claims from availability, pricing, territory, and rights claims.",
    "For actor likeness, brand/IP, synthetic performer, or training-data issues, include compliance context when source-backed.",
    "Ignore generic AI hype unless it has a concrete production implication for working Gen ADs."
  ]
}

```

---

## Tools Manifest

# GenLens Tools Manifest

**Complete list of 130+ AI creative tools tracked across 6 verticals.**

Last updated: April 26, 2026
Format: Each vertical lists tools by category (rendering, composition, voice, etc.)

-----

## VERTICAL 1: PRODUCT PHOTOGRAPHY

### CAD / 3D Modeling

- Figma Weave (product mockup -> 3D)
- Fusion 360 (parametric modeling, AI assists)
- Solidworks (engineering to product rendering pipeline)
- Blender (open-source, GPU rendering)
- Rhino (industrial design)
- FreeCAD (parametric CAD)
- Tinkercad (beginner CAD)

### Rendering

- **KeyShot 2026** (real-time rendering, AI relighting)
- Octane Render (GPU-accelerated)
- V-Ray (production rendering)
- Arnold (AI denoising)
- RenderMan (Pixar standard)
- Cycles (Blender native)
- Redshift (real-time 3D)
- Corona Renderer (photorealism)
- Lumion (architectural/product)
- Vray Next (GPU rendering)

### Lighting / Materials / Texturing

- Substance 3D (material workflows)
- Marmoset Toolbag (real-time rendering + texturing)
- Quixel Megascans (asset library)
- Adobe Firefly (texture generation)
- Stable Diffusion XL (texture generation)
- Runway Gen-2 (texture synthesis)
- ClipDrop (AI texture from images)

### Background Generation / Compositing

- **Claid AI** (background removal + generation)
- Remove.bg (background removal)
- Photoshop Generative Fill (compositing)
- Affinity Photo (non-destructive compositing)
- GIMP (open-source compositing)
- Nuke (professional VFX compositing)
- After Effects (motion + compositing)
- Krea AI (image expansion)
- Upscayl (upscaling)

### Post-Processing / Color Grading

- Adobe Lightroom AI (batch editing)
- Capture One (color accuracy)
- Exposure X7 (raw processing)
- DxO PhotoLab (AI denoising, lens correction)
- Aurora HDR (HDR processing)
- ON1 Photo Raw (AI masking, editing)

### E-commerce / Presale

- Shopify (marketplace integration)
- WooCommerce (product feeds)
- BigCommerce (product data)
- Printful (POD integration)
- Teespring (creator commerce)
- Printable (batch ordering)

-----

## VERTICAL 2: COMMERCIAL FILMMAKING

### Pre-Production / Storyboarding / Concept

- Shotlist (virtual storyboarding)
- Previz (pre-visualization VFX)
- Adobe Animate (quick animatics)
- Procreate Dreams (iPad animation)
- Blender Grease Pencil (2D in 3D)

### Live Action Capture / Shooting

- DaVinci Resolve (color grading + editing, AI features)
- Premiere Pro (editing + dynamic link to AE)
- Final Cut Pro (magnetic timeline, native color)
- Shotcut (open-source editing)
- HitFilm Express (VFX-first editing)

### VFX / Compositing

- **After Effects** (industry standard VFX, Firefly integration)
- Nuke (node-based compositing, deep integration)
- Fusion (DaVinci ecosystem)
- Natron (open-source node compositing)
- Houdini (procedural FX, simulation)
- Maya (rigging, animation, dynamics)
- 3ds Max (game engine pipeline)
- Blender (full 3D + VFX)
- Cinema 4D (motion graphics-friendly 3D)

### Color Grading / Finishing

- **DaVinci Resolve Studio** (professional grading suite)
- ColorLogic (professional grading)
- Adobe SpeedGrade (deprecated, Resolve replacement)
- Baselight (high-end grading)

### Motion Design / Motion Graphics

- **Cavalry** (node-based motion design)
- Rive (interactive motion)
- Jitter (creative code for motion)
- Haiku Animator (generative animation)
- Lottie (web animation)
- Adobe Animate (frame-by-frame + tweening)

### Sound Design / Audio Post

- **Descript** (video transcription, speech removal, auto-captions)
- Adobe Audition (audio editing + noise reduction)
- DaVinci Resolve (audio in timeline)
- Logic Pro (music production)
- Pro Tools (audio engineering standard)
- Reaper (DAW, unlimited tracks)
- Audacity (open-source audio editing)
- IZOTOPE RX (advanced audio repair)
- ffmpeg (command-line audio/video)

### Rendering / Engine

- **Unreal Engine 5** (Nanite, Lumen, MetaHuman for synthetic actors)
- Unity (real-time rendering, game engine)
- Luma AI (neural radiance fields, video synthesis)
- Sora (OpenAI video generation)
- Runway Gen-2 (video synthesis, motion transfer)
- Deforum (Stable Diffusion animation)

-----

## VERTICAL 3: DIGITAL HUMANS / SYNTHETIC ACTORS

### Character Design / 3D Avatar

- MetaHuman Creator (Unreal, realistic digital humans)
- **D-ID** (realistic talking head from image/video)
- Synthesia (video avatar generation)
- HeyGen (video avatar creation)
- Genies (avatar creation for metaverse)
- Roblox Studio (gaming avatar)
- ReadyPlayer.Me (avatar for web3)

### Voice Generation / Synthesis

- **ElevenLabs** (emotional prosody, multilingual)
- Google Cloud Text-to-Speech (multilingual)
- Amazon Polly (neural voices)
- Microsoft Azure Speech (real-time synthesis)
- **Resemble AI** (voice cloning, emotional range)
- Coqui TTS (open-source TTS)
- Bark AI (TTS with emotion)
- Tortoise TTS (naturalness)
- Descript Overdub (voice cloning from recordings)

### Animation / Motion Capture

- **Runway Animate** (pose-to-video, motion transfer)
- **Move.ai** (markerless motion capture)
- Rokoko (motion capture suit)
- DeepMotion (AI mocap)
- Cascable (motion capture from video)
- Radical Motion (lightweight mocap)
- MotionBuilder (rigging + animation)
- Mixamo (motion capture library)

### Lip-Sync / Dialogue Sync

- **Descript** (auto-sync, speech alignment)
- Papercut (lip-sync from audio)
- Salsa3D (automatic lip-sync)
- Jali Research (speech-driven animation)

### Scene Composition / Rendering

- Unreal Engine 5 (real-time compositing)
- Unity (real-time rendering)
- Blender (offline rendering)
- Substance Painter (material authoring)

### Full-Body AI Performance Capture

- Xsens (sensor-based mocap)
- OptiTrack (optical motion capture)
- Noitom PerceptionNeuron (wireless mocap)
- Vicon (professional mocap system)

-----

## VERTICAL 4: MUSIC PRODUCTION / AUDIO

### Music Generation / Composition

- **Suno AI** (AI music generation, full songs)
- **Udio** (AI music generation, royalty-free)
- AIVA (AI composition for film/game)
- Amper Music (adaptive music generation)
- Soundraw (AI music creation)
- Mubert (generative music)
- OpenAI Jukebox (music generation)

### Stem Separation / Source Splitting

- **iZotope RX Neural Stem Splitter** (AI source separation)
- Descript Stems (automatic stem extraction)
- Spleeter (open-source stem separation)
- Adobe Audition Remix (gesture-based mixing)
- Isolator Network (stem splitting)

### Mastering / Audio Enhancement

- **iZotope Ozone AI** (intelligent mastering)
- Landr (automated mastering)
- MasterWorks (reference-based mastering)
- Deezer Stem Splitter (source separation for mixing)
- NeuralDSP (tone modeling for guitars)

### Sound Design / Effects

- **Suno SoundShaping** (parametric sound design)
- Splice (sound library + AI recommendations)
- Soundly (impact sound design)
- Jambee AI (harmonic analysis + suggestions)
- Audio Ease Altiverb (convolution reverb)

### DAW / Music Production

- **Logic Pro** (Apple ecosystem, native plugins)
- **Ableton Live** (clip-based production, Max for Live)
- Reaper (unlimited tracks, scripting)
- FL Studio (grid-based production)
- Cubase (professional DAW, AI features)
- Pro Tools (industry standard for music + audio)
- Studio One (PreSonus ecosystem)

### Vocals / Voice Production

- **Melodyne** (pitch/time manipulation without artifacts)
- Antares Auto-Tune (pitch correction)
- iZotope VocalSynth (vocal processing)
- Waves Clarity Vx (vocal enhancement)
- Descript (transcript-to-voice, synthetic voiceover)

### Mixing / Dynamics

- **iZotope Neutron AI** (intelligent mixing plugin)
- Waves SSL (classic console emulation)
- FabFilter Pro-Q (EQ with AI suggestions)
- Soundtoys (creative processing)
- Universal Audio (Neve, SSL, Neve emulation)

-----

## VERTICAL 5: AI-ACCELERATED DESIGN / MOTION GRAPHICS

### Design / Vector Graphics

- **Figma with Plugins** (design system, prototyping, Weave)
- Adobe XD (UI design + prototyping)
- Sketch (macOS design, plugins)
- Affinity Designer (vector graphics)
- CorelDRAW (commercial design)

### Motion Design / Animation

- **Cavalry** (node-based motion design)
- **Rive** (interactive animation for web/app)
- **Jitter** (creative coding for motion)
- **Haiku Animator** (generative design system)
- Lottie (cross-platform animation format)
- Spline (3D design in browser)
- Framer (React-based prototyping)

### Generative Design / Parametric

- Processing (creative coding)
- p5.js (JavaScript creative coding)
- Grasshopper (parametric design in Rhino)
- Houdini (procedural asset generation)
- TouchDesigner (visual programming)

### Layout / Composition AI

- Adobe Firefly (design composition generation)
- Midjourney (image generation from text)
- Stable Diffusion (open-source image generation)
- DALL-E 3 (text-to-image)
- Krea AI (AI design tool)

### Typography / Font Design

- Fontlab (type design)
- Glyphs (font editor)
- Variable fonts (responsive typography)
- Adobe Fonts (creative cloud library)
- Google Fonts (open-source typography)

### Interaction Design / Prototyping

- **Figma** (real-time collaboration)
- Framer (code-based prototyping)
- Webflow (visual development)
- Adobe XD (high-fidelity prototyping)
- Marvel (mobile prototyping)

### Color / Palette Generation

- Adobe Color (color harmony generation)
- Coolors.co (palette generator)
- Chroma.js (color scale generation)
- Huemint (AI color palette)
- Khroma (AI color discovery)

### Asset Management / Libraries

- Abstract (design version control)
- Figma Libraries (shared components)
- Zeplin (design handoff)
- InVision DSM (design system management)
- Knack (asset library)

-----

## VERTICAL 6: FASHION / APPAREL / TEXTILE DESIGN

### 3D Garment Simulation

- **CLO 3D** (industry-standard garment simulation)
- **Marvelous Designer** (cloth simulation, real-time)
- Browzwear (3D garment design)
- Optitex (pattern-to-3D pipeline)
- StyleShoots (product photography for apparel)

### Pattern Design / Grading

- Gerber AccuMark (CAD pattern design)
- Lectra Kaledo (pattern automation)
- Optitex Modaris (pattern grading, AI sizing)
- Zeng Zeng Pattern (fabric-to-pattern design)

### Fabric / Textile Generation

- Stable Diffusion (texture generation for textiles)
- Midjourney (fabric design ideation)
- Adobe Firefly (textile pattern generation)
- ASOS Design Lab (trend-based design)
- Printful (on-demand fabric printing)

### Size Prediction / Fit

- True Fit (fit prediction AI)
- SizeScale (AI sizing algorithms)
- Fittech (smart sizing)
- StitchFix algorithms (personal fit prediction)

### Color / Trend Forecasting

- WGSN (trend forecasting platform)
- Fashion Snoops (color + trend forecasting)
- TRENDSTOP (season trend analysis)
- Adobe Color Trends (design trend generation)
- Shutterstock Trends (visual trend analysis)

### E-Commerce / Retail

- Shopify (apparel marketplace)
- WooCommerce (fashion store)
- BigCommerce (large catalog management)
- Printful (POD + integration)
- Printify (multi-supplier POD)

### Photography / Product Imaging

- StyleShoots (apparel product photography)
- Claid AI (background generation for apparel)
- Remove.bg (garment isolation)
- Figma Weave (mockup generation)
- Photoshop Generative Fill (retouching apparel)

### Inventory / Supply Chain

- TraceableAI (supply chain transparency)
- FashionBI (inventory forecasting)
- Celerity (demand forecasting)
- Shoptimized (inventory optimization)

-----

## VERTICAL 7 (SHELVED): Game Development / Real-Time 3D

### Engines

- Unreal Engine 5 (Nanite, Lumen)
- Unity (real-time 3D)
- Godot (open-source game engine)
- Amazon Lumberyard (AWS-integrated)

### Procedural Generation

- Houdini (procedural assets)
- World Creator (terrain generation)
- Gaea (terrain design)
- SpeedTree (tree generation)

### Asset Libraries

- Quixel Megascans (photogrammetry assets)
- Polyhaven (free 3D assets)
- Sketchfab (model marketplace)
- CGTrader (3D asset marketplace)

### AI for Game Dev

- NVIDIA ACE (character AI)
- OpenAI Codex (code generation for gameplay)
- Deep Tagging (asset organization)
- GodotAI (open-source game AI)

-----

## VERTICAL 8 (SHELVED): Scientific Visualization / Data

### Tools

- D3.js (data visualization)
- Plotly (interactive charts)
- Tableau (business intelligence)
- Power BI (enterprise analytics)
- Observable (computational notebooks)

-----

## VERTICAL 9 (SHELVED): Medical Imaging / Healthcare

### Tools

- ITK (image segmentation)
- VTK (3D visualization)
- ParaView (scientific visualization)
- DICOM viewers (medical imaging standard)

-----

## Cross-Vertical Tools (appear in multiple verticals)

**Render Engines:**

- Blender (used in Product Photography, Filmmaking, Digital Humans, Fashion, Games)
- Unreal Engine 5 (Filmmaking, Digital Humans, Games)
- Arnold (Product Photography, Filmmaking)

**Image/Video Generation:**

- Stable Diffusion XL (Product Photography, Motion Graphics, Fashion, Games)
- Midjourney (Product Photography, Motion Graphics, Fashion)
- DALL-E 3 (across all)
- Runway Gen-2 (Filmmaking, Digital Humans, Music sync to video)

**Compositing:**

- After Effects (Filmmaking, Motion Graphics, Music video)
- Nuke (Filmmaking, VFX, Product Photography compositing)

**Design Platforms:**

- Figma (Product Photography via Weave, Motion Graphics, Fashion mockups)
- Adobe Creative Cloud (all verticals)

**DAW / Audio:**

- DaVinci Resolve (Filmmaking, Music sync, Audio)
- Adobe Audition (Filmmaking, Music, Podcasts)

**Open Source Across All:**

- Blender (3D, rendering, compositing)
- GIMP (image editing)
- Audacity (audio editing)
- FFmpeg (format conversion, media pipeline)
- Krita (digital painting)

-----

## How to Use This Manifest

1. **Scraper sources:** Each tool in this list is traceable to 1+ of your 130+ sources. When building the scraper, cross-reference this list. If a new tool appears in your sources and is not here, add it.
2. **Tool taxonomy:** Every signal ingested references tools. The tool name must be normalized against this canonical list (e.g., "elevenlabs" -> "ElevenLabs", "final cut" -> "Final Cut Pro").
3. **Leaderboard:** Tools are ranked by Score, which is computed from signals that reference them. Every tool on this list is scoreable.
4. **Vertical filtering:** Users toggle between verticals and see only signals relevant to their tools.
5. **Cross-vertical insights:** Some tools appear in multiple verticals (Blender, After Effects, Figma, Stable Diffusion). These are your most versatile, highest-value tools for multi-disciplinary creatives.

-----

**Total tools:** 130+
**Total verticals:** 6 (3 active, 3 shelved)
**Last sync with sources:** April 26, 2026
**Next review:** When sources change or new tools hit market (weekly check recommended)


---

## Vertical Backlog

# GenLens Vertical Backlog

This file is context for Genny. It keeps possible GenLens expansion areas on deck without activating them in the daily briefing.

## Activation Rule

A discipline qualifies as a GenLens vertical when it has all three:

1. A distinct AI tool stack that is moving fast.
2. A creative technologist audience that self-identifies with the discipline.
3. A workflow with measurable time/cost stages.

Genny must not activate new daily briefing verticals from this backlog unless Jonathan explicitly says to promote one.

## Tier 1: Active Now

These are the only active daily briefing verticals.

1. Product Photography: hard goods, soft goods, lifestyle, presale.
2. AI Filmmaking: VFX, color grading, motion, visual effects.
3. Digital Humans / Synthetic Actors: voice, animation, lip-sync, avatar.

## Tier 2: Deferred

These are approved as on-deck, but deferred until GenLens has enough user demand, roughly 100 users or a clear audience pull.

4. Music Production / Audio: composition, stem separation, mastering, sound design.
5. AI-Accelerated Design / Motion Graphics: Cavalry, Rive, Jitter, Figma, generative layout.
6. Fashion / Apparel / Textile: garment simulation, pattern, fabric generation, trend forecasting.

## Tier 3: Strong Candidates

These are not active. Track as strategic candidates and source-discovery prompts only.

7. Advertising / Brand Content

Fit: high.

Distinct from AI Filmmaking because it centers on 15-30 second commercial production, brand identity systems, campaign asset generation, brief-to-variant workflows, and delivery packages. Relevant tools include Adobe Express, Canva AI, Pencil, Typeface, Jasper-style copy tooling, and campaign production systems. The audience is brand designers, creative directors, agency producers, and in-house creative teams. Strong hiring and budget signal.

Recommended action: add to backlog with revisit triggers. This is likely a strong near-term addition.

8. Architectural Visualization / ArchViz

Fit: high.

Relevant tools include Rhino, SketchUp, Lumion, Enscape, V-Ray, Midjourney, and Stable Diffusion for concept renders. Workflow stages include concept sketch, CAD, material/lighting, render, and post. Distinct from Product Photography because the object is built space: buildings, interiors, environments, and landscape context.

Recommended action: add to backlog with revisit triggers. Validate whether ArchViz practitioners self-identify with the Gen AD / creative technologist frame.

9. Podcast / Long-Form Audio

Fit: medium-high.

Relevant tools include Descript, Adobe Podcast, Riverside, Cleanfeed, iZotope RX, ElevenLabs, transcript editing, voice cloning for pickups, automated show notes, and chapter markers. Distinct from Music Production because the workflow is spoken word, editorial, and distribution-focused.

Recommended action: track first as a sub-vertical under Digital Humans or Music/Audio. Split only if distinct signals justify it.

10. Education / E-Learning Content

Fit: medium-high.

Relevant tools include Synthesia, HeyGen, D-ID, Articulate 360, Rise, and Descript. AI is reducing training-content production cost and time, especially avatar-led and localization-heavy workflows. Audience includes instructional designers, L&D studios, and corporate training producers.

Recommended action: track first as a sub-vertical under Digital Humans. Split only if distinct signals justify it.

11. Social / Short-Form Video

Fit: medium-high.

Relevant tools include CapCut AI, Opus Clip, Descript, Pictory, and Runway. Workflow is speed-first, trend-reactive, template-driven, and different from AI Filmmaking. Audience includes content creators, social media managers, and creator economy operators.

Recommended action: pass unless GenLens data shows clear demand. The intelligence market is saturated.

12. Game Development / Real-Time 3D

Fit: medium.

Relevant tools include Unreal Engine 5, Unity, Godot, Houdini, SpeedTree, procedural generation, NPC AI, and asset generation. Strong AI disruption but already well-served by existing game development media.

Recommended action: keep shelved unless the waitlist shows a significant game development cohort.

## Tier 4: Adjacent Or Probably Wrong Product

13. UX / Product Design

Fit: medium-low.

Relevant tools include Figma AI, Framer, and Webflow. Large audience, but the workflow is wireframe, prototype, handoff, accessibility, and design systems. This may be a separate product rather than GenLens.

14. Screenwriting / Scriptwriting

Fit: medium-low.

Relevant tools include Final Draft, Arc Studio, Fade In, ChatGPT, Claude, and WGA-related AI policy. Mostly text-first and separate from the visual production identity.

15. Spatial Computing / XR

Fit: medium-low.

Relevant areas include Apple Vision Pro, Meta Quest, volumetric video, spatial audio, and 3D UI. Likely early for GenLens.

16. Live Events / Stage Design

Fit: low.

Relevant tools include TouchDesigner, Notch, disguise, and d3. Highly specialized and likely too small for near-term GenLens coverage.

17. Scientific Visualization

Fit: low. Shelved.

Audience is research/data rather than commercial creative technologists.

18. Medical Imaging / Healthcare

Fit: low. Shelved.

Regulated clinical domain. Not GenLens.

## Summary

| # | Vertical | Fit | Status |
|---|---|---|---|
| 1 | Product Photography | Core | Active |
| 2 | AI Filmmaking | Core | Active |
| 3 | Digital Humans / Synthetic Actors | Core | Active |
| 4 | Music Production / Audio | High | Deferred |
| 5 | AI Design / Motion Graphics | High | Deferred |
| 6 | Fashion / Apparel / Textile | Medium-high | Deferred |
| 7 | Advertising / Brand Content | High | Candidate |
| 8 | ArchViz | High | Candidate |
| 9 | Podcast / Long-Form Audio | Medium-high | Candidate |
| 10 | Education / E-Learning | Medium-high | Candidate |
| 11 | Social / Short-Form Video | Medium-high | Candidate |
| 12 | Game Development | Medium | Shelved |
| 13 | UX / Product Design | Medium-low | Probably separate product |
| 14 | Screenwriting | Medium-low | Probably separate product |
| 15 | Spatial Computing / XR | Medium-low | Too early |
| 16 | Live Events / Stage Design | Low | Too niche |
| 17 | Scientific Visualization | Low | Shelved |
| 18 | Medical Imaging | Low | Shelved |

## Near-Term Recommendation

Advertising / Brand Content and ArchViz are the strongest candidates to keep closest to the roadmap. Podcast / Long-Form Audio and Education / E-Learning should be tracked as sub-verticals first. Social / Short-Form Video should stay on watch but not be prioritized without strong demand data.

## Known Uncertainties

- Advertising / Brand Content may partially overlap with AI Filmmaking, especially for 30-second commercial production.
- ArchViz may be culturally closer to AEC than to Gen AD creative technologists.
- Market-size estimates are directional and should be researched before committing roadmap.
- Podcast / Long-Form Audio may belong under Music Production / Audio instead of Digital Humans.
