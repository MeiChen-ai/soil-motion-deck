#!/usr/bin/env bash
set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS=("soil-motion-html" "soil-motion-deck")

TARGETS=(
  "$HOME/.gemini/config/skills"
  "$HOME/.config/opencode/skills"
  "$HOME/.agents/skills"
  "$HOME/.claude/skills"
  "$HOME/.codex/skills"
)

for TARGET in "${TARGETS[@]}"; do
  mkdir -p "$TARGET"
  for SKILL in "${SKILLS[@]}"; do
    rm -rf "$TARGET/$SKILL"
    cp -r "$REPO_ROOT/skills/$SKILL" "$TARGET/$SKILL"
  done
  echo "[OK] Installed (${SKILLS[*]}) to: $TARGET"
done

echo ""
echo "🎉 Both SOIL Motion Skills (soil-motion-html & soil-motion-deck) are installed!"
echo "👉 Open a new chat in Antigravity, OpenCode, Claude Code, or Codex to start animating your teaching slides."
