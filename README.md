# GenLens

Daily intelligence for creative technologists working in AI-accelerated visual production (product photography, filmmaking, digital humans).

## Status

**Phase 1 — Foundation.** Next.js 14, NextAuth v5 with Resend magic links + invite codes, Neon Postgres schema, dark editorial UI shell, settings page. Scrapers, Claude synthesis, signal feed, and email delivery come online in Phase 2 onward.

See [docs/GENLENS_CLAUDE_CODE_BRIEF.md](docs/GENLENS_CLAUDE_CODE_BRIEF.md) and [docs/GENLENS_FOR_CREATIVES_COMPLETE_SPEC.md](docs/GENLENS_FOR_CREATIVES_COMPLETE_SPEC.md) for the full spec.

## Stack

- Next.js 14 (App Router)
- Neon Postgres (`@neondatabase/serverless`)
- NextAuth v5 beta (`@auth/pg-adapter`, Resend provider)
- Anthropic SDK (`@anthropic-ai/sdk`) — model `claude-sonnet-4-20250514`
- Tailwind CSS
- Vercel Cron

## Local setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Provision a Neon database.** Create a project at https://neon.tech, grab the pooled connection string.

3. **Run the schema migration:**
   ```bash
   psql "$DATABASE_URL" -f lib/db/schema.sql
   ```

4. **Seed an invite code** (replace value):
   ```bash
   psql "$DATABASE_URL" -c "INSERT INTO invite_codes (code, max_uses) VALUES ('GL-LAUNCH-0001', 50);"
   ```

5. **Fill in `.env.local`.** Required for sign-in:
   - `DATABASE_URL` — Neon pooled connection string
   - `AUTH_SECRET` (and `NEXTAUTH_SECRET`) — `openssl rand -base64 32`
   - `RESEND_API_KEY` — from https://resend.com
   - `EMAIL_FROM` — verified sender on a domain configured in Resend
   - `ANTHROPIC_API_KEY` — for Phase 3 synthesis

6. **Run dev server:**
   ```bash
   npm run dev
   ```
   Visit http://localhost:3000 — you'll be redirected to `/auth/invite`.

## Auth flow

1. User lands → middleware redirects to `/auth/invite`
2. Enter invite code → `/api/invite` validates, sets short-lived `genlens_invite` cookie
3. Enter email → NextAuth `signIn('resend', { email })` triggers magic link via Resend
4. User clicks link → session created, `events.createUser` consumes the invite cookie and stamps `users.invite_code_used`

## Next phases

- **Phase 2** — Scraper engine: 130+ sources, dedup, taxonomy, Vercel Cron
- **Phase 3** — Claude synthesis: daily briefings, social drafts, keynote points
- **Phase 4** — Dashboard: signal feed, vertical toggle, dimension filter, leaderboards
- **Phase 5** — Email delivery + admin
- **Phase 6** — Polish, archive, monitoring

## Repository layout

```
app/                 # Next.js App Router
  api/               # Route handlers (auth, invite, settings; cron added in Phase 2)
  auth/              # Sign-in pages (invite, signin redirect, verify-request)
  settings/          # User preferences
auth.ts              # NextAuth config (root, per v5 convention)
middleware.ts        # Route protection
lib/
  db.ts              # Neon client + typed queries
  db/schema.sql      # Postgres migration (run before first sign-in)
  constants.ts       # Verticals, dimensions, taxonomy enums
docs/                # Original product spec and build brief
vercel.json          # Cron schedule
```
