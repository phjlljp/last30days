#!/bin/bash
set -euo pipefail

# Check if last30days has any configuration source available.
# Priority: .claude/last30days.local.md > ~/.config/last30days/.env > env vars

LOCAL_MD=".claude/last30days.local.md"
GLOBAL_ENV="$HOME/.config/last30days/.env"

# Helper: warn if file permissions are too open
check_perms() {
  local file="$1"
  if [[ ! -f "$file" ]]; then return; fi
  local perms
  perms=$(stat -f '%Lp' "$file" 2>/dev/null || stat -c '%a' "$file" 2>/dev/null || echo "")
  if [[ -n "$perms" && "$perms" != "600" && "$perms" != "400" ]]; then
    echo "/last30days: WARNING — $file has permissions $perms (should be 600)."
    echo "  Fix: chmod 600 $file"
  fi
}

# Check plugin-native config
if [[ -f "$LOCAL_MD" ]]; then
  check_perms "$LOCAL_MD"
  exit 0
fi

# Check legacy global config
if [[ -f "$GLOBAL_ENV" ]]; then
  check_perms "$GLOBAL_ENV"
  exit 0
fi

# Check if OPENAI_API_KEY is set in environment (minimum requirement)
if [[ -n "${OPENAI_API_KEY:-}" ]]; then
  exit 0
fi

# No config found — inform user
cat <<'EOF'
/last30days: No API keys configured.

Run /last30days-setup to create .claude/last30days.local.md with your API keys,
or create ~/.config/last30days/.env manually. At minimum, OPENAI_API_KEY is required.
EOF
