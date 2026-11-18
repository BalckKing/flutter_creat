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
TASK_LOCAL_FALLBACK="$TASK_TMP/local-listing"
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
cp "$TASK_BUNDLE_DIR/README.md" "$TASK_PORTABLE/README.md"
cp -R "$TASK_BUNDLE_DIR/flutter-engine-runner" "$TASK_PORTABLE/flutter-engine-runner"
cp -R "$TASK_BUNDLE_DIR/工作流文档" "$TASK_PORTABLE/工作流文档"
cp -R "$TASK_BUNDLE_DIR/flutter_done_check" "$TASK_PORTABLE/flutter_done_check"
[[ ! -e "$TASK_PORTABLE/ios-app-listing" ]]

FLUTTER_APP_LISTING_REPO="$TASK_REMOTE" FLUTTER_APP_LISTING_FALLBACK="$TASK_TMP/no-local" CODEX_HOME="$TASK_CODEX_HOME" \
  /bin/zsh "$TASK_PORTABLE/start.sh" --install-only --skills-dir "$TASK_TMP/skills" >/dev/null

[[ "$(<"$TASK_INSTALLED/references/ios-app-listing/REVISION.txt")" == "latest" ]]
[[ "$(git -C "$TASK_INSTALLED/references/ios-app-listing" branch --show-current)" == "feature/1.2.1-A1" ]]
[[ "$(git -C "$TASK_INSTALLED/references/ios-app-listing" rev-parse HEAD)" == "$TASK_LATEST_COMMIT" ]]
[[ "$(git -C "$TASK_INSTALLED/references/ios-app-listing" remote get-url origin)" == "$TASK_REMOTE" ]]
cmp "$TASK_BUNDLE_DIR/flutter-engine-runner/scripts/validate_about_copy.py" "$TASK_INSTALLED/scripts/validate_about_copy.py"
cmp "$TASK_BUNDLE_DIR/flutter-engine-runner/scripts/validate_review_remarks.py" "$TASK_INSTALLED/scripts/validate_review_remarks.py"
cmp "$TASK_BUNDLE_DIR/flutter-engine-runner/scripts/validate_public_copy.py" "$TASK_INSTALLED/scripts/validate_public_copy.py"
cmp "$TASK_BUNDLE_DIR/flutter-engine-runner/scripts/validate_path_names.py" "$TASK_INSTALLED/scripts/validate_path_names.py"
cmp "$TASK_BUNDLE_DIR/flutter-engine-runner/scripts/prepare_ios_config.py" "$TASK_INSTALLED/scripts/prepare_ios_config.py"
cmp "$TASK_BUNDLE_DIR/flutter-engine-runner/scripts/prepare_git_handoff.py" "$TASK_INSTALLED/scripts/prepare_git_handoff.py"

TASK_INSTALL_OUTPUT="$(FLUTTER_APP_LISTING_REPO="$TASK_TMP/missing.git" FLUTTER_APP_LISTING_FALLBACK="$TASK_TMP/no-local" CODEX_HOME="$TASK_CODEX_HOME" \
  /bin/zsh "$TASK_PORTABLE/start.sh" --install-only --skills-dir "$TASK_TMP/skills" 2>&1)"

[[ -d "$TASK_INSTALLED" ]]
[[ -f "$TASK_INSTALLED/SKILL.md" ]]
[[ ! -e "$TASK_INSTALLED/references/ios-app-listing" ]]
[[ "$TASK_INSTALL_OUTPUT" == *"后备生成"* ]]
[[ "$TASK_INSTALL_OUTPUT" == *"远程同步失败"* ]]
[[ "$(<"$TASK_INSTALLED/references/ios-app-listing-source.txt")" == *"mode=contract-fallback"* ]]
[[ "$(<"$TASK_INSTALLED/references/ios-app-listing-source.txt")" == *"checkout_branch=none"* ]]
[[ "$TASK_INSTALL_OUTPUT" == *"仍安装核心流程"* ]]
TASK_PRIOR_CHECKOUTS=("$TASK_TMP"/skill-backups/flutter-engine-runner/previous-*/references/ios-app-listing(N))
[[ ${#TASK_PRIOR_CHECKOUTS} -ge 1 ]]
[[ "$(git -C "${TASK_PRIOR_CHECKOUTS[1]}" rev-parse HEAD)" == "$TASK_LATEST_COMMIT" ]]

# A local Skill can be a non-Git directory and may lack a newer optional validator.
mkdir -p "$TASK_LOCAL_FALLBACK"
cp -R "$TASK_SOURCE/" "$TASK_LOCAL_FALLBACK/"
rm -rf -- "$TASK_LOCAL_FALLBACK/.git"
rm -- "$TASK_LOCAL_FALLBACK/scripts/validate_site_publication_ready.py"
TASK_INSTALL_OUTPUT="$(FLUTTER_APP_LISTING_REPO="$TASK_TMP/missing.git" FLUTTER_APP_LISTING_FALLBACK="$TASK_LOCAL_FALLBACK" CODEX_HOME="$TASK_CODEX_HOME" \
  /bin/zsh "$TASK_PORTABLE/start.sh" --install-only --skills-dir "$TASK_TMP/skills" 2>&1)"
[[ -L "$TASK_INSTALLED/references/ios-app-listing" ]]
[[ "$(readlink "$TASK_INSTALLED/references/ios-app-listing")" == "$TASK_LOCAL_FALLBACK" ]]
[[ "$(<"$TASK_INSTALLED/references/ios-app-listing-source.txt")" == *"mode=local-fallback"* ]]
[[ "$(<"$TASK_INSTALLED/references/ios-app-listing-source.txt")" == *"commit=unversioned"* ]]
[[ "$(<"$TASK_INSTALLED/references/ios-app-listing-source.txt")" == *"optional_publication_validator=missing; use the available output-contract and rendered-page checks"* ]]
[[ "$TASK_INSTALL_OUTPUT" == *"本机 ios-app-listing 后备生成"* ]]
[[ "$TASK_INSTALL_OUTPUT" == *"没有可选的 validate_site_publication_ready.py"* ]]

# An incomplete remote checkout must not masquerade as a usable remote Skill.
git -C "$TASK_SOURCE" rm scripts/render_app_listing.py >/dev/null
git -C "$TASK_SOURCE" commit -m "incomplete listing fixture" >/dev/null
git -C "$TASK_SOURCE" push origin feature/1.2.1-A1 >/dev/null 2>&1
FLUTTER_APP_LISTING_REPO="$TASK_REMOTE" FLUTTER_APP_LISTING_FALLBACK="$TASK_LOCAL_FALLBACK" CODEX_HOME="$TASK_CODEX_HOME" \
  /bin/zsh "$TASK_PORTABLE/start.sh" --install-only --skills-dir "$TASK_TMP/skills" >/dev/null 2>&1
[[ -L "$TASK_INSTALLED/references/ios-app-listing" ]]
[[ "$(readlink "$TASK_INSTALLED/references/ios-app-listing")" == "$TASK_LOCAL_FALLBACK" ]]

# A first installation also succeeds when neither source exists.
FLUTTER_APP_LISTING_REPO="$TASK_TMP/missing.git" FLUTTER_APP_LISTING_FALLBACK="$TASK_TMP/no-local" CODEX_HOME="$TASK_CODEX_HOME" \
  /bin/zsh "$TASK_PORTABLE/start.sh" --install-only --skills-dir "$TASK_TMP/fresh-skills" >/dev/null 2>&1
[[ -f "$TASK_TMP/fresh-skills/flutter-engine-runner/SKILL.md" ]]
cmp "$TASK_BUNDLE_DIR/flutter-engine-runner/scripts/validate_about_copy.py" "$TASK_TMP/fresh-skills/flutter-engine-runner/scripts/validate_about_copy.py"
cmp "$TASK_BUNDLE_DIR/flutter-engine-runner/scripts/validate_review_remarks.py" "$TASK_TMP/fresh-skills/flutter-engine-runner/scripts/validate_review_remarks.py"
cmp "$TASK_BUNDLE_DIR/flutter-engine-runner/scripts/validate_public_copy.py" "$TASK_TMP/fresh-skills/flutter-engine-runner/scripts/validate_public_copy.py"
cmp "$TASK_BUNDLE_DIR/flutter-engine-runner/scripts/validate_path_names.py" "$TASK_TMP/fresh-skills/flutter-engine-runner/scripts/validate_path_names.py"
cmp "$TASK_BUNDLE_DIR/flutter-engine-runner/scripts/prepare_git_handoff.py" "$TASK_TMP/fresh-skills/flutter-engine-runner/scripts/prepare_git_handoff.py"
[[ ! -e "$TASK_TMP/fresh-skills/flutter-engine-runner/references/ios-app-listing" ]]
[[ "$(<"$TASK_TMP/fresh-skills/flutter-engine-runner/references/ios-app-listing-source.txt")" == *"mode=contract-fallback"* ]]
print -r -- "PASS: latest remote, missing/incomplete remote, local fallback without optional validator, recoverable prior install, and fresh contract fallback."
