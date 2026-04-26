# GenLens Backlog

Ideas explored but deliberately deferred. Each entry has a **revisit trigger**
that is observable from data or operations, not vague intent.

Review this file:
- Quarterly (calendar reminder)
- When hitting milestones (50, 100, 500 users)
- When a user explicitly asks for one of these features
- When a signal in the data makes one obviously timely

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
