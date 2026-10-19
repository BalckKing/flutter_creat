#!/bin/zsh

emulate -L zsh
set -euo pipefail

TASK_BUNDLE_DIR="${1:-${0:A:h:h}}"
TASK_BUNDLE_DIR="${TASK_BUNDLE_DIR:A}"
TASK_TMP="$(mktemp -d /tmp/flutter-listing-install-test.XXXXXX)"
trap 'rm -rf -- "$TASK_TMP"' EXIT

TASK_SOURCE="$TASK_TMP/source"
TASK_REMOTE="$TASK_TMP/remote.git"
TASK_PORTABLE="$TASK_TMP/portable"
TASK_INSTALLED="$TASK_TMP/skills/flutter-engine-runner"
TASK_CODEX_HOME="$TASK_TMP/codex"
mkdir -p "$TASK_SOURCE/references" "$TASK_SOURCE/scripts" "$TASK_SOURCE/assets/site-render" "$TASK_PORTABLE"

git init --bare "$TASK_REMOTE" >/dev/null
git init "$TASK_SOURCE" >/dev/null
git -C "$TASK_SOURCE" checkout -b feature/1.2.1-A1 >/dev/null
git -C "$TASK_SOURCE" config user.name "Workflow Test"
git -C "$TASK_SOURCE" config user.email "workflow-test@example.invalid"

print -r -- "name: ios-app-listing" > "$TASK_SOURCE/SKILL.md"
print -r -- "latest output contract" > "$TASK_SOURCE/references/output-contract.md"
print -r -- "privacy rules" > "$TASK_SOURCE/references/privacy-ai-rules.md"
print -r -- "inspect" > "$TASK_SOURCE/scripts/inspect_app.py"
print -r -- "generate" > "$TASK_SOURCE/scripts/generate_app_listing.py"
print -r -- "validate" > "$TASK_SOURCE/scripts/validate_site_publication_ready.py"
print -r -- "render" > "$TASK_SOURCE/scripts/render_app_listing.py"
print -r -- "{}" > "$TASK_SOURCE/assets/site-render/templates-manifest.json"
print -r -- "initial" > "$TASK_SOURCE/REVISION.txt"
git -C "$TASK_SOURCE" add .
git -C "$TASK_SOURCE" commit -m "initial listing skill" >/dev/null
git -C "$TASK_SOURCE" remote add origin "$TASK_REMOTE"
git -C "$TASK_SOURCE" push -u origin feature/1.2.1-A1 >/dev/null 2>&1

print -r -- "latest" > "$TASK_SOURCE/REVISION.txt"
git -C "$TASK_SOURCE" add REVISION.txt
git -C "$TASK_SOURCE" commit -m "latest listing skill" >/dev/null
git -C "$TASK_SOURCE" push origin feature/1.2.1-A1 >/dev/null 2>&1
TASK_LATEST_COMMIT="$(git -C "$TASK_SOURCE" rev-parse HEAD)"

cp "$TASK_BUNDLE_DIR/start.sh" "$TASK_PORTABLE/start.sh"
cp -R "$TASK_BUNDLE_DIR/flutter-engine-runner" "$TASK_PORTABLE/flutter-engine-runner"
cp -R "$TASK_BUNDLE_DIR/工作流文档" "$TASK_PORTABLE/工作流文档"
[[ ! -e "$TASK_PORTABLE/ios-app-listing" ]]

FLUTTER_APP_LISTING_REPO="$TASK_REMOTE" CODEX_HOME="$TASK_CODEX_HOME" \
  /bin/zsh "$TASK_PORTABLE/start.sh" --install-only --skills-dir "$TASK_TMP/skills" >/dev/null

[[ "$(<"$TASK_INSTALLED/references/ios-app-listing/REVISION.txt")" == "latest" ]]
[[ "$(git -C "$TASK_INSTALLED/references/ios-app-listing" branch --show-current)" == "feature/1.2.1-A1" ]]
[[ "$(git -C "$TASK_INSTALLED/references/ios-app-listing" rev-parse HEAD)" == "$TASK_LATEST_COMMIT" ]]
[[ "$(git -C "$TASK_INSTALLED/references/ios-app-listing" remote get-url origin)" == "$TASK_REMOTE" ]]

if FLUTTER_APP_LISTING_REPO="$TASK_TMP/missing.git" CODEX_HOME="$TASK_CODEX_HOME" \
  /bin/zsh "$TASK_PORTABLE/start.sh" --install-only --skills-dir "$TASK_TMP/skills" >/dev/null 2>&1; then
  print -u2 -- "Expected installation to fail when the remote repository is unavailable."
  exit 1
fi

[[ "$(<"$TASK_INSTALLED/references/ios-app-listing/REVISION.txt")" == "latest" ]]
[[ "$(git -C "$TASK_INSTALLED/references/ios-app-listing" rev-parse HEAD)" == "$TASK_LATEST_COMMIT" ]]
print -r -- "PASS: installs latest remote branch without a bundled copy and preserves the prior install on fetch failure."
