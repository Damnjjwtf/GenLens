# GenLens Backlog

Ideas explored but deliberately deferred. Each entry has a **revisit trigger**
that is observable from data or operations, not vague intent.

Review this file:
- Quarterly (calendar reminder)
- When hitting milestones (50, 100, 500 users)
- When a user explicitly asks for one of these features
- When a signal in the data makes one obviously timely

---

## NEW VERTICALS (Phase 3+)

### Vertical 4: Music Production / Audio

**What:** Daily intelligence for music producers, sound designers, audio engineers working in AI-accelerated composition, stem separation, mastering, and voice synthesis.

**Why it matters:** ElevenLabs, Suno, Udio are moving as fast as visual tools. Producers want to know: which AI mastering tools are trusted? Can you actually use Suno-generated stems commercially? What's the latest on stem separation quality?

**Sources already tracked:** 35+ (Suno, Udio, AIVA, iZotope, Descript, Logic Pro, Ableton, Reaper, Splice, etc.) See TOOLS_MANIFEST.md for full list.

**Dimensions map:**
1. Workflow stages: composition, arrangement, stem separation, mixing, mastering, distribution
5. Cost/time delta: "AI mastering costs $0.99, human mastering costs $500"
6. Legal: mechanical licensing for AI composition, copyright of generated music, disclosure
7. Hiring: producers who can use Suno command 2-3x rates in gig markets

**Accent color:** Cyan (cool, distinct from lime/amber/purple)

**Revisit when:**
- 100+ active users, Music Production appears in 15%+ of "What's your discipline?" survey
- Or: Suno/Udio licensing questions spike in support (signal creatives care)

---

### Vertical 5: AI-Accelerated Design / Motion Graphics

**What:** Daily intelligence for motion designers, UI animators, interaction designers using AI to accelerate design systems, prototyping, and animation.

**Why it matters:** Cavalry, Rive, Jitter, Haiku Animator transforming motion creation. Figma + AI plugins, Midjourney for layout, Stable Diffusion for assets. Arguably more practitioners than Product Photography.

**Sources already tracked:** 40+ (Cavalry, Rive, Jitter, Haiku, Figma, Midjourney, Stable Diffusion, Framer, Spline, etc.) See TOOLS_MANIFEST.md for full list.

**Dimensions map:**
1. Workflow stages: ideation, composition, layout, animation, prototyping, implementation
4. Templates: "Haiku + Figma workflow: 8 hours per design system component"
9. Trends: micro-interactions, generative layouts, code-driven animation

**Accent color:** Blue (professional, tech-adjacent)

**Revisit when:**
- 100+ active users, Motion Design/Graphics appears in 15%+ of survey
- Or: After Effects + Cavalry tool chains appear in signals with high frequency
- Or: Motion designers self-report as separate from Filmmaking users

---

### Vertical 6: Fashion / Apparel / Textile Design

**What:** Daily intelligence for fashion designers, pattern makers, apparel technologists using AI for garment simulation, fabric generation, fit prediction, and trend forecasting.

**Why it matters:** CLO 3D, Marvelous Designer adoption accelerating. AI fabric generation (Midjourney, Stable Diffusion) for texture. Size prediction AI (True Fit, SizeScale). Trend forecasting (WGSN, Fashion Snoops) + generative tools.

**Sources already tracked:** 30+ (CLO 3D, Marvelous Designer, Browzwear, True Fit, WGSN, Printful, etc.) See TOOLS_MANIFEST.md for full list.

**Dimensions map:**
2. Category deep dive: soft goods (currently under Product Photography), textiles, hybrid
5. Cost/time delta: "CLO 3D saves 8 hours per garment vs. physical sample"
7. Hiring: pattern graders who know Lectra + AI at 45% higher salaries

**Accent color:** Pink / warm (creative, fashion-adjacent)

**Key question before building:** Are fashion designers self-identifying as separate from "product photographers (apparel)" or are they the same user?

**Revisit when:**
- 20%+ of survey respondents identify as "fashion designer" vs. "product photographer"
- Or: CLO 3D + Marvelous Designer signals dominate soft goods category
- Or: You identify fashion-specific communities (CLO Discord, Fashion Snoops forums) unreached by Product Photography channels

---

## SHELVED VERTICALS (do not pursue)

### Game Development / Real-Time 3D
**Why:** Strong existing communities (GDC, Gamasutra, r/GameDev, Discord). GenLens adds no value. Skip.

### Scientific Visualization / Data
**Why:** Different audience (researchers, academics). No creative technologist overlap. Skip.

### Medical Imaging / Healthcare
**Why:** Regulated industry. Clinical requirements. Different tools. Not a GenLens use case. Skip.

---

## ORIGINAL BACKLOG ITEMS

---

## GenLens Arbitrage

**What:** Time-bounded pricing-opportunity alerts. Example: voice synthesis
cost dropped 98% in 6 months while studios still charge old rates. Surface
these windows to freelancers with a countdown ("closes in ~62 days based
on adoption curve") so they can capture the delta.

**Why deferred:** Needs Score + Index shipped first to have credibility
and source data. Also needs user workflow logging at volume.

**Revisit when (any one):**
- GenLens Score is live and cited by 1+ tool vendor
- 100+ active users have logged at least one workflow
- 3+ tools in the same vertical drop cost 50%+ in a single quarter
  (auto-detectable from `signals.cost_saved_dollars` deltas)

**Open questions to resolve before building:**
- Does "Arbitrage" land with creatives or read as finance-bro? Test name
  with 5 target users first.
- Is the framing ("charge old rates, deliver new costs") an optics or
  legal issue? Get a read before launch.

---

## Rate Card Generator

**What:** Auto-generates a freelancer rate card from logged tool stack
plus active arbitrage windows. Outputs a downloadable, shareable artifact.

**Why deferred:** Depends on Arbitrage shipping first.

**Revisit when:** Arbitrage has 30+ days of usage data and at least 20
users have logged a tool stack.

---

## Score Decay (half-life mechanic)

**What:** Tool scores drop over time without updates. KeyShot's score
falls 5 points/month if the company ships nothing new. Forces vendor
re-engagement and signals which tools are stagnating.

**Why deferred:** Fun mechanic but adds complexity before the core Score
is validated. Could also produce noisy/unfair scores if the recency
component is already in the formula.

**Revisit when:** Score has been live for 3+ months and we have data on
how often tools actually update (which determines if decay is signal or noise).

---

## Personal Arbitrage Alerts

**What:** Email push when a user's logged stack hits an arbitrage window.
"Your stack just got 40% cheaper. Here's how to capture the delta."

**Why deferred:** Subset of Arbitrage. Same gating conditions.

**Revisit when:** Arbitrage ships and email infrastructure is already
proven via the daily briefing.

---

## Growth Loop (Score + Arbitrage shareable artifacts)

**What:** Users share their personal Score / Arbitrage wins on X and
LinkedIn with branded cards. Shares contain "see your score" CTAs.
Followers in the same vertical sign up. New users contribute workflow
data, which improves benchmarks, which makes scores more accurate, which
makes them more shareable. Closed loop.

**Why deferred:** The loop only works once both Score and Arbitrage exist
AND workflow logging takes under 60 seconds. Premature optimization
otherwise.

**Revisit when (all three):**
- Score is live
- Arbitrage is live
- Workflow log flow takes <60 seconds end-to-end (measure it)

**Risks to watch:**
- Step 1 friction (manual workflow logging). Mitigation: pull from
  connected tools, or one-click "add this template I just used."
- Share artifact quality. If it looks like every other "I used AI" badge,
  the loop dies. Design matters.
- Cold start. Need enough users in a vertical for percentiles to mean
  anything.

---

## Revisit triggers — quick reference

| Idea | Trigger |
|---|---|
| Arbitrage | Score cited by 1 vendor OR 100 users logged workflow OR cost-drop signal cluster |
| Rate Card Generator | Arbitrage live + 30 days data + 20 users with stacks |
| Score Decay | Score live for 3 months |
| Personal Arbitrage Alerts | Arbitrage ships |
| Growth Loop | Score live + Arbitrage live + workflow log <60s |

---

## How to add a new shelved idea

When deferring something new, use this template:

```
## [Idea Name]

**What:** [one paragraph, plain English]
**Why deferred:** [the actual reason, not "we'll get to it"]
**Revisit when:** [observable, queryable trigger]
**Open questions:** [things to resolve before building]
```

If you can't write a concrete revisit trigger, the idea isn't ready to
shelve — it's ready to kill. Either commit to a trigger or remove it.
