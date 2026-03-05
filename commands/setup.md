---
name: last30days-setup
description: Configure API keys for /last30days in .claude/last30days.local.md
allowed-tools: ["Read", "Write", "AskUserQuestion", "Bash"]
---

# /last30days-setup

Set up or update the per-project API key configuration for the /last30days plugin.

## Steps

1. Check if `.claude/last30days.local.md` already exists. If it does, read it and show the user which keys are currently configured (show key names only, not values).

2. Ask the user which keys they want to configure. Explain the key groups:

   **Required (at least one):**
   - `OPENAI_API_KEY` - Powers Reddit search and web search fallback

   **X / Twitter (recommended):**
   - `AUTH_TOKEN` + `CT0` - Browser cookies for Bird GraphQL (best X data, free)
   - `XAI_API_KEY` - Fallback for X search via xAI API (if Bird unavailable)

   **Web Search (pick one):**
   - `PARALLEL_API_KEY` - Parallel AI search (preferred, best results)
   - `BRAVE_API_KEY` - Brave Search API (good alternative)
   - Or omit all three to use OpenRouter via OPENROUTER_API_KEY as fallback

   **Video / Social:**
   - `SCRAPECREATORS_API_KEY` - TikTok + Instagram search (same key for both, 100 free credits)
   - YouTube requires no key (uses yt-dlp locally)

   **Other:**
   - `OPENROUTER_API_KEY` - Fallback web search + alternative model routing

3. For each key the user provides, collect the value.

4. Write (or update) `.claude/last30days.local.md` with YAML frontmatter containing the keys. Use this template:

```markdown
---
OPENAI_API_KEY: "sk-..."
AUTH_TOKEN: "your_auth_token"
CT0: "your_ct0"
# Add other keys as needed
---

# /last30days Configuration

API keys for the last30days research plugin.
Keys are loaded automatically when running /last30days.
```

5. Ensure `.claude/` directory exists. Ensure `.gitignore` includes `*.local.md` pattern.

6. **Set file permissions to 600** (owner read/write only). After writing the file, run:
   ```bash
   chmod 600 .claude/last30days.local.md
   ```
   This prevents other users on the system from reading your API keys.

7. Confirm to the user that configuration is saved. Remind them:
   - This file is per-project, gitignored, and restricted to owner-only access (chmod 600)
   - Keys here override `~/.config/last30days/.env` and environment variables are still checked first
   - They can re-run `/last30days-setup` anytime to update keys
   - The SessionStart hook will warn if permissions are too open
