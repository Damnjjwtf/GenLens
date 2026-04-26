# Blocked Sources — Workarounds

Sources that can't be scraped automatically, with manual workarounds.
Action items here are owner tasks, not automation work.

---

## befores & afters Weeklies (newsletter only)

**Reason:** Newsletter-gated. The blog is scrapable (already in `sources.ts`), but the deeper "Weeklies" content ships only via newsletter.

**Workaround:** [kill-the-newsletter.com](https://kill-the-newsletter.com) — generates an RSS feed from a newsletter subscription. One-time setup, then RSS forever.

**Action:** Set up this week. Add the generated feed to `sources.ts` as another `befores & afters Weeklies` entry.

---

## WGSN

**Reason:** Paywalled trend forecasting (~$15k/yr enterprise).

**Workaround:** Monitor Sourcing Journal and BoF Technology for WGSN citations. Extract signal secondhand.

**Action:** Defer. Not worth the cost at current stage.

---

## Fashion Snoops

**Reason:** Paywalled, similar to WGSN.

**Workaround:** Same as WGSN — secondhand via trade press.

**Action:** Defer.

---

## Tool Discords (ElevenLabs, Descript, Wonder Dynamics, CLO 3D community)

**Reason:** Invite-required. Cannot automate.

**Workaround:** Join manually as GenLens. Monitor key channels. Seed high-signal posts as manual entries via admin panel.

**Action:** Join the ElevenLabs Discord this week — highest signal for DH vertical.

---

## VFX Squad Discord

**Invite:** https://discord.com/invite/vfx-squad-797000245413281792

**Reason:** Real-time troubleshooting / peer review for compositors, editors, motion designers. Discord, requires account.

**Workaround:** Join GenLens account, monitor key channels, seed high-signal threads as manual signals.

**Action:** Join this week. High-signal for FM vertical.

---

## Adobe Substance 3D Discord

**Invite:** https://discord.com/invite/010JCPblJTh3d6CXe

**Reason:** Pipeline troubleshooting + beta feature discussions for material authoring/texturing. Discord, requires account.

**Workaround:** Manual monitoring; seed beta-feature signals.

**Action:** Join when PP vertical scraper hits volume. Defer for now.

---

## Figma Community Discord

**Invite:** https://discord.com/invite/figma

**Reason:** AI plugins + design system automation discussion. Discord, requires account.

**Workaround:** Manual monitoring; seed plugin/AI signals.

**Action:** Activate when MG (motion graphics / design) vertical activates.

---

## Practitioner X accounts

**Reason:** Twitter API v2 free tier rate limits are severe. Authenticated scraping is costly.

**Workaround:** Use the web-search fallback (to be built in `lib/scraper/twitter.ts`) for top handles. Account list is in `lib/constants.ts → MONITORED_X_ACCOUNTS`. Cap at 10–15 high-signal accounts to stay within search-cost budget.

**Action:** Already wired in constants.ts. Build the `twitter.ts` fallback when scraper engine is in place.

---

## SIGGRAPH Proceedings

**Reason:** Annual. PDFs behind ACM paywall. Abstracts are public.

**Workaround:** HTML scrape `siggraph.org` proceedings page for titles + abstracts annually (July/August). One-time cron, not daily.

**Action:** Build as annual one-off. Low priority.

---

## Nuke (Foundry) community plugins

**Reason:** No public GitHub org. Plugin repos scattered across individual accounts.

**Workaround:** Search GitHub for `nuke plugin` filtered by recent update. Manual curation only.

**Action:** Defer. Cover via fxguide and r/vfx instead.

---

## Water & Music paid research

**Reason:** Best music tech analysis is behind Patreon.

**Workaround:** Free posts via the RSS feed already in `sources-deferred.ts`. Subscribe manually for paid research; add key findings as manual signals when especially relevant.

**Action:** Activate when Music Production vertical turns on.

---

## AES (Audio Engineering Society) publications

**Reason:** Membership-gated journal content.

**Workaround:** Conference schedule and free abstracts are public. Cover via r/audioengineering and MusicTech in the interim.

**Action:** Defer until MP vertical activates.
