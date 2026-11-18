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
TASK_APP_LISTING_REPO="${FLUTTER_APP_LISTING_REPO:-git@codeup.aliyun.com:6366640f0cd435624679b545/Aurora/Agent/aurora_skills/ios-app-listing.git}"
TASK_APP_LISTING_BRANCH="feature/1.2.1-A1"
TASK_APP_LISTING_FALLBACK="${FLUTTER_APP_LISTING_FALLBACK:-/Users/admin/Desktop/config/ios-app-listing}"
TASK_APP_LISTING_COMMIT=""
TASK_APP_LISTING_SOURCE=""
TASK_APP_LISTING_MODE=""
TASK_APP_LISTING_CHECKOUT_BRANCH=""
TASK_APP_LISTING_OPTIONAL_VALIDATOR="not-run"
TASK_STAGE=""
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

for TASK_REQUIRED in "$TASK_DOC" "$TASK_DOC_MANIFEST" "$TASK_RUNNER_SOURCE/SKILL.md" "$TASK_RUNNER_SOURCE/agents/openai.yaml" "$TASK_RUNNER_SOURCE/scripts/validate_about_copy.py" "$TASK_RUNNER_SOURCE/scripts/validate_visual_implementation.py" "$TASK_RUNNER_SOURCE/scripts/validate_review_remarks.py" "$TASK_RUNNER_SOURCE/scripts/validate_public_copy.py" "$TASK_RUNNER_SOURCE/scripts/validate_path_names.py" "$TASK_RUNNER_SOURCE/scripts/prepare_ios_config.py" "$TASK_RUNNER_SOURCE/scripts/prepare_git_handoff.py" "$TASK_RUNNER_SOURCE/scripts/prepare_asset_staging.py" "$TASK_RUNNER_SOURCE/scripts/validate_asset_staging.py" "$TASK_RUNNER_SOURCE/scripts/cleanup_generation_history.py" "$TASK_RUNNER_SOURCE/scripts/validate_flutter_navigation.py" "$TASK_RUNNER_SOURCE/scripts/validate_protocol_urls.py" "$TASK_RUNNER_SOURCE/scripts/validate_launch_screen_visual.py" "$TASK_RUNNER_SOURCE/scripts/validate_game_project.py" "$TASK_RUNNER_SOURCE/scripts/validate_work_records.py" "$TASK_RUNNER_SOURCE/scripts/validate_ios_artifacts.py" "$TASK_RUNNER_SOURCE/scripts/validate_aduit_allowlist.py" "$TASK_RUNNER_SOURCE/scripts/validate_welcome_flow.py" "$TASK_RUNNER_SOURCE/scripts/validate_execution_state.py" "$TASK_RUNNER_SOURCE/scripts/validate_capability_matrix.py" "$TASK_RUNNER_SOURCE/scripts/validate_quality_records.py" "$TASK_RUNNER_SOURCE/scripts/validate_logo_quality.py" "$TASK_RUNNER_SOURCE/scripts/validate_release_readiness.py"; do
  if [[ ! -f "$TASK_REQUIRED" ]]; then
    print -u2 -- "资料包不完整，缺少：$TASK_REQUIRED"
    print -u2 -- "请复制整个 Flutter工程 文件夹，不要只复制启动器或 Markdown。"
    exit 1
  fi
done

TASK_BUNDLE_CHECK_LAYOUT="$TASK_BUNDLE_DIR/flutter_done_check/test_bundle_layout.sh"
if [[ ! -f "$TASK_BUNDLE_CHECK_LAYOUT" || -L "$TASK_BUNDLE_CHECK_LAYOUT" ]]; then
  print -u2 -- "资料包不完整，缺少检查目录布局检查：$TASK_BUNDLE_CHECK_LAYOUT"
  exit 1
fi
if ! /bin/zsh "$TASK_BUNDLE_CHECK_LAYOUT"; then
  print -u2 -- "检查目录布局检查失败；未更新技能安装。"
  exit 1
fi

TASK_WORKFLOW_INTEGRITY="$TASK_BUNDLE_DIR/flutter_done_check/test_workflow_integrity.sh"
if [[ ! -f "$TASK_WORKFLOW_INTEGRITY" || -L "$TASK_WORKFLOW_INTEGRITY" ]]; then
  print -u2 -- "资料包不完整，缺少工作流完整性检查：$TASK_WORKFLOW_INTEGRITY"
  exit 1
fi
if ! /bin/zsh "$TASK_WORKFLOW_INTEGRITY"; then
  print -u2 -- "工作流完整性检查失败；未更新技能安装。"
  exit 1
fi

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
task_cleanup_staging() {
  if [[ -n "$TASK_STAGE" && -d "$TASK_STAGE" ]]; then
    rm -rf -- "$TASK_STAGE"
  fi
}
trap task_cleanup_staging EXIT

mkdir -p "$TASK_STAGE/agents" "$TASK_STAGE/references"
cp "$TASK_RUNNER_SOURCE/SKILL.md" "$TASK_STAGE/SKILL.md"
cp "$TASK_RUNNER_SOURCE/agents/openai.yaml" "$TASK_STAGE/agents/openai.yaml"
cp -R "$TASK_RUNNER_SOURCE/scripts" "$TASK_STAGE/scripts"
cp "$TASK_DOC" "$TASK_STAGE/references/workflow.md"
cp -R "$TASK_DOCS_DIR" "$TASK_STAGE/references/工作流文档"

TASK_APP_LISTING_DIR="$TASK_STAGE/references/ios-app-listing"
TASK_GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -o BatchMode=yes -o ConnectTimeout=10}"
task_listing_source_complete() {
  local task_listing_root="$1"
  [[ -d "$task_listing_root" ]] || return 1
  for TASK_LISTING_REQUIRED in \
    SKILL.md \
    references/output-contract.md \
    references/privacy-ai-rules.md \
    scripts/inspect_app.py \
    scripts/generate_app_listing.py \
    scripts/render_app_listing.py \
    assets/site-render/templates-manifest.json; do
    [[ -f "$task_listing_root/$TASK_LISTING_REQUIRED" ]] || return 1
  done
}

task_record_listing_source() {
  local task_listing_root="$1"
  if git -C "$task_listing_root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    TASK_APP_LISTING_CHECKOUT_BRANCH="$(git -C "$task_listing_root" branch --show-current)"
    TASK_APP_LISTING_COMMIT="$(git -C "$task_listing_root" rev-parse HEAD)"
  else
    TASK_APP_LISTING_CHECKOUT_BRANCH="unversioned"
    TASK_APP_LISTING_COMMIT="unversioned"
  fi
  if [[ -f "$task_listing_root/scripts/validate_site_publication_ready.py" ]]; then
    TASK_APP_LISTING_OPTIONAL_VALIDATOR="available"
  else
    TASK_APP_LISTING_OPTIONAL_VALIDATOR="missing; use the available output-contract and rendered-page checks"
    print -u2 -- "提示：所选 ios-app-listing 来源没有可选的 validate_site_publication_ready.py；继续使用其余生成器，并对全部产物执行现有契约检查与人工页面复核。"
  fi
}

if GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="$TASK_GIT_SSH_COMMAND" git clone \
  --branch "$TASK_APP_LISTING_BRANCH" --single-branch "$TASK_APP_LISTING_REPO" "$TASK_APP_LISTING_DIR"; then
  if [[ "$(git -C "$TASK_APP_LISTING_DIR" branch --show-current)" == "$TASK_APP_LISTING_BRANCH" ]] && \
    task_listing_source_complete "$TASK_APP_LISTING_DIR"; then
    TASK_APP_LISTING_SOURCE="$TASK_APP_LISTING_REPO"
    TASK_APP_LISTING_MODE="remote"
    task_record_listing_source "$TASK_APP_LISTING_DIR"
  else
    print -u2 -- "远程 ios-app-listing 检出不完整或分支不匹配，将尝试本机后备目录。"
    rm -rf -- "$TASK_APP_LISTING_DIR"
  fi
else
  print -u2 -- "远程同步失败：无法获取 ios-app-listing 分支 $TASK_APP_LISTING_BRANCH；将尝试后备生成。"
  rm -rf -- "$TASK_APP_LISTING_DIR"
fi

if [[ -z "$TASK_APP_LISTING_SOURCE" ]] && task_listing_source_complete "$TASK_APP_LISTING_FALLBACK"; then
  ln -s "$TASK_APP_LISTING_FALLBACK" "$TASK_APP_LISTING_DIR"
  TASK_APP_LISTING_SOURCE="$TASK_APP_LISTING_FALLBACK"
  TASK_APP_LISTING_MODE="local-fallback"
  task_record_listing_source "$TASK_APP_LISTING_FALLBACK"
  print -r -- "已切换到本机 ios-app-listing 后备生成：$TASK_APP_LISTING_FALLBACK"
fi

if [[ -z "$TASK_APP_LISTING_SOURCE" ]]; then
  TASK_APP_LISTING_MODE="contract-fallback"
  TASK_APP_LISTING_CHECKOUT_BRANCH="none"
  TASK_APP_LISTING_OPTIONAL_VALIDATOR="unavailable"
  print -u2 -- "远程与本机 ios-app-listing 来源均不可用；仍安装核心流程，并按随包生成契约继续完成 AppListing、About、aduit 整理、引导页与 Review Remarks。"
  print -r -- "不得因此停止或等待用户；逐项完成可交付产物，未通过的校验如实标记，不得伪报通过。具体错误与验证结果写入目标工程 .codex-work/。"
fi

print -r -- "远程同步失败时使用 $TASK_APP_LISTING_FALLBACK；所有 AppListing、About 与 Review Remarks 任务继续执行。"
print -r -- "local_generation_complete、failures 与 verification 状态必须分开记录，不得将未验证结果伪报为通过。" \
  > "$TASK_STAGE/references/app-listing-fallback-contract.md"
print -r -- "source=$TASK_APP_LISTING_SOURCE" > "$TASK_STAGE/references/ios-app-listing-source.txt"
print -r -- "mode=$TASK_APP_LISTING_MODE" >> "$TASK_STAGE/references/ios-app-listing-source.txt"
print -r -- "branch=$TASK_APP_LISTING_BRANCH" >> "$TASK_STAGE/references/ios-app-listing-source.txt"
print -r -- "checkout_branch=$TASK_APP_LISTING_CHECKOUT_BRANCH" >> "$TASK_STAGE/references/ios-app-listing-source.txt"
print -r -- "commit=$TASK_APP_LISTING_COMMIT" >> "$TASK_STAGE/references/ios-app-listing-source.txt"
print -r -- "optional_publication_validator=$TASK_APP_LISTING_OPTIONAL_VALIDATOR" >> "$TASK_STAGE/references/ios-app-listing-source.txt"

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

TASK_PROMPT='使用 $flutter-engine-runner，请直接开始执行。将项目名称、创意主题、性能与功能目标水平、Git 仓库地址一并收集，仓库地址由我提供主题时一起给出，只询问缺失项；名称使用我提供的。性能请完整列出 1 极低、2 低、3 中、4 高（推荐、默认）、5 极高五个选项让我直接选择编号或档名，不要求我手写参数、具体机型或功能标准；功能目标由你按主题自动制定。性能档位未明确时采用高档（默认），针对性能说“不在乎/无限制”等意思映射极高档，已有选择不要重问。按文档为每页分别生成最详细的思维导图和执行文档，分开保存；展示全部页面图、执行文档链接和目标验收标准，整体确认后继续。不要询问项目位置；未指定时使用当前 Codex 工作目录，不在资料包或技能目录创建工程。游戏是可选主题：只有我选择游戏主题或创意明确包含真实游戏模块时，先判断是否需要专用引擎；持续世界、实时物理/碰撞、复杂3D、高频实体或编辑器导出管线使用精确版本的 Flame/Godot/Unity 等引擎，回合制、卡牌、问答、轻量棋盘和有限状态解谜可用 Flutter 原生实现。将 implementation_mode、engine_required 和 decision_reason 写入 .codex-work/game-engine.json；引擎路线完成引擎垂直切片，Flutter 原生路线完成 Flutter 规则垂直切片，并使用动画/效果目录和六部分效果提示词公式，二者都要真实输入、规则、结果、反馈和重开；非游戏项目不接入游戏引擎或游戏专项验收，但必须选择主题匹配的真实地图 SDK/瓦片、图表、媒体、3D、时间线或其他工具，记录 capability、real_tool_or_sdk、version、license/source、actual_consumer、fallback、runtime_evidence、formula_record；禁止线条地图、色块地图、静态地图截图、假坐标网格，组件目录不等于全量安装清单；按主题使用贴题本地动态图和真实数据能力；每个项目独立设计架构、导航和视觉样式，并按工作流验收。项目自有文件夹和文件名禁止Codex/AI相关词，开发记录统一.codex-work/并执行命名检查；项目UI自主创作，以完整成品的美观与精修证据验收，不套固定外观；每页保留真实半透明主题图片点缀，与背景动画同时呈现，按当前构建逐页检查；生图网站/工具不要求统一，按题材选择，以精致美观和主题质量验收。全部验收、修复复验及五张最终截图通过后，最后关联我提供的 Git 仓库地址，创建并切换 feat/1.0.0 分支；不暂存、不提交、不推送代码，等待我自行提交。'
if [[ -n "$TASK_PROJECT_DIR" ]]; then
  TASK_PROMPT+=" 本次完整目标工程目录：$TASK_PROJECT_DIR。"
fi

print -r -- "技能已安装：$TASK_INSTALLED_DIR"
if [[ -n "$TASK_APP_LISTING_SOURCE" ]]; then
  print -r -- "AppListing 技能来源：$TASK_APP_LISTING_SOURCE ($TASK_APP_LISTING_MODE; $TASK_APP_LISTING_BRANCH @ $TASK_APP_LISTING_COMMIT)"
else
  print -r -- "AppListing 技能来源：未取得 checkout；已启用本地生成后备契约"
fi
print -r -- "总入口与 $(( ${#TASK_DOCUMENTS} - 1 )) 份规范正文已安装；AppListing 来源顺序为远程指定分支，失败时自动使用 $TASK_APP_LISTING_FALLBACK，再失败时按本地生成契约继续。"
if [[ -n "$TASK_PREVIOUS" ]]; then
  print -r -- "旧安装可恢复：$TASK_PREVIOUS"
fi
print -r -- "首次安装或更新后，请重新打开 Codex 并进入新对话，让技能重新加载。"
print -r -- "在技能列表搜索 Flutter 工程执行；也可粘贴并发送下面这句话："
print -r -- "$TASK_PROMPT"
print -r -- "若列表尚未出现，可明确发送：读取并使用 $TASK_INSTALLED_DIR/SKILL.md，开始执行工作流。"
print -r -- "工程目录以你在 Codex 中指定的位置为准；安装器不会创建 Flutter 项目。"
print -r -- "导航硬门槛：全项目禁止 GetX，必须使用 Flutter 原生 Navigator；可运行 validate_flutter_navigation.py 验收。"

if (( ! TASK_INSTALL_ONLY && TASK_CLIPBOARD )) && command -v pbcopy >/dev/null 2>&1; then
  if print -rn -- "$TASK_PROMPT" | pbcopy; then
    print -r -- "启动语句已复制到剪贴板；在 Codex 输入框粘贴后发送。"
  fi
fi
if (( ! TASK_INSTALL_ONLY && TASK_OPEN )) && command -v open >/dev/null 2>&1; then
  open -a Codex 2>/dev/null || print -r -- "请手动打开 Codex。"
fi
