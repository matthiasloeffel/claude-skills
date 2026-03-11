#!/bin/bash
# Auto-sync Claude skills to GitHub
# Runs every 5 minutes via macOS LaunchAgent

SKILLS_DIR="$HOME/.claude/skills"
LOG="$HOME/.claude/skills-sync.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

cd "$SKILLS_DIR" || exit 1

# Check if remote is configured
if ! git remote get-url origin &>/dev/null; then
  echo "[$DATE] No remote configured — skipping push" >> "$LOG"
  exit 0
fi

# Stage any changes
git add -A

# Only commit + push if there are actual changes
if git diff --cached --quiet; then
  # No changes
  exit 0
fi

git commit -m "Auto-sync $DATE" >> "$LOG" 2>&1
git push origin main >> "$LOG" 2>&1 && echo "[$DATE] Pushed successfully" >> "$LOG" || echo "[$DATE] Push failed" >> "$LOG"
