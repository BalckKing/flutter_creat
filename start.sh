#!/bin/zsh

emulate -L zsh
set -euo pipefail

TASK_BUNDLE_DIR="${0:A:h}"
TASK_DOCS_DIR="$TASK_BUNDLE_DIR/工作流文档"
TASK_DOC_MANIFEST="$TASK_DOCS_DIR/manifest.txt"
TASK_DOC="$TASK_BUNDLE_DIR/从零开始创建完整且精致的flutter app工程.md"
if [[ ! -f "$TASK_DOC" ]]; then
  TASK_DOC="$TASK_DOCS_DIR/00-总入口.md"
fi
TASK_RUNNER_SOURCE="$TASK_BUNDLE_DIR/flutter-engine-runner"
TASK_CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"
TASK_SKILLS_DIR="$TASK_CODEX_DIR/skills"
TASK_INSTALL_ONLY=0
TASK_OPEN=1
TASK_CLIPBOARD=1
TASK_CUSTOM_SKILLS=0
TASK_PROJECT_DIR=""

while (( $# > 0 )); do
  case "$1" in
    --install-only) TASK_INSTALL_ONLY=1; TASK_OPEN=0; TASK_CLIPBOARD=0; shift ;;
    --no-open) TASK_OPEN=0; shift ;;
    --no-clipboard) TASK_CLIPBOARD=0; shift ;;
    --skills-dir|--project-dir)
      TASK_OPTION="$1"
      if (( $# < 2 )) || [[ -z "$2" || "$2" == --* ]]; then
        print -u2 -- "缺少参数：$TASK_OPTION 需要一个目录。"
        exit 2
      fi
      if [[ "$TASK_OPTION" == --skills-dir ]]; then
        TASK_SKILLS_DIR="${2:A}"
        TASK_CUSTOM_SKILLS=1
      else
        TASK_PROJECT_DIR="${2:A}"
      fi
      shift 2
      ;;
    --help)
      print -r -- "用法：start.command [--install-only] [--no-open] [--no-clipboard] [--project-dir 工程目录] [--skills-dir 技能目录]"
      exit 0
      ;;
    *) print -u2 -- "未知参数：$1；运行 --help 查看用法。"; exit 2 ;;
  esac
done

for TASK_REQUIRED in "$TASK_DOC" "$TASK_DOC_MANIFEST" "$TASK_RUNNER_SOURCE/SKILL.md" "$TASK_RUNNER_SOURCE/agents/openai.yaml" \
  "$TASK_BUNDLE_DIR/ios-app-listing/SKILL.md" \
  "$TASK_BUNDLE_DIR/ios-app-listing/references/output-contract.md" \
  "$TASK_BUNDLE_DIR/ios-app-listing/references/privacy-ai-rules.md" \
  "$TASK_BUNDLE_DIR/ios-app-listing/scripts/inspect_app.py" \
  "$TASK_BUNDLE_DIR/ios-app-listing/scripts/generate_app_listing.py" \
  "$TASK_BUNDLE_DIR/ios-app-listing/scripts/validate_site_publication_ready.py" \
  "$TASK_BUNDLE_DIR/ios-app-listing/scripts/render_app_listing.py" \
  "$TASK_BUNDLE_DIR/ios-app-listing/assets/site-render/templates-manifest.json"; do
  if [[ ! -f "$TASK_REQUIRED" ]]; then
    print -u2 -- "资料包不完整，缺少：$TASK_REQUIRED"
    print -u2 -- "请复制整个 Flutter工程 文件夹，不要只复制启动器或 Markdown。"
    exit 1
  fi
done

# Validate every ordered document before modifying the current installation.
TASK_DOCUMENTS=()
while IFS= read -r TASK_DOCUMENT || [[ -n "$TASK_DOCUMENT" ]]; do
  if [[ -z "$TASK_DOCUMENT" || "$TASK_DOCUMENT" != *.md || "$TASK_DOCUMENT" == */* || "$TASK_DOCUMENT" == *$'\r'* ]]; then
    print -u2 -- "文档清单含无效文件名，未更新技能：$TASK_DOC_MANIFEST"
    exit 1
  fi
  if (( ${TASK_DOCUMENTS[(Ie)$TASK_DOCUMENT]} > 0 )); then
    print -u2 -- "文档清单重复，未更新技能：$TASK_DOCUMENT"
    exit 1
  fi
  if [[ ! -f "$TASK_DOCS_DIR/$TASK_DOCUMENT" || -L "$TASK_DOCS_DIR/$TASK_DOCUMENT" ]]; then
    print -u2 -- "文档集不完整或含非普通文件，未更新技能：$TASK_DOCS_DIR/$TASK_DOCUMENT"
    exit 1
  fi
  TASK_DOCUMENTS+=("$TASK_DOCUMENT")
done < "$TASK_DOC_MANIFEST"
if (( ${#TASK_DOCUMENTS} < 2 )) || [[ "${TASK_DOCUMENTS[1]}" != '00-总入口.md' ]]; then
  print -u2 -- "文档清单必须先列总入口，再列全部正文：$TASK_DOC_MANIFEST"
  exit 1
fi

task_is_runner() {
  [[ -f "$1/SKILL.md" ]] && /usr/bin/grep -Eq '^name:[[:space:]]*flutter-engine-runner[[:space:]]*$' "$1/SKILL.md"
}

TASK_INSTALLED_DIR="$TASK_SKILLS_DIR/flutter-engine-runner"
# Reuse the original installation when present, avoiding duplicate skill names.
if task_is_runner "$TASK_SKILLS_DIR/flutter工程执行"; then
  TASK_INSTALLED_DIR="$TASK_SKILLS_DIR/flutter工程执行"
fi
if [[ -e "$TASK_INSTALLED_DIR" || -L "$TASK_INSTALLED_DIR" ]]; then
  if [[ -L "$TASK_INSTALLED_DIR" ]] || ! task_is_runner "$TASK_INSTALLED_DIR"; then
    print -u2 -- "安装目标已被其他目录或链接占用，未覆盖：$TASK_INSTALLED_DIR"
    exit 1
  fi
fi

TASK_BACKUP_ROOT="${TASK_SKILLS_DIR:h}/skill-backups/flutter-engine-runner"
mkdir -p "$TASK_SKILLS_DIR" "$TASK_BACKUP_ROOT"
TASK_STAGE="$(mktemp -d "$TASK_BACKUP_ROOT/staging.XXXXXX")"
mkdir -p "$TASK_STAGE/agents" "$TASK_STAGE/references"
cp "$TASK_RUNNER_SOURCE/SKILL.md" "$TASK_STAGE/SKILL.md"
cp "$TASK_RUNNER_SOURCE/agents/openai.yaml" "$TASK_STAGE/agents/openai.yaml"
cp "$TASK_DOC" "$TASK_STAGE/references/workflow.md"
cp -R "$TASK_DOCS_DIR" "$TASK_STAGE/references/工作流文档"
cp -R "$TASK_BUNDLE_DIR/ios-app-listing" "$TASK_STAGE/references/ios-app-listing"

TASK_PREVIOUS=""
if [[ -d "$TASK_INSTALLED_DIR" ]]; then
  TASK_PREVIOUS="$TASK_BACKUP_ROOT/previous-$(date +%Y%m%d-%H%M%S)-${TASK_STAGE:t}"
  mv "$TASK_INSTALLED_DIR" "$TASK_PREVIOUS"
fi
if ! mv "$TASK_STAGE" "$TASK_INSTALLED_DIR"; then
  if [[ -n "$TASK_PREVIOUS" && ! -e "$TASK_INSTALLED_DIR" ]]; then
    mv "$TASK_PREVIOUS" "$TASK_INSTALLED_DIR"
  fi
  print -u2 -- "安装失败；已恢复旧安装，暂存文件保留在：$TASK_STAGE"
  exit 1
fi

# Archive a second known registration rather than leave stale workflow rules.
for TASK_OLD_DIR in "$TASK_SKILLS_DIR/flutter-engine-runner" "$TASK_SKILLS_DIR/flutter工程执行"; do
  if [[ "$TASK_OLD_DIR" != "$TASK_INSTALLED_DIR" ]] && task_is_runner "$TASK_OLD_DIR"; then
    mv "$TASK_OLD_DIR" "$TASK_BACKUP_ROOT/duplicate-${TASK_OLD_DIR:t}-$(date +%Y%m%d-%H%M%S)-${TASK_STAGE:t}"
  fi
done

# Share the same installed copy with clients that discover user skills in .agents.
if (( ! TASK_CUSTOM_SKILLS )); then
  TASK_COMPAT_ROOT="$HOME/.agents/skills"
  TASK_COMPAT_LINK="$TASK_COMPAT_ROOT/flutter-engine-runner"
  mkdir -p "$TASK_COMPAT_ROOT"
  if [[ -L "$TASK_COMPAT_LINK" && "${TASK_COMPAT_LINK:A}" == "${TASK_INSTALLED_DIR:A}" ]]; then
    :
  elif [[ ! -e "$TASK_COMPAT_LINK" && ! -L "$TASK_COMPAT_LINK" ]]; then
    ln -s "$TASK_INSTALLED_DIR" "$TASK_COMPAT_LINK"
  elif task_is_runner "$TASK_COMPAT_LINK"; then
    mv "$TASK_COMPAT_LINK" "$TASK_BACKUP_ROOT/previous-agents-$(date +%Y%m%d-%H%M%S)-${TASK_STAGE:t}"
    ln -s "$TASK_INSTALLED_DIR" "$TASK_COMPAT_LINK"
  else
    print -u2 -- "保留已有的兼容目录：$TASK_COMPAT_LINK；请使用下方已安装技能。"
  fi
fi

TASK_PROMPT='使用 $flutter-engine-runner，请直接开始执行。缺少创意主题或项目名称时先询问；名称使用我提供的。按文档展示完整思维导图，确认后继续。不要询问项目位置；未指定时使用当前 Codex 工作目录，不在资料包或技能目录创建工程。'
if [[ -n "$TASK_PROJECT_DIR" ]]; then
  TASK_PROMPT+=" 本次完整目标工程目录：$TASK_PROJECT_DIR。"
fi

print -r -- "技能已安装：$TASK_INSTALLED_DIR"
print -r -- "总入口、$(( ${#TASK_DOCUMENTS} - 1 )) 份规范正文与 AppListing 已随技能复制，不依赖原机器用户名或 /Applications/config。"
if [[ -n "$TASK_PREVIOUS" ]]; then
  print -r -- "旧安装可恢复：$TASK_PREVIOUS"
fi
print -r -- "首次安装或更新后，请重新打开 Codex 并进入新对话，让技能重新加载。"
print -r -- "在技能列表搜索 Flutter 工程执行；也可粘贴并发送下面这句话："
print -r -- "$TASK_PROMPT"
print -r -- "若列表尚未出现，可明确发送：读取并使用 $TASK_INSTALLED_DIR/SKILL.md，开始执行工作流。"
print -r -- "工程目录以你在 Codex 中指定的位置为准；安装器不会创建 Flutter 项目。"

if (( ! TASK_INSTALL_ONLY && TASK_CLIPBOARD )) && command -v pbcopy >/dev/null 2>&1; then
  if print -rn -- "$TASK_PROMPT" | pbcopy; then
    print -r -- "启动语句已复制到剪贴板；在 Codex 输入框粘贴后发送。"
  fi
fi
if (( ! TASK_INSTALL_ONLY && TASK_OPEN )) && command -v open >/dev/null 2>&1; then
  open -a Codex 2>/dev/null || print -r -- "请手动打开 Codex。"
fi
