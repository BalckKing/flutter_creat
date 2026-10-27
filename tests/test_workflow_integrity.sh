#!/bin/zsh

emulate -L zsh
set -euo pipefail

TASK_ROOT="${0:A:h:h}"
TASK_DOCS_DIR="$TASK_ROOT/工作流文档"
TASK_MANIFEST="$TASK_DOCS_DIR/manifest.txt"
TASK_ORDER="$TASK_DOCS_DIR/09-实施顺序与交付报告.md"
TASK_START="$TASK_ROOT/start.sh"

fail() {
  print -u2 -- "FAIL: $1"
  exit 1
}

require_file() {
  [[ -f "$1" && ! -L "$1" ]] || fail "缺少普通文件：$1"
}

require_text() {
  local task_file="$1"
  local task_pattern="$2"
  rg -q -- "$task_pattern" "$task_file" || fail "缺少契约：$task_file：$task_pattern"
}

line_of() {
  local task_file="$1"
  local task_pattern="$2"
  rg -n -m 1 -- "$task_pattern" "$task_file" | cut -d: -f1
}

require_before() {
  local task_before="$1"
  local task_after="$2"
  local task_before_line task_after_line
  task_before_line="$(line_of "$TASK_ORDER" "$task_before" || true)"
  task_after_line="$(line_of "$TASK_ORDER" "$task_after" || true)"
  [[ -n "$task_before_line" && -n "$task_after_line" && "$task_before_line" -lt "$task_after_line" ]] || \
    fail "执行顺序错误：$task_before 必须在 $task_after 之前"
}

require_file "$TASK_MANIFEST"
require_file "$TASK_ORDER"
require_file "$TASK_START"

typeset -a task_expected_docs=(
  '00-总入口.md'
  '01-执行约定.md'
  '02-创意与思维导图.md'
  '03-产品定义与导航.md'
  '04-视觉与页面功能.md'
  '05-数据与工程架构.md'
  '06-素材与真实照片.md'
  '07-测试与质量验收.md'
  '08-发布与About材料.md'
  '09-实施顺序与交付报告.md'
  '10-第三方资源来源.md'
)
typeset -a task_manifest_docs=()
while IFS= read -r task_doc || [[ -n "$task_doc" ]]; do
  [[ -n "$task_doc" ]] || continue
  [[ "$task_doc" != */* && "$task_doc" == *.md ]] || fail "manifest 含无效条目：$task_doc"
  (( ${task_manifest_docs[(Ie)$task_doc]} == 0 )) || fail "manifest 含重复条目：$task_doc"
  task_manifest_docs+=("$task_doc")
  require_file "$TASK_DOCS_DIR/$task_doc"
done < "$TASK_MANIFEST"

[[ "${#task_manifest_docs}" -eq "${#task_expected_docs}" ]] || \
  fail "manifest 文档数量错误：期望 ${#task_expected_docs}，实际 ${#task_manifest_docs}"
for task_doc in "${task_expected_docs[@]}"; do
  (( ${task_manifest_docs[(Ie)$task_doc]} > 0 )) || fail "manifest 缺少：$task_doc"
done
[[ "${task_manifest_docs[1]}" == '00-总入口.md' ]] || fail 'manifest 第一项必须是 00-总入口.md'

for task_step in {1..20}; do
  rg -q -- "^${task_step}\\. " "$TASK_ORDER" || fail "实施顺序缺少第 ${task_step} 步"
done
[[ "$(rg -c -- '^([0-9]|1[0-9]|20)\. ' "$TASK_ORDER")" -ge 20 ]] || fail '实施顺序步骤数量不足'

require_text "$TASK_ORDER" '第 13 节是唯一的执行顺序'
require_text "$TASK_ORDER" '第 14 节是唯一的最终报告格式'
require_text "$TASK_ORDER" '本节只保留入口索引和跨文档的不可省略门槛'
require_text "$TASK_ORDER" '第 17 步先核对远程 checkout'
require_text "$TASK_ORDER" '^18\. .*生成 Review Remarks'
require_text "$TASK_ORDER" '^19\. .*最终图片加载检查'
require_text "$TASK_ORDER" '^20\. .*最终 iOS 权限校验'
require_text "$TASK_ORDER" '项目根目录.*aduit.*必须保留'
require_text "$TASK_ORDER" '依赖树和 App bundle 中的 `aduit/` 副本必须移除'
require_text "$TASK_ORDER" 'All URL.*四值.*逐字不变'
require_text "$TASK_ORDER" '缺少证据不能标为 `Verified`'

require_before '^17\. ' '^18\. \*\*验收首页引导页'
require_before '^18\. \*\*验收首页引导页' '^19\. \*\*最终图片加载检查'
require_before '^19\. \*\*最终图片加载检查' '^20\. \*\*最终 iOS 权限校验'
require_text "$TASK_ORDER" '引导页通过验收后.*生成不超过 4,000 字符的全英文'
require_text "$TASK_ORDER" '第 19 步之后、最终报告之前.*全部适用项完成后才提交最终报告'

require_text "$TASK_START" 'TASK_DOC_MANIFEST'
require_text "$TASK_START" 'TASK_RUNNER_SOURCE/scripts/validate_about_copy.py'
require_text "$TASK_START" 'TASK_DOCUMENTS'

task_execution_step_count() {
  local task_step="$1"
  awk -v task_step="$task_step" '
    /^## 13[.] / { in_execution=1; next }
    /^## 14[.] / { in_execution=0 }
    in_execution && $0 ~ ("^" task_step "[.] ") { count++ }
    END { print count + 0 }
  ' "$TASK_ORDER"
}
for task_step in {1..20}; do
  [[ "$(task_execution_step_count "$task_step")" -eq 1 ]] || fail "第 13 节的实施顺序缺少或重复第 ${task_step} 步"
done

print -r -- 'PASS: workflow manifest, 00-10 document set, steps 1-20, cross-document gates, and final-stage ordering are executable.'
