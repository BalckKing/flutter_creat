#!/bin/zsh

emulate -L zsh
set -euo pipefail

TASK_BUNDLE_DIR="${1:-${0:A:h:h}}"
TASK_BUNDLE_DIR="${TASK_BUNDLE_DIR:A}"
TASK_TMP="$(mktemp -d /tmp/flutter-project-local-listing-test.XXXXXX)"
trap 'rm -rf -- "$TASK_TMP"' EXIT

TASK_PORTABLE="$TASK_TMP/portable"
TASK_SKILLS="$TASK_TMP/skills"
TASK_CODEX_HOME="$TASK_TMP/codex"
mkdir -p "$TASK_PORTABLE"

cp "$TASK_BUNDLE_DIR/start.sh" "$TASK_PORTABLE/start.sh"
cp "$TASK_BUNDLE_DIR/README.md" "$TASK_PORTABLE/README.md"
cp -R "$TASK_BUNDLE_DIR/flutter-engine-runner" "$TASK_PORTABLE/flutter-engine-runner"
cp -R "$TASK_BUNDLE_DIR/工作流文档" "$TASK_PORTABLE/工作流文档"
cp -R "$TASK_BUNDLE_DIR/flutter_check" "$TASK_PORTABLE/flutter_check"
cp -R "$TASK_BUNDLE_DIR/ios-app-listing" "$TASK_PORTABLE/ios-app-listing"

# This sentinel exists only in the project-local source. The test also sets
# stale remote variables to prove they are ignored by the launcher.
print -r -- "project-local-sentinel" > "$TASK_PORTABLE/ios-app-listing/PROJECT_LOCAL_SENTINEL"

LEGACY_LISTING_REPO="$TASK_TMP/remote-that-must-not-be-read" \
LEGACY_LISTING_FALLBACK="$TASK_TMP/fallback-that-must-not-be-read" \
CODEX_HOME="$TASK_CODEX_HOME" \
  /bin/zsh "$TASK_PORTABLE/start.sh" --install-only --skills-dir "$TASK_SKILLS" >/dev/null

TASK_INSTALLED="$TASK_SKILLS/flutter-engine-runner"
[[ -f "$TASK_INSTALLED/references/ios-app-listing/PROJECT_LOCAL_SENTINEL" ]]
[[ "$(<"$TASK_INSTALLED/references/ios-app-listing-source.txt")" == *"mode=project-local"* ]]
[[ "$(<"$TASK_INSTALLED/references/ios-app-listing-source.txt")" == *"configured_source=project-local"* ]]
[[ "$(<"$TASK_INSTALLED/references/ios-app-listing-source.txt")" != *"remote-branch-marker"* ]]

# Removing the local source must use only the bundled contract fallback.
rm -rf -- "$TASK_PORTABLE/ios-app-listing"
LEGACY_LISTING_REPO="$TASK_TMP/remote-that-must-not-be-read" \
LEGACY_LISTING_FALLBACK="$TASK_TMP/fallback-that-must-not-be-read" \
CODEX_HOME="$TASK_CODEX_HOME" \
  /bin/zsh "$TASK_PORTABLE/start.sh" --install-only --skills-dir "$TASK_TMP/fresh-skills" >/dev/null 2>&1
[[ "$(<"$TASK_TMP/fresh-skills/flutter-engine-runner/references/ios-app-listing-source.txt")" == *"mode=contract-fallback"* ]]
[[ ! -e "$TASK_TMP/fresh-skills/flutter-engine-runner/references/ios-app-listing" ]]

print -r -- "PASS: project-local AppListing source is used; remote and external fallback variables are ignored; contract fallback is local-only."
