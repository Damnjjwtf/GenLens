# Marti Discord Feed

Marti can publish a concise, source-linked intelligence digest to a dedicated
Discord channel through a Discord webhook. The webhook is a delivery secret and
must live only in the VPS profile `.env`.

## Safety Contract

- A connection-only test may post before Marti is promoted.
- A real briefing post requires the same deterministic Marti promotion status
  used by editorial operations: three clean dated runs, 20 attributed human
  card reviews, and no more than one false positive in the review window.
- There is no force-send flag.
- Exact payload fingerprints are retained in
  `state/discord_delivery_history.json`; a repeated payload is not posted twice.
- Discord mentions are disabled in the webhook payload.
- The sender never prints the webhook URL.

## One-Time Discord Setup

1. In your Discord server, create a text channel named `marti-intelligence`.
2. Open **Server Settings → Integrations → Webhooks**.
3. Choose **New Webhook**, name it `Marti • GenLens`, and select the
   `#marti-intelligence` channel.
4. Choose **Copy Webhook URL**. Treat the URL like a password.
5. In the Spaceship VPS console, open Genny's environment file:

   ```bash
   nano /root/.hermes/profiles/genny/.env
   ```

6. Add this line, replacing the placeholder with the copied URL:

   ```text
   MARTI_DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   ```

7. Save with **Control-O**, press **Return**, then exit with **Control-X**.
8. Restart Genny so the environment change is available:

   ```bash
   systemctl restart hermes-gateway-genny.service
   ```

Do not paste the webhook URL into Codex, Discord chat, GitHub, screenshots, or
logs.

## Connection Test

The test posts only a short connection message and does not publish a briefing:

```bash
python3 /root/.hermes/profiles/genny/scripts/genlens_send_discord.py --test --send
```

Success returns JSON containing `"sent": true` and a Discord `message_id`.

## Preview and Publish

Preview the payload without sending:

```bash
python3 /root/.hermes/profiles/genny/scripts/genlens_send_discord.py
```

After Marti passes promotion, publish the latest governed briefing:

```bash
python3 /root/.hermes/profiles/genny/scripts/genlens_send_discord.py --send
```

Before promotion, the real send exits safely with the current hold reason. Do
not schedule the real sender until promotion is complete.
