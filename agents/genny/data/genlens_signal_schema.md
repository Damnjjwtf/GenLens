# GenLens Signal Schema

Last updated: July 18, 2026

Adapted from a MarTech monitoring PRD. The subject matter is different, but the operating model is useful for Genny.

## Core Directive

Genny is not a link aggregator. Genny is an AI creative-production intelligence agent.

Every accepted signal should explain:

- what changed.
- how it works.
- who uses it.
- what production metric it affects.
- where the source proves it.

## Required Signal Fields

### Headline

Action-oriented. Name the tool/platform and the mechanism.

Weak:

- "Runway has a new update."

Strong:

- "Runway Aleph adds controllable frame editing inside Figma Weave."

### Core Dynamic

Explain the underlying mechanism:

- model capability.
- node graph / workflow engine.
- API or SDK.
- agent framework.
- data hook.
- renderer, inference layer, compositing path, mocap system, voice pipeline, or automation layer.

### Concrete Use Case

Explain how a working creative uses it:

- product photographer creates presale PDP images before manufacturing.
- VFX artist moves generated plates into Nuke/Resolve.
- digital human director generates localized avatar dialogue.
- game team blocks playable variants during find-the-fun.
- ArchViz studio creates design-option renders before client review.

### Strategic Impact

Tie the signal to measurable production outcomes:

- time saved.
- cost reduced.
- iteration count increased.
- render/inference latency changed.
- quality control improved.
- rights/compliance risk reduced.
- human labor shifted from execution to supervision.

If no metric or workflow impact can be inferred from the source, mark the item as a lead, not a publishable signal.

### Verifiable Source

Prefer source hierarchy:

1. Official release notes, docs, changelogs, GitHub releases, papers.
2. Verified case studies and production breakdowns.
3. Trade publications with concrete workflow details.
4. Curated news/search feeds only as discovery, not final authority.

## GenLens Pillars

### Generative Visual Production

Image, video, 3D, shot, layout, and campaign asset generation.

Keywords:

- image-to-video
- text-to-video
- controllable generation
- frame editing
- visual consistency
- style transfer
- product imagery
- campaign variants

### Creative Pipeline Automation

Workflow engines, node graphs, batch production, asset handoff, and studio operations.

Keywords:

- ComfyUI
- node graph
- batch generation
- ShotGrid
- production pipeline
- API workflow
- model routing
- render automation

### Synthetic Performance

Digital humans, voices, avatars, mocap, lip sync, localization, and synthetic actors.

Keywords:

- avatar
- voice cloning
- dubbing
- synthetic presenter
- lip sync
- mocap
- MetaHuman
- character animation

### Creative Inference Infrastructure

Model hosting, latency, cost, GPUs, API delivery, and production reliability.

Keywords:

- inference
- latency
- GPU
- fal
- Replicate
- API pricing
- model deployment
- throughput

### Rights, Provenance, And Compliance

Licensing, consent, labeling, provenance, training data constraints, union rules, and delivery documentation.

Keywords:

- consent
- likeness
- provenance
- watermark
- SAG-AFTRA
- rights
- compliance
- content credentials

### AI-Native Creative Roles

Hiring signals and new labor patterns.

Keywords:

- creative technologist
- generative artist
- AI pipeline engineer
- inference specialist
- synthetic production TD
- AI workflow producer
- ComfyUI artist

## Publish Filter

Reject:

- generic AI hype.
- product homepages.
- broad funding news without workflow implication.
- duplicate rewrites of the same announcement.
- stale posts outside the recency window.
- gear posts unrelated to AI workflow.
- "will X redefine Y?" thought pieces without a concrete mechanism.

Accept:

- releases with specific model/workflow capability.
- API, SDK, or integration changes.
- production case studies.
- tool interoperability changes.
- benchmark/cost/latency changes.
- credible role/hiring signals.
- rights/compliance changes with creative-production impact.

## Daily Brief Format

For each accepted item:

- **Platform/Technology**: tool and parent company.
- **Core Dynamic**: mechanism or workflow change.
- **Concrete Use Case**: how a Gen AD uses it.
- **Strategic Impact**: time, cost, quality, iteration, compliance, or role impact.
- **Source Verification Link**: exact source URL.

## Curator Rule

If Genny cannot fill at least three of the five daily brief fields from the source, the item stays in the research queue and does not enter the email.
