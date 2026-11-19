#!/bin/zsh

emulate -L zsh
set -euo pipefail

TASK_ROOT="${0:A:h:h}"
TASK_README="$TASK_ROOT/README.md"
TASK_START="$TASK_ROOT/start.sh"
TASK_SKILL="$TASK_ROOT/flutter-engine-runner/SKILL.md"
TASK_YAML="$TASK_ROOT/flutter-engine-runner/agents/openai.yaml"
TASK_PLANNING="$TASK_ROOT/工作流文档/02-创意与思维导图.md"
TASK_QA="$TASK_ROOT/工作流文档/07-测试与质量验收.md"

fail() {
  print -u2 -- "FAIL: $1"
  exit 1
}

typeset -a task_files=(
  "$TASK_README"
  "$TASK_START"
  "$TASK_SKILL"
  "$TASK_YAML"
  "$TASK_PLANNING"
  "$TASK_QA"
)

for task_file in "${task_files[@]}"; do
  [[ -f "$task_file" ]] || fail "缺少目标文件：$task_file"
done

rg -q '4 · 高（推荐、默认）' "$TASK_README" || fail 'README 未将第 4 档标为推荐默认'
rg -q '4 高（推荐、默认）' "$TASK_START" || fail 'start.sh 未将第 4 档标为推荐默认'
rg -q '4 高（推荐、默认）' "$TASK_YAML" || fail 'openai.yaml 未将第 4 档标为推荐默认'
rg -q '4 高' "$TASK_SKILL" || fail 'SKILL.md 未列出第 4 档高端机型'
rg -q 'high-end, recommended/default' "$TASK_SKILL" || fail 'SKILL.md 未将第 4 档标为推荐默认'
rg -q 'option 4 \(`high-end`\) as the default' "$TASK_SKILL" || fail 'SKILL.md 缺少 option 4 默认映射'
rg -q 'Target iPhone tier: high-end' "$TASK_PLANNING" || fail '规划文档缺少 high-end 目标记录'
rg -q '默认高档' "$TASK_QA" || fail '验收文档缺少默认高档规则'

typeset -a task_legacy=(
  '中（推荐、默认）'
  '中（推荐默认）'
  '默认中端'
  '默认中档'
  '默认推荐中档'
  'mid-range, recommended/default'
  'mid-range by default'
)
for task_pattern in "${task_legacy[@]}"; do
  if rg -q -F -- "$task_pattern" "${task_files[@]}"; then
    fail "残留第 3 档默认规则：$task_pattern"
  fi
done

print -r -- 'PASS: performance tier 4 is the default and tier 3 remains explicit-only.'
