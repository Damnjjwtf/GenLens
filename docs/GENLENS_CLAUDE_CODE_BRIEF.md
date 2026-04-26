# GENLENS FOR CREATIVES — CLAUDE CODE PROJECT BRIEF
## Paste this entire document into Claude Code to begin building.

---

## PROJECT OVERVIEW

Build **GenLens for Creatives**: a full-stack Vercel SaaS application that serves as daily intelligence for creative technologists doing AI-accelerated visual production (product photography, filmmaking, digital humans/synthetic actors).

**Stack:**
- Framework: Next.js 14 (App Router)
- Database: Neon Postgres (serverless)
- Auth: NextAuth.js (email magic links + invite codes)
- Email: Resend
- AI Synthesis: Anthropic Claude API (claude-sonnet-4-20250514)
- Styling: Tailwind CSS
- Cron: Vercel Cron Jobs
- Deployment: Vercel

**Design aesthetic:** Dark mode by default. High-contrast. Editorial/terminal feel. IBM Plex Mono for UI, Lora for headlines. Accent color: #c8f04a (lime). Secondary accent: #f0a83c (amber). Background: #0e0e0e. Think Bloomberg Terminal meets creative studio.

---

## ARCHITECTURE

```
genlens/
├── app/
│   ├── layout.tsx                    # Root layout (dark mode, fonts, nav)
│   ├── page.tsx                      # Dashboard (main feed)
│   ├── auth/
│   │   ├── signin/page.tsx           # Sign in (magic link)
│   │   └── invite/page.tsx           # Invite code entry
│   ├── settings/page.tsx             # User preferences
│   ├── templates/page.tsx            # Template leaderboard
│   ├── leaderboard/page.tsx          # Creator leaderboard
│   └── api/
│       ├── auth/[...nextauth]/route.ts
│       ├── cron/
│       │   └── daily-scrape/route.ts          # Vercel Cron: scrape all sources
│       │   └── daily-brief/route.ts           # Vercel Cron: synthesize + email
│       ├── feeds/
│       │   └── all/route.ts                   # GET: return all cached signals
│       │   └── scrape/route.ts                # POST: trigger manual scrape
│       ├── synthesis/
│       │   └── briefing/route.ts              # POST: generate daily briefing
│       │   └── social/route.ts                # POST: generate X/LinkedIn drafts
│       │   └── keynote/route.ts               # POST: generate keynote talking points
│       ├── settings/route.ts                  # GET/POST: user preferences
│       ├── subscribers/route.ts               # GET/POST: subscriber management
│       └── templates/route.ts                 # GET: template leaderboard data
├── lib/
│   ├── db.ts                         # Neon client + all queries
│   ├── auth.ts                       # NextAuth config
│   ├── scraper/
│   │   ├── index.ts                  # Orchestrator: runs all scrapers
│   │   ├── rss.ts                    # Generic RSS fetcher
│   │   ├── github.ts                 # GitHub API scraper
│   │   ├── hn.ts                     # HN Algolia scraper
│   │   ├── arxiv.ts                  # arXiv API scraper
│   │   ├── youtube.ts                # YouTube RSS scraper
│   │   ├── reddit.ts                 # Reddit RSS scraper
│   │   ├── behance.ts                # Behance API scraper
│   │   ├── producthunt.ts            # Product Hunt GraphQL scraper
│   │   ├── twitter.ts                # Twitter/X scraper (web search fallback)
│   │   ├── patent.ts                 # USPTO patent scraper
│   │   ├── html.ts                   # Generic HTML blog scraper
│   │   └── sources.ts                # Master source list (125+ sources)
│   ├── taxonomy.ts                   # Signal classification engine
│   ├── dedup.ts                      # Deduplication engine
│   ├── synthesis.ts                  # Claude synthesis (briefings, social, keynote)
│   ├── email.ts                      # Resend email templates
│   └── constants.ts                  # Enums, types, config
├── components/
│   ├── Dashboard.tsx                 # Main feed component
│   ├── SignalCard.tsx                # Individual signal card
│   ├── VerticalToggle.tsx            # Product Photo | Filmmaking | Digital Humans
│   ├── DimensionFilter.tsx           # Filter by dimension (1-10)
│   ├── WorkflowStageView.tsx         # Drill into specific workflow stage
│   ├── TemplateLeaderboard.tsx       # Top templates ranked
│   ├── CreatorLeaderboard.tsx        # Top creators ranked
│   ├── CostTimeDelta.tsx             # Savings visualization
│   ├── TrendSignals.tsx              # Cultural/aesthetic trends
│   ├── LegalAlerts.tsx               # Regulatory/IP signals
│   ├── HiringSignals.tsx             # Talent market view
│   ├── IntegrationMatrix.tsx         # Pipeline compatibility
│   ├── Sidebar.tsx                   # Source status, stats, quick nav
│   ├── SettingsPanel.tsx             # User preferences
│   ├── SocialDrafts.tsx              # X/LinkedIn draft viewer
│   └── KeynoteOutput.tsx             # Keynote talking points viewer
└── vercel.json                       # Cron config
```

---

## DATABASE SCHEMA (NEON POSTGRES)

```sql
-- ═══════════════════════════════════════════════════════════
-- CORE TABLES
-- ═══════════════════════════════════════════════════════════

-- Users (NextAuth)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  image TEXT,
  role VARCHAR DEFAULT 'user', -- user, admin, subscriber
  invite_code_used TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  type VARCHAR NOT NULL,
  provider VARCHAR NOT NULL,
  provider_account_id VARCHAR NOT NULL,
  refresh_token TEXT,
  access_token TEXT,
  expires_at INT,
  token_type VARCHAR,
  scope VARCHAR,
  id_token TEXT,
  session_state VARCHAR
);

CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_token TEXT UNIQUE NOT NULL,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  expires TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE verification_tokens (
  identifier TEXT NOT NULL,
  token TEXT UNIQUE NOT NULL,
  expires TIMESTAMP WITH TIME ZONE NOT NULL,
  PRIMARY KEY (identifier, token)
);

CREATE TABLE invite_codes (
  id SERIAL PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  max_uses INT DEFAULT 50,
  uses INT DEFAULT 0,
  created_by UUID REFERENCES users(id),
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════
-- SIGNALS (unified table for ALL intelligence)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE signals (
  id SERIAL PRIMARY KEY,
  
  -- Classification
  vertical VARCHAR NOT NULL, -- product_photography, filmmaking, digital_humans
  dimension INT NOT NULL, -- 1-10
  signal_type VARCHAR NOT NULL, -- tool_release, competitive_move, template, benchmark, trend, hiring, legal, integration, aesthetic, leaderboard
  
  -- Content
  title TEXT NOT NULL,
  description TEXT,
  summary TEXT, -- Claude-generated summary
  raw_content TEXT, -- Original scraped content
  
  -- Taxonomy tags
  workflow_stages TEXT[], -- sketch, cad, render, composite, video, presale, character_design, voice_gen, animation, lip_sync, scene_comp, color_grade, concept, preproduction, shooting, vfx, sound_design
  product_categories TEXT[], -- hard_goods, soft_goods, hybrid, accessories, commercial_spot, music_video, short_film, feature, documentary, educational, synthetic_film, hybrid_film, talking_head, animation_2d, animation_3d, deepfake_ethical, voiceover
  tool_names TEXT[], -- figma_weave, keyshot, flux, elevenlabs, d_id, synthesia, runway, luma, sora, descript, heygen, midjourney, stable_diffusion, comfyui, claid, photoroom, blender, unreal, davinci_resolve, after_effects, nuke, clo3d, marvelous_designer, adobe_firefly, substance_3d, etc.
  
  -- Impact metrics
  time_saved_hours DECIMAL,
  cost_saved_dollars DECIMAL,
  quality_improvement_percent DECIMAL,
  learning_curve_hours DECIMAL,
  
  -- Source
  source_url TEXT,
  source_platform VARCHAR, -- rss, github, hn, arxiv, youtube, reddit, behance, twitter, producthunt, blog, patent, linkedin, instagram, tiktok
  source_name TEXT, -- Human-readable source name
  
  -- Engagement / trending
  trending_score INT DEFAULT 0, -- 0-100
  engagement_count INT DEFAULT 0, -- likes, stars, upvotes combined
  
  -- Dedup
  content_hash TEXT UNIQUE, -- For deduplication
  
  -- Dates
  published_at TIMESTAMP WITH TIME ZONE,
  scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Status
  status VARCHAR DEFAULT 'raw' -- raw, classified, synthesized, published, archived
);

CREATE INDEX idx_signals_vertical ON signals(vertical);
CREATE INDEX idx_signals_dimension ON signals(dimension);
CREATE INDEX idx_signals_signal_type ON signals(signal_type);
CREATE INDEX idx_signals_status ON signals(status);
CREATE INDEX idx_signals_created ON signals(created_at DESC);
CREATE INDEX idx_signals_hash ON signals(content_hash);

-- ═══════════════════════════════════════════════════════════
-- TEMPLATES (indexed workflow templates from community)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE templates (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  
  -- Classification
  vertical VARCHAR NOT NULL,
  product_category VARCHAR,
  workflow_stages TEXT[],
  tool_stack TEXT[],
  
  -- Metrics
  total_time_hours DECIMAL,
  estimated_cost_dollars DECIMAL,
  time_breakdown JSONB, -- {"sketch": 2, "cad": 4, "render": 2, "composite": 1}
  quality_rating DECIMAL, -- 0-100 (community rated or estimated)
  
  -- Source
  source_platform VARCHAR, -- figma_weave, github, youtube, reddit, medium, behance, gumroad
  source_url TEXT,
  creator_name TEXT,
  creator_handle TEXT,
  creator_url TEXT,
  
  -- Trending
  trending_score INT DEFAULT 0,
  community_engagement INT DEFAULT 0, -- forks + likes + views combined
  adoption_count INT DEFAULT 0, -- estimated number of creatives using
  
  -- Content
  content_hash TEXT UNIQUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════
-- CREATORS (leaderboard tracking)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE creators (
  id SERIAL PRIMARY KEY,
  handle TEXT NOT NULL,
  name TEXT,
  platform VARCHAR NOT NULL, -- instagram, behance, youtube, twitter, portfolio
  profile_url TEXT,
  
  -- Classification
  specialty TEXT, -- hard_goods, soft_goods, synthetic_actors, voice, etc.
  verticals TEXT[],
  tool_stack TEXT[],
  
  -- Metrics
  follower_count INT,
  engagement_rate DECIMAL,
  production_speed_hours DECIMAL,
  commercial_clients INT,
  
  -- Ranking
  leaderboard_score INT DEFAULT 0, -- composite score
  leaderboard_rank INT,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  UNIQUE(handle, platform)
);

-- ═══════════════════════════════════════════════════════════
-- COMPETITORS (competitive intelligence)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE competitors (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  industry VARCHAR, -- retail, production, agency, brand
  website TEXT,
  product_categories TEXT[],
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE competitor_moves (
  id SERIAL PRIMARY KEY,
  competitor_id INT REFERENCES competitors(id),
  move_type VARCHAR, -- product_launch, tool_adoption, process_change, partnership, hiring, patent
  title TEXT NOT NULL,
  description TEXT,
  product_categories TEXT[],
  workflow_stages_affected TEXT[],
  source_url TEXT,
  relevance_score INT DEFAULT 50, -- 0-100
  announced_date DATE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════
-- GENERATED OUTPUTS
-- ═══════════════════════════════════════════════════════════

CREATE TABLE briefings (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  vertical VARCHAR,
  briefing_type VARCHAR DEFAULT 'daily', -- daily, weekly, custom
  
  -- Content
  ticker TEXT, -- Wire headline
  synthesis TEXT, -- Full briefing narrative
  signal_ids INT[], -- Which signals were included
  template_ids INT[], -- Which templates were highlighted
  
  -- Outputs
  email_html TEXT,
  x_draft TEXT,
  linkedin_draft TEXT,
  keynote_notes TEXT,
  
  -- Delivery
  sent_at TIMESTAMP WITH TIME ZONE,
  recipient_count INT DEFAULT 0,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════
-- USER PREFERENCES
-- ═══════════════════════════════════════════════════════════

CREATE TABLE user_preferences (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  
  -- Verticals
  active_verticals TEXT[] DEFAULT ARRAY['product_photography', 'filmmaking', 'digital_humans'],
  
  -- Focus areas
  workflow_stage_focus TEXT[], -- Which stages they care about most
  product_categories_focus TEXT[],
  tools_tracking TEXT[], -- Specific tools they want to follow
  competitors_watching TEXT[], -- Competitor names
  
  -- Delivery
  delivery_frequency VARCHAR DEFAULT 'daily', -- daily, weekly
  delivery_time TIME DEFAULT '08:00',
  delivery_timezone VARCHAR DEFAULT 'America/New_York',
  output_formats TEXT[] DEFAULT ARRAY['email', 'dashboard'], -- email, slack, dashboard
  
  -- Display
  dimensions_visible INT[] DEFAULT ARRAY[1,2,3,4,5,6,7,8,9,10],
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════
-- SUBSCRIBERS (email list)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE subscribers (
  id SERIAL PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  active BOOLEAN DEFAULT true,
  user_id UUID REFERENCES users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════
-- OPERATIONAL
-- ═══════════════════════════════════════════════════════════

CREATE TABLE scrape_log (
  id SERIAL PRIMARY KEY,
  source_name TEXT NOT NULL,
  source_url TEXT,
  status VARCHAR, -- success, error, timeout, rate_limited
  signals_found INT DEFAULT 0,
  signals_new INT DEFAULT 0,
  error_message TEXT,
  duration_ms INT,
  scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE cache (
  source TEXT PRIMARY KEY,
  data TEXT NOT NULL,
  fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## MASTER SOURCE LIST (125+ SOURCES)

Build each source as a module in `lib/scraper/sources.ts`. Each source entry should include: name, url, type (rss | api | html | github | graphql), vertical(s), dimension(s), scrape_interval (hours), and a parse function.

### DIMENSION 1: WORKFLOW STAGE SIGNALS (20 sources)

```typescript
// Tool blogs and release feeds
{ name: "KeyShot Blog", url: "https://www.keyshot.com/blog/feed/", type: "rss", verticals: ["product_photography"], dimensions: [1, 2, 5] },
{ name: "Adobe Blog", url: "https://blog.adobe.com/en/publish/rss", type: "rss", verticals: ["product_photography", "filmmaking"], dimensions: [1, 5, 8] },
{ name: "Black Forest Labs / FLUX", url: "https://bfl.ai/blog", type: "html", verticals: ["product_photography", "digital_humans"], dimensions: [1, 5] },
{ name: "Beeble AI Blog", url: "https://beeble.ai/blog", type: "html", verticals: ["product_photography", "filmmaking"], dimensions: [1, 5] },
{ name: "fal.ai Blog", url: "https://fal.ai/blog", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [1, 8] },
{ name: "OpenAI Blog", url: "https://openai.com/blog/rss.xml", type: "rss", verticals: ["filmmaking", "digital_humans"], dimensions: [1, 5, 6] },
{ name: "Google AI Blog", url: "https://blog.google/technology/ai/rss/", type: "rss", verticals: ["filmmaking", "digital_humans"], dimensions: [1, 5] },
{ name: "Anthropic Blog", url: "https://www.anthropic.com/blog/rss.xml", type: "rss", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [1] },
{ name: "ElevenLabs Blog", url: "https://elevenlabs.io/blog", type: "html", verticals: ["digital_humans", "filmmaking"], dimensions: [1, 2, 5, 7] },
{ name: "D-ID Blog", url: "https://www.d-id.com/blog/", type: "html", verticals: ["digital_humans", "filmmaking"], dimensions: [1, 2, 5] },
{ name: "Synthesia Blog", url: "https://www.synthesia.io/blog", type: "html", verticals: ["digital_humans"], dimensions: [1, 2, 5, 7] },
{ name: "Runway Blog", url: "https://runwayml.com/blog/", type: "html", verticals: ["filmmaking", "digital_humans"], dimensions: [1, 5] },
{ name: "Luma AI Blog", url: "https://lumalabs.ai/blog", type: "html", verticals: ["filmmaking", "product_photography"], dimensions: [1, 5] },
{ name: "Descript Blog", url: "https://www.descript.com/blog", type: "html", verticals: ["filmmaking", "digital_humans"], dimensions: [1, 5, 8] },
{ name: "HeyGen Blog", url: "https://www.heygen.com/blog", type: "html", verticals: ["digital_humans"], dimensions: [1, 5] },
{ name: "Figma Blog", url: "https://www.figma.com/blog/rss.xml", type: "rss", verticals: ["product_photography"], dimensions: [1, 4, 8] },
{ name: "ComfyUI Releases", url: "https://github.com/Comfy-Org/ComfyUI/releases.atom", type: "rss", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [1, 8] },
{ name: "Blender Release Notes", url: "https://developer.blender.org/", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [1, 8] },
{ name: "Unreal Engine Blog", url: "https://www.unrealengine.com/en-US/feed", type: "rss", verticals: ["filmmaking", "digital_humans"], dimensions: [1, 5, 8] },
{ name: "DaVinci Resolve Updates", url: "https://www.blackmagicdesign.com/products/davinciresolve", type: "html", verticals: ["filmmaking"], dimensions: [1, 5] },
```

### DIMENSION 2: PRODUCT CATEGORY DEEP DIVE (15 sources)

```typescript
{ name: "Figma Weave Community", url: "https://www.figma.com/community/weave", type: "html", verticals: ["product_photography"], dimensions: [2, 4] },
{ name: "Behance Product Photography", url: "https://www.behance.net/search/projects?field=photography&search=product+photography", type: "html", verticals: ["product_photography"], dimensions: [2, 9, 10] },
{ name: "ArtStation Character Design", url: "https://www.artstation.com/channels/character_design", type: "html", verticals: ["digital_humans"], dimensions: [2, 9, 10] },
{ name: "Substance 3D Community", url: "https://substance3d.adobe.com/community-assets", type: "html", verticals: ["product_photography"], dimensions: [2, 8] },
{ name: "CLO3D Blog", url: "https://www.clo3d.com/blog", type: "html", verticals: ["product_photography"], dimensions: [2, 1] },
{ name: "Marvelous Designer Updates", url: "https://www.marvelousdesigner.com/", type: "html", verticals: ["product_photography"], dimensions: [2, 1] },
{ name: "Core77 (Product Design)", url: "https://www.core77.com/rss", type: "rss", verticals: ["product_photography"], dimensions: [2, 9] },
{ name: "Design Observer", url: "https://designobserver.com/rss", type: "rss", verticals: ["product_photography"], dimensions: [2, 9] },
{ name: "It's Nice That", url: "https://www.itsnicethat.com/rss", type: "rss", verticals: ["product_photography", "filmmaking"], dimensions: [2, 9] },
{ name: "Pinterest Trends", url: "https://trends.pinterest.com/", type: "html", verticals: ["product_photography"], dimensions: [2, 9] },
{ name: "Claid AI Blog", url: "https://claid.ai/blog", type: "html", verticals: ["product_photography"], dimensions: [2, 1, 5] },
{ name: "Photoroom Blog", url: "https://www.photoroom.com/blog", type: "html", verticals: ["product_photography"], dimensions: [2, 1, 5] },
{ name: "Flair AI Blog", url: "https://flair.ai/blog", type: "html", verticals: ["product_photography"], dimensions: [2, 1] },
{ name: "Pebblely Blog", url: "https://www.pebblely.com/blog", type: "html", verticals: ["product_photography"], dimensions: [2, 1] },
{ name: "Fashion AI Tools Blog", url: "https://fashionai.tools/blog", type: "html", verticals: ["product_photography"], dimensions: [2, 9] },
```

### DIMENSION 3: COMPETITIVE INTELLIGENCE (18 sources)

```typescript
{ name: "Behance Trending", url: "https://www.behance.net/galleries", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [3, 9, 10] },
{ name: "TechCrunch Retail AI", url: "https://techcrunch.com/tag/retail-ai/feed/", type: "rss", verticals: ["product_photography"], dimensions: [3] },
{ name: "VentureBeat AI", url: "https://venturebeat.com/category/ai/feed/", type: "rss", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [3] },
{ name: "Retail Dive", url: "https://www.retaildive.com/feeds/news/", type: "rss", verticals: ["product_photography"], dimensions: [3] },
{ name: "Digiday", url: "https://digiday.com/feed/", type: "rss", verticals: ["product_photography", "filmmaking"], dimensions: [3] },
{ name: "No Film School", url: "https://nofilmschool.com/rss.xml", type: "rss", verticals: ["filmmaking", "digital_humans"], dimensions: [3, 1, 9] },
{ name: "Motionographer", url: "https://motionographer.com/feed/", type: "rss", verticals: ["filmmaking"], dimensions: [3, 9] },
{ name: "CineD", url: "https://www.cined.com/feed/", type: "rss", verticals: ["filmmaking"], dimensions: [3, 1, 5] },
{ name: "NVIDIA Blog", url: "https://blogs.nvidia.com/feed/", type: "rss", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [3, 1, 5] },
{ name: "Shopify Blog (E-commerce)", url: "https://www.shopify.com/blog/rss", type: "rss", verticals: ["product_photography"], dimensions: [3, 5] },
{ name: "IKEA Press", url: "https://www.ikea.com/global/en/newsroom/", type: "html", verticals: ["product_photography"], dimensions: [3] },
{ name: "Wayfair Blog", url: "https://www.aboutwayfair.com/blog", type: "html", verticals: ["product_photography"], dimensions: [3] },
{ name: "Target Corporate", url: "https://corporate.target.com/news-features", type: "html", verticals: ["product_photography"], dimensions: [3] },
{ name: "Williams Sonoma Press", url: "https://www.williams-sonomainc.com/news/", type: "html", verticals: ["product_photography"], dimensions: [3] },
{ name: "Crunchbase AI Retail", url: "https://www.crunchbase.com/discover/funding_rounds", type: "api", verticals: ["product_photography"], dimensions: [3] },
{ name: "Sundance Film Festival", url: "https://www.sundance.org/blogs", type: "html", verticals: ["filmmaking", "digital_humans"], dimensions: [3, 10] },
{ name: "SXSW Film", url: "https://www.sxsw.com/film/", type: "html", verticals: ["filmmaking", "digital_humans"], dimensions: [3, 10] },
{ name: "NAB Show", url: "https://www.nabshow.com/news", type: "html", verticals: ["filmmaking"], dimensions: [3] },
```

### DIMENSION 4: TEMPLATE LIBRARY (12 sources)

```typescript
{ name: "Figma Weave Community Templates", url: "https://www.figma.com/community/weave", type: "html", verticals: ["product_photography"], dimensions: [4, 2] },
{ name: "GitHub ComfyUI Workflows", url: "https://api.github.com/search/repositories?q=comfyui+workflow&sort=stars&order=desc", type: "api", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [4, 8] },
{ name: "GitHub SD Workflows", url: "https://api.github.com/search/repositories?q=stable-diffusion+workflow&sort=stars&order=desc", type: "api", verticals: ["product_photography", "digital_humans"], dimensions: [4, 8] },
{ name: "GitHub AI Filmmaking", url: "https://api.github.com/search/repositories?q=ai+filmmaking+OR+ai+video&sort=stars&order=desc", type: "api", verticals: ["filmmaking", "digital_humans"], dimensions: [4] },
{ name: "Reddit r/StableDiffusion", url: "https://www.reddit.com/r/StableDiffusion/top/.json?t=week", type: "api", verticals: ["product_photography", "digital_humans"], dimensions: [4, 1, 9] },
{ name: "Reddit r/productphotography", url: "https://www.reddit.com/r/productphotography/top/.json?t=week", type: "api", verticals: ["product_photography"], dimensions: [4, 2, 9] },
{ name: "Reddit r/videography", url: "https://www.reddit.com/r/videography/top/.json?t=week", type: "api", verticals: ["filmmaking"], dimensions: [4, 1] },
{ name: "Reddit r/filmmakers", url: "https://www.reddit.com/r/Filmmakers/top/.json?t=week", type: "api", verticals: ["filmmaking"], dimensions: [4, 1] },
{ name: "Reddit r/vfx", url: "https://www.reddit.com/r/vfx/top/.json?t=week", type: "api", verticals: ["filmmaking"], dimensions: [4, 1] },
{ name: "Reddit r/cinematography", url: "https://www.reddit.com/r/cinematography/top/.json?t=week", type: "api", verticals: ["filmmaking"], dimensions: [4, 1] },
{ name: "Reddit r/DigitalArt", url: "https://www.reddit.com/r/DigitalArt/top/.json?t=week", type: "api", verticals: ["digital_humans", "product_photography"], dimensions: [4, 9] },
{ name: "Gumroad AI Workflows", url: "https://gumroad.com/discover?query=ai+workflow", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [4] },
```

### DIMENSION 5: COST & TIME DELTA (10 sources)

```typescript
{ name: "CineD Benchmarks", url: "https://www.cined.com/feed/", type: "rss", verticals: ["filmmaking"], dimensions: [5, 1] },
{ name: "NVIDIA Forums GPU", url: "https://forums.developer.nvidia.com/", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [5] },
{ name: "Reddit r/LocalLLaMA", url: "https://www.reddit.com/r/LocalLLaMA/top/.json?t=week", type: "api", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [5, 1] },
{ name: "Tom's Hardware AI Benchmarks", url: "https://www.tomshardware.com/tag/artificial-intelligence", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [5] },
{ name: "Replicate Blog", url: "https://replicate.com/blog", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [5, 1, 8] },
{ name: "Civitai Trending Models", url: "https://civitai.com/api/v1/models?sort=Most+Downloaded&period=Week", type: "api", verticals: ["product_photography", "digital_humans"], dimensions: [5, 1, 4] },
{ name: "Replicate Trending Models", url: "https://replicate.com/explore", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [5, 1] },
{ name: "Hugging Face Trending", url: "https://huggingface.co/api/trending", type: "api", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [5, 1] },
{ name: "WooCommerce Blog", url: "https://woocommerce.com/blog/feed/", type: "rss", verticals: ["product_photography"], dimensions: [5, 3] },
{ name: "Shopify Editions", url: "https://www.shopify.com/editions", type: "html", verticals: ["product_photography"], dimensions: [5, 3] },
```

### DIMENSION 6: REGULATORY / IP / ETHICAL (12 sources)

```typescript
{ name: "SAG-AFTRA News", url: "https://www.sagaftra.org/news", type: "html", verticals: ["filmmaking", "digital_humans"], dimensions: [6] },
{ name: "FTC AI Announcements", url: "https://www.ftc.gov/news-events/topics/artificial-intelligence", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [6] },
{ name: "EFF AI Coverage", url: "https://www.eff.org/issues/ai", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [6] },
{ name: "USPTO Patent Search AI", url: "https://patft.uspto.gov/", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [6, 3] },
{ name: "Google Patents AI", url: "https://patents.google.com/?q=artificial+intelligence+product+photography&oq=artificial+intelligence+product+photography", type: "html", verticals: ["product_photography"], dimensions: [6, 3] },
{ name: "Ars Technica AI Legal", url: "https://arstechnica.com/tag/ai/feed/", type: "rss", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [6] },
{ name: "The Verge AI Policy", url: "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", type: "rss", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [6, 1] },
{ name: "Wired AI Ethics", url: "https://www.wired.com/tag/artificial-intelligence/feed/rss", type: "rss", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [6] },
{ name: "Copyright Alliance", url: "https://copyrightalliance.org/trending-topics/artificial-intelligence/", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [6] },
{ name: "AI and Media Law Blog", url: "https://www.lexology.com/search?q=AI+copyright&ct=articles", type: "html", verticals: ["filmmaking", "digital_humans"], dimensions: [6] },
{ name: "Creative Commons AI", url: "https://creativecommons.org/tag/artificial-intelligence/", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [6] },
{ name: "Reddit r/AIethics", url: "https://www.reddit.com/r/AIethics/top/.json?t=week", type: "api", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [6] },
```

### DIMENSION 7: TALENT + HIRING (8 sources)

```typescript
{ name: "LinkedIn Jobs AI Creative", url: "https://www.linkedin.com/jobs/search/?keywords=AI+product+photography", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [7] },
{ name: "Upwork AI Skills", url: "https://www.upwork.com/freelance-jobs/ai-product-photography/", type: "html", verticals: ["product_photography", "digital_humans"], dimensions: [7] },
{ name: "Fiverr AI Gigs", url: "https://www.fiverr.com/search/gigs?query=ai+product+photography", type: "html", verticals: ["product_photography", "digital_humans"], dimensions: [7] },
{ name: "Indeed AI Creative Jobs", url: "use_indeed_mcp", type: "mcp", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [7] },
{ name: "Skillshare AI Courses", url: "https://www.skillshare.com/search?query=ai+filmmaking", type: "html", verticals: ["filmmaking", "digital_humans"], dimensions: [7] },
{ name: "LinkedIn Learning AI", url: "https://www.linkedin.com/learning/search?keywords=AI+filmmaking", type: "html", verticals: ["filmmaking", "digital_humans"], dimensions: [7] },
{ name: "Coursera AI Creative", url: "https://www.coursera.org/search?query=ai+filmmaking", type: "html", verticals: ["filmmaking", "digital_humans"], dimensions: [7] },
{ name: "Glassdoor AI Creative Salaries", url: "https://www.glassdoor.com/Salaries/ai-product-photographer-salary", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [7] },
```

### DIMENSION 8: INTEGRATION + COMPATIBILITY (8 sources)

```typescript
{ name: "Figma Plugin Marketplace", url: "https://www.figma.com/community/plugins", type: "html", verticals: ["product_photography"], dimensions: [8] },
{ name: "Adobe Exchange", url: "https://exchange.adobe.com/", type: "html", verticals: ["product_photography", "filmmaking"], dimensions: [8] },
{ name: "Blender Add-ons", url: "https://extensions.blender.org/", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [8] },
{ name: "Unreal Marketplace", url: "https://www.unrealengine.com/marketplace/en-US/store", type: "html", verticals: ["filmmaking", "digital_humans"], dimensions: [8] },
{ name: "GitHub API Releases AI Tools", url: "https://api.github.com/search/repositories?q=ai+plugin+integration&sort=updated", type: "api", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [8] },
{ name: "Replicate API Models", url: "https://replicate.com/explore", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [8, 1] },
{ name: "fal.ai Models", url: "https://fal.ai/models", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [8, 1] },
{ name: "DaVinci Resolve Plugins", url: "https://www.blackmagicdesign.com/products/davinciresolve/plugins", type: "html", verticals: ["filmmaking"], dimensions: [8] },
```

### DIMENSION 9: CULTURAL / TREND SIGNALS (12 sources)

```typescript
{ name: "Behance Photography Trending", url: "https://www.behance.net/galleries/photography", type: "html", verticals: ["product_photography"], dimensions: [9, 3] },
{ name: "Behance Motion Trending", url: "https://www.behance.net/galleries/motion", type: "html", verticals: ["filmmaking"], dimensions: [9, 3] },
{ name: "Dribbble Trending", url: "https://dribbble.com/shots/popular", type: "html", verticals: ["product_photography"], dimensions: [9] },
{ name: "Instagram #AIFilmmaking", url: "web_search_fallback", type: "search", verticals: ["filmmaking", "digital_humans"], dimensions: [9] },
{ name: "Instagram #AIProductPhotography", url: "web_search_fallback", type: "search", verticals: ["product_photography"], dimensions: [9] },
{ name: "Instagram #SyntheticActors", url: "web_search_fallback", type: "search", verticals: ["digital_humans"], dimensions: [9] },
{ name: "TikTok AI Trends", url: "web_search_fallback", type: "search", verticals: ["filmmaking", "digital_humans"], dimensions: [9] },
{ name: "It's Nice That", url: "https://www.itsnicethat.com/rss", type: "rss", verticals: ["product_photography", "filmmaking"], dimensions: [9] },
{ name: "Design Observer", url: "https://designobserver.com/rss", type: "rss", verticals: ["product_photography"], dimensions: [9] },
{ name: "Prolost (Stu Maschwitz)", url: "https://prolost.com/feed", type: "rss", verticals: ["filmmaking"], dimensions: [9, 1] },
{ name: "Stills Magazine", url: "https://www.stillsmagazine.com/", type: "html", verticals: ["product_photography"], dimensions: [9] },
{ name: "Colossal Art Blog", url: "https://www.thisiscolossal.com/feed/", type: "rss", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [9] },
```

### DIMENSION 10: BENCHMARK + LEADERBOARD (10 sources)

```typescript
{ name: "Behance Commercial Projects", url: "https://www.behance.net/search/projects?field=advertising", type: "html", verticals: ["product_photography", "filmmaking"], dimensions: [10, 3] },
{ name: "ArtStation AI Art", url: "https://www.artstation.com/channels/ai_art", type: "html", verticals: ["digital_humans", "product_photography"], dimensions: [10, 9] },
{ name: "GitHub Stars Tracking AI", url: "https://api.github.com/search/repositories?q=ai+product+photography+OR+ai+filmmaking&sort=stars", type: "api", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [10, 4] },
{ name: "YouTube AI Filmmaking Creators", url: "web_search_fallback", type: "search", verticals: ["filmmaking", "digital_humans"], dimensions: [10] },
{ name: "Corridor Crew YouTube", url: "https://www.youtube.com/feeds/videos.xml?channel_id=UCSpFnDQr88xCZ80N-X7t0nQ", type: "rss", verticals: ["filmmaking", "digital_humans"], dimensions: [10, 1, 9] },
{ name: "Peter McKinnon YouTube", url: "https://www.youtube.com/feeds/videos.xml?channel_id=UC3DkFux8Iv-aYnTRWzwaiBA", type: "rss", verticals: ["product_photography", "filmmaking"], dimensions: [10, 9] },
{ name: "Daniel Schiffer YouTube", url: "https://www.youtube.com/feeds/videos.xml?channel_id=UCwUH9hrqQ-wg12DXNI5TBuQ", type: "rss", verticals: ["product_photography"], dimensions: [10, 9] },
{ name: "Potato Jet YouTube", url: "https://www.youtube.com/feeds/videos.xml?channel_id=UCYfMWYFKOhYaLKMUiNPVDcA", type: "rss", verticals: ["filmmaking"], dimensions: [10, 1] },
{ name: "Hugh Hou YouTube", url: "https://www.youtube.com/feeds/videos.xml?channel_id=UCyg6bkMj4MmnAKxJh79CUww", type: "rss", verticals: ["filmmaking"], dimensions: [10, 1] },
{ name: "AI Explained YouTube", url: "https://www.youtube.com/feeds/videos.xml?channel_id=UCNJ1Ymd5yFuUPtn21xtRbbw", type: "rss", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [10, 1] },
```

### ADDITIONAL SOURCES: BUILDER BRIEF CROSSOVER (10 sources)

```typescript
// These feed both GenLens AND the original Builder Brief
{ name: "Hacker News AI", url: "https://hn.algolia.com/api/v1/search?query=AI&tags=story&hitsPerPage=20", type: "api", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [1, 3, 5] },
{ name: "arXiv CS.AI", url: "https://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CV+OR+cat:cs.GR&sortBy=submittedDate&sortOrder=descending&max_results=15", type: "api", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [1, 5] },
{ name: "Product Hunt", url: "https://api.producthunt.com/v2/api/graphql", type: "graphql", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [1, 3] },
{ name: "GitHub Trending AI/ML", url: "https://api.github.com/search/repositories?q=topic:artificial-intelligence&sort=stars&order=desc&per_page=15", type: "api", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [1, 4] },
{ name: "Hugging Face Papers", url: "https://huggingface.co/papers", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [1, 5] },
{ name: "News.smol.ai", url: "https://news.smol.ai/", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [1, 3] },
{ name: "The Rundown AI", url: "https://www.therundown.ai/", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [1, 3] },
{ name: "Import AI", url: "https://importai.substack.com/feed", type: "rss", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [1, 5] },
{ name: "Deep Learning Weekly", url: "https://www.deeplearningweekly.com/", type: "html", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [1, 5] },
{ name: "Last Week in AI", url: "https://lastweekin.ai/feed", type: "rss", verticals: ["product_photography", "filmmaking", "digital_humans"], dimensions: [1, 3] },
```

### TWITTER/X VOICES (25 accounts)

```typescript
// Use Claude web search as fallback since Twitter API requires auth
// Search pattern: "from:@handle" + AI-related keywords
const TWITTER_VOICES = [
  // Builder Brief voices
  "@karpathy", "@simonw", "@_philschmid", "@drjimfan", "@aiatmeta",
  "@ai_pub", "@percyliang", "@janleike", "@polynoamial", "@lilianweng",
  "@swyx", "@levie", "@rez0__", "@sama", "@dariogamino",
  "@alexalbert__", "@miramurati",
  // GenLens production voices
  "@runwayml", "@lumalabsai", "@klingai", "@soravideosai",
  "@nickfluder", "@nolanmorse", "@corridorcrew", "@ThisIsKp", "@chazwick"
];
```

### ADDITIONAL SOURCES: MOTION CAPTURE + ANIMATION (5 sources)

```typescript
{ name: "Cascable Blog", url: "https://cascable.se/blog/", type: "html", verticals: ["filmmaking", "digital_humans"], dimensions: [1, 2] },
{ name: "Move.ai Blog", url: "https://www.move.ai/blog", type: "html", verticals: ["filmmaking", "digital_humans"], dimensions: [1, 2, 5] },
{ name: "Rokoko Blog", url: "https://www.rokoko.com/blog", type: "html", verticals: ["filmmaking", "digital_humans"], dimensions: [1, 2, 5] },
{ name: "DeepMotion Blog", url: "https://www.deepmotion.com/blog", type: "html", verticals: ["filmmaking", "digital_humans"], dimensions: [1, 2] },
{ name: "Radical Motion Blog", url: "https://radicalmotion.com/blog", type: "html", verticals: ["filmmaking", "digital_humans"], dimensions: [1, 2, 5] },
```

### ADDITIONAL SOURCES: VOICE + AUDIO (5 sources)

```typescript
{ name: "ElevenLabs Changelog", url: "https://elevenlabs.io/changelog", type: "html", verticals: ["digital_humans", "filmmaking"], dimensions: [1, 5, 8] },
{ name: "Resemble AI Blog", url: "https://www.resemble.ai/blog", type: "html", verticals: ["digital_humans", "filmmaking"], dimensions: [1, 5] },
{ name: "Coqui TTS GitHub", url: "https://github.com/coqui-ai/TTS/releases.atom", type: "rss", verticals: ["digital_humans"], dimensions: [1, 4] },
{ name: "Bark AI GitHub", url: "https://github.com/suno-ai/bark/releases.atom", type: "rss", verticals: ["digital_humans"], dimensions: [1, 4] },
{ name: "Tortoise TTS GitHub", url: "https://github.com/neonbjb/tortoise-tts/releases.atom", type: "rss", verticals: ["digital_humans"], dimensions: [1, 4] },
```

### ADDITIONAL SOURCES: IMAGE/VIDEO GENERATION (5 sources)

```typescript
{ name: "Midjourney Updates", url: "web_search_fallback", type: "search", verticals: ["product_photography", "digital_humans"], dimensions: [1, 5, 9] },
{ name: "Stable Diffusion Releases", url: "https://github.com/Stability-AI/stablediffusion/releases.atom", type: "rss", verticals: ["product_photography", "digital_humans"], dimensions: [1, 4] },
{ name: "ControlNet Releases", url: "https://github.com/lllyasviel/ControlNet/releases.atom", type: "rss", verticals: ["product_photography", "digital_humans"], dimensions: [1, 4, 8] },
{ name: "Deforum Releases", url: "https://github.com/deforum-art/deforum-stable-diffusion/releases.atom", type: "rss", verticals: ["filmmaking"], dimensions: [1, 4] },
{ name: "Kling AI Blog", url: "https://klingai.com/blog", type: "html", verticals: ["filmmaking", "digital_humans"], dimensions: [1, 5] },
```

---

**TOTAL SOURCES: 130**

---

## SYNTHESIS PROMPTS

### Daily Briefing Synthesis

For each vertical, Claude receives all signals from the last 24 hours + cached live data. The synthesis prompt should produce:

```
System prompt for daily briefing:

You are GenLens, the intelligence engine for creative technologists working in AI-accelerated visual production.

Your audience: freelance Gen ADs, product photographers, filmmakers, digital human creators, creative technologists.

You have 10 dimensions of intelligence:
1. Workflow Stage Signals (what changed in their bottleneck)
2. Product Category Deep Dive (hard goods, soft goods, film types)
3. Competitive Intelligence (what other creatives are shipping)
4. Workflow Templates (fastest proven methods from real creators)
5. Cost & Time Delta (quantified savings)
6. Regulatory / IP / Ethical (legal safety)
7. Talent + Hiring (market rates, skills demand)
8. Integration + Compatibility (what plays nicely together)
9. Cultural / Trend Signals (what aesthetic is winning)
10. Benchmark + Leaderboard (who's winning, how)

For each signal, determine:
- Which vertical(s) it applies to
- Which dimension(s) it maps to
- What workflow stage(s) it affects
- What the creative implication is (not the business implication)
- What the action item is (what should a creative DO with this info)

Frame everything for creatives, not retailers. Language should be warm, expert, direct. Not corporate. Not academic. Think "smart friend who's also a working creative."

Output format: valid JSON (no markdown, no backticks):
{
  "ticker": "Top headline (max 12 words)",
  "vertical": "product_photography | filmmaking | digital_humans",
  "signals": [
    {
      "headline": "Declarative headline (max 10 words)",
      "dimension": 1-10,
      "dimension_label": "Workflow Stage Signals",
      "vertical": "product_photography | filmmaking | digital_humans",
      "source": "Source name",
      "source_url": "URL",
      "workflow_stages": ["render", "composite"],
      "product_categories": ["hard_goods"],
      "tools": ["keyshot"],
      "summary": "2-3 sentences. Each claim ends with (high), (medium), or (low) confidence.",
      "creative_implication": "What this means for your craft. 1-2 sentences.",
      "action_item": "What to do about it. 1 sentence.",
      "time_saved_hours": 6,
      "cost_saved_dollars": 1100,
      "confidence": "high | medium | low",
      "tags": ["rendering", "hard_goods", "keyshot"]
    }
  ],
  "template_spotlight": {
    "title": "Top template this week",
    "creator": "@handle",
    "tool_stack": ["figma_weave", "keyshot", "claid"],
    "time_hours": 12,
    "cost_dollars": 400,
    "trending_score": 340
  },
  "trend_signal": "One-sentence aesthetic trend observation",
  "legal_alert": "One-sentence legal/ethical update (or null)",
  "hiring_signal": "One-sentence talent market observation (or null)",
  "unsure": "Anything unconfirmed across all signals"
}
```

### X/LinkedIn Draft Synthesis

```
System prompt for social drafts:

Generate social media drafts based on the daily briefing data provided.

X post rules:
- Max 280 characters
- Punchy, warm, expert
- Pipeline impact first
- Light emoji usage
- End with engagement question or call to action
- Tag relevant tool accounts when applicable

LinkedIn post rules:
- Professional, value-first
- 150-300 words
- Lead with insight, not news
- Include specific numbers (time saved, cost reduced)
- End with question for engagement
- No hashtag spam (max 3 relevant hashtags)

Output format: valid JSON:
{
  "x_drafts": [
    { "text": "280 char max post", "tags": ["@runwayml"] }
  ],
  "linkedin_drafts": [
    { "text": "Full LinkedIn post", "hashtags": ["#AIFilmmaking"] }
  ]
}
```

### Keynote Talking Points Synthesis

```
System prompt for keynote output:

Generate keynote-ready talking points from the daily briefing.

Frame for: VP-level presentation to creative leadership or retail executives.
Tone: Strategic, data-backed, tied to time-to-market and competitive advantage.

Output format: valid JSON:
{
  "slide_title": "Headline for the slide",
  "narrative": "3-4 sentence strategic narrative",
  "key_metrics": [
    { "metric": "Time-to-market reduction", "value": "60%", "context": "vs. Q4 2025" }
  ],
  "competitive_context": "1-2 sentences on competitor landscape",
  "call_to_action": "1 sentence recommendation",
  "supporting_data": ["bullet point 1", "bullet point 2"]
}
```

---

## VERCEL CRON CONFIGURATION

```json
{
  "crons": [
    {
      "path": "/api/cron/daily-scrape",
      "schedule": "0 11 * * *"
    },
    {
      "path": "/api/cron/daily-brief",
      "schedule": "0 13 * * *"
    }
  ]
}
```

- `daily-scrape` runs at 11:00 UTC (6:00 AM ET): Scrapes all 130 sources, deduplicates, classifies, caches.
- `daily-brief` runs at 13:00 UTC (8:00 AM ET): Synthesizes cached signals into briefing, generates social drafts + keynote, sends email to all subscribers.

---

## AUTH FLOW

1. User visits GenLens
2. If not authenticated: show landing page with "Enter Invite Code" form
3. User enters invite code → validates against `invite_codes` table
4. If valid: show "Enter Email" for magic link (NextAuth email provider via Resend)
5. User clicks magic link in email → authenticated, redirected to dashboard
6. Session persists via NextAuth JWT

Admin can generate new invite codes from settings panel.

---

## BUILD ORDER

Follow this exact sequence:

### Phase 1: Foundation (Days 1-3)
1. `npx create-next-app@latest genlens --typescript --tailwind --app`
2. Set up Neon Postgres connection
3. Run database migrations (all tables above)
4. Set up NextAuth with email provider (Resend)
5. Invite code system
6. Basic layout (dark mode, fonts, nav)
7. Settings page (user preferences)

### Phase 2: Scraper Engine (Days 4-8)
1. Build generic RSS fetcher
2. Build generic HTML scraper
3. Build GitHub API scraper
4. Build HN Algolia scraper
5. Build arXiv API scraper
6. Build Reddit JSON scraper
7. Build YouTube RSS scraper
8. Wire up all 130 sources in `sources.ts`
9. Build deduplication engine (content hashing)
10. Build taxonomy classifier (tag each signal by dimension, vertical, workflow stage, category)
11. Build scraper orchestrator (runs all sources in parallel with rate limiting)
12. Build Vercel Cron endpoint for daily scrape
13. Build scrape logging (track success/failure per source)

### Phase 3: Synthesis (Days 9-12)
1. Build Claude synthesis engine
2. Daily briefing generation (per vertical)
3. X/LinkedIn draft generation
4. Keynote talking points generation
5. Template spotlight selection (find top trending template)
6. Store generated outputs in `briefings` table

### Phase 4: Dashboard (Days 13-18)
1. Main feed (signal cards, filterable by vertical + dimension)
2. Vertical toggle (Product Photography | Filmmaking | Digital Humans)
3. Dimension filter (show only specific dimensions)
4. Signal card component (headline, summary, creative implication, action item, cost/time delta)
5. Template leaderboard page
6. Creator leaderboard page
7. Sidebar (source status, stats, quick nav)
8. Cost/time savings visualization
9. Trend signals section
10. Legal alerts section
11. Hiring signals section
12. Integration matrix section

### Phase 5: Outputs (Days 19-22)
1. Daily email template (Resend)
2. Email delivery system (subscriber list, send to all)
3. Social drafts viewer (X/LinkedIn, copy-to-clipboard)
4. Keynote output viewer
5. Vercel Cron endpoint for daily email
6. Test email functionality
7. Subscriber management (add/remove/test)

### Phase 6: Polish (Days 23-28)
1. Error handling across all scrapers
2. Rate limiting (respect API limits)
3. Source health monitoring (track which sources are failing)
4. Mobile responsive
5. Loading states, empty states
6. Archive page (past briefings, searchable)
7. Settings: customize verticals, dimensions, delivery time, tools tracked
8. Admin panel: invite codes, subscriber list, scrape status, brief log

---

## ENVIRONMENT VARIABLES

```
DATABASE_URL=postgres://...@neon.tech/genlens?sslmode=require
NEXTAUTH_SECRET=random-secret-string
NEXTAUTH_URL=https://your-domain.vercel.app
ANTHROPIC_API_KEY=sk-ant-xxxx
RESEND_API_KEY=re_xxxx
EMAIL_FROM=brief@yourdomain.com
CRON_SECRET=random-cron-secret
PRODUCT_HUNT_TOKEN=optional
GITHUB_TOKEN=optional-for-higher-rate-limits
INVITE_CODE_DEFAULT=your-first-invite-code
```

---

## DESIGN TOKENS

```css
:root {
  --bg: #0e0e0e;
  --bg2: #161616;
  --bg3: #1e1e1e;
  --border: #2a2a2a;
  --border2: #333;
  --text: #e8e4dc;
  --text2: #9a9690;
  --text3: #5a5652;
  --accent: #c8f04a;      /* lime - builder/technical signals */
  --accent2: #f0a83c;     /* amber - creative/trend signals */
  --red: #f04a4a;          /* alerts, errors, legal warnings */
  --blue: #5ab4f0;         /* live data, links */
  --purple: #b07af0;       /* digital humans vertical accent */
  --font-mono: 'IBM Plex Mono', monospace;
  --font-serif: 'Lora', serif;
  --font-display: 'Playfair Display', serif;
}
```

Vertical accent colors:
- Product Photography: `--accent` (lime)
- Filmmaking: `--accent2` (amber)
- Digital Humans: `--purple` (purple)

---

## NOTES FOR CLAUDE CODE

1. Use `@neondatabase/serverless` for database (not pg or prisma)
2. Use `next-auth@5` (v5 beta for App Router compatibility)
3. All API routes use Next.js App Router format (`route.ts`)
4. Scraper should use `Promise.allSettled` (don't fail all if one source fails)
5. Rate limit: max 5 concurrent scrapes, 1 second delay between batches
6. Content hash for dedup: SHA-256 of `title + source_url`
7. Taxonomy classification: use Claude API call per batch of 10 signals (not per signal)
8. Cache scraped data in Neon (2-hour TTL for live feeds, 24-hour for blogs)
9. All dates in UTC, convert to user timezone on display
10. No em dashes in any output text, replace with commas or colons
11. Mobile-first responsive design
12. Dark mode only (no light mode toggle needed)
13. Every component should have loading + empty + error states
