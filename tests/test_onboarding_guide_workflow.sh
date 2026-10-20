#!/bin/zsh

emulate -L zsh
set -euo pipefail

TASK_ROOT="${0:A:h:h}"
TASK_MATERIALS="$TASK_ROOT/工作流文档/06-素材与真实照片.md"
TASK_PUBLISH="$TASK_ROOT/工作流文档/08-发布与About材料.md"
TASK_QA="$TASK_ROOT/工作流文档/07-测试与质量验收.md"
TASK_ORDER="$TASK_ROOT/工作流文档/09-实施顺序与交付报告.md"
TASK_ENTRY="$TASK_ROOT/工作流文档/00-总入口.md"
TASK_SKILL="$TASK_ROOT/flutter-engine-runner/SKILL.md"
TASK_README="$TASK_ROOT/README.md"

task_require() {
  local task_file="$1"
  local task_pattern="$2"
  rg -q -- "$task_pattern" "$task_file" || {
    print -u2 -- "Missing onboarding-guide workflow requirement in $task_file: $task_pattern"
    return 1
  }
}

task_ordered() {
  local task_file="$1"
  local task_before="$2"
  local task_after="$3"
  local task_before_line task_after_line
  task_before_line="$(rg -o -b --no-filename -- "$task_before" "$task_file" | head -n 1 | cut -d: -f1 || true)"
  task_after_line="$(rg -o -b --no-filename -- "$task_after" "$task_file" | head -n 1 | cut -d: -f1 || true)"
  [[ -n "$task_before_line" && -n "$task_after_line" && "$task_before_line" -lt "$task_after_line" ]] || {
    print -u2 -- "Incorrect onboarding-guide order in $task_file: '$task_before' must precede '$task_after'."
    return 1
  }
}

task_require "$TASK_PUBLISH" 'aduit/site/index\.html'
task_require "$TASK_PUBLISH" '3–5 张真实介绍卡片'
task_require "$TASK_PUBLISH" '单一自包含 HTML 文件'
task_require "$TASK_PUBLISH" '262,144 字节'
task_require "$TASK_PUBLISH" 'viewport-fit=cover'
task_require "$TASK_PUBLISH" 'safe-area-inset-top'
task_require "$TASK_PUBLISH" 'safe-area-inset-bottom'
task_require "$TASK_PUBLISH" 'AppBridge\.postMessage'
task_require "$TASK_PUBLISH" 'function continueToApp\(\)'
task_require "$TASK_PUBLISH" "window\.AppBridge && typeof window\.AppBridge\.postMessage === 'function'"
task_require "$TASK_PUBLISH" "window\.AppBridge\.postMessage\('continue'\);"
task_require "$TASK_PUBLISH" "window\.location\.href = 'go://continue';"
task_require "$TASK_PUBLISH" 'go://continue'
task_require "$TASK_PUBLISH" '页面不存在外部资源请求'
task_require "$TASK_PUBLISH" '390×667'
task_require "$TASK_PUBLISH" '390×844'
task_require "$TASK_PUBLISH" '1024×768'
task_require "$TASK_PUBLISH" '1440×900'
task_require "$TASK_PUBLISH" '自动轮播'
task_require "$TASK_PUBLISH" '可点击且有可访问名称的分页圆点'
task_require "$TASK_PUBLISH" 'prefers-reduced-motion'
task_require "$TASK_PUBLISH" '无句末句号'
task_require "$TASK_PUBLISH" 'By continuing, you agree to our'
task_require "$TASK_PUBLISH" 'Terms of Use and Privacy Policy'
task_require "$TASK_PUBLISH" '在这些检查完成前不得开始 Review Remarks'
task_ordered "$TASK_PUBLISH" '引导页验收时核对文案结构' '原始 URL 的注册及两个目标的绑定'

task_require "$TASK_QA" '390×667'
task_require "$TASK_QA" '1440×900'
task_require "$TASK_QA" 'Bridge 可用时仅发送一次'
task_require "$TASK_QA" 'go://continue'
task_require "$TASK_QA" 'prefers-reduced-motion'
task_require "$TASK_MATERIALS" '本地依赖'
task_require "$TASK_MATERIALS" '依赖目录与 App bundle 中不得残留.*aduit'
task_require "$TASK_MATERIALS" '项目根目录.*aduit.*保留'
task_require "$TASK_MATERIALS" 'assets/logo\.png'
task_require "$TASK_MATERIALS" 'All URL.*原始地址'
task_require "$TASK_MATERIALS" '协议 HTML.*不复制或打包进 Flutter 依赖'
task_require "$TASK_MATERIALS" '不访问或探测真实 URL'
task_require "$TASK_ORDER" 'aduit/site/index\.html'
task_ordered "$TASK_ORDER" '17\. 按第 12\.1 节先核对' '18\. \*\*验收首页引导页'
task_ordered "$TASK_ORDER" '18\. \*\*验收首页引导页' '19\. \*\*最终图片加载检查'
task_ordered "$TASK_ORDER" '引导页通过验收后' '生成不超过 4,000 字符的全英文'
task_require "$TASK_ORDER" '依赖树.*aduit.*不得残留'
task_require "$TASK_ORDER" '项目根目录.*aduit.*保留'
task_require "$TASK_ORDER" 'All URL.*原始地址'
task_require "$TASK_ORDER" '不访问或探测真实 URL'
task_require "$TASK_ENTRY" '首页引导页'
task_require "$TASK_ENTRY" '依赖.*aduit.*不得残留'
task_require "$TASK_SKILL" 'aduit/site/index\.html'
task_require "$TASK_SKILL" 'window\.AppBridge\.postMessage\('
task_require "$TASK_SKILL" 'go://continue'
task_require "$TASK_SKILL" 'prefers-reduced-motion'
task_require "$TASK_SKILL" '1440×900'
task_require "$TASK_SKILL" '^7\. After every implementation'
task_require "$TASK_SKILL" 'local dependency.*aduit'
task_require "$TASK_SKILL" 'root.*aduit.*preserv'
task_require "$TASK_SKILL" 'assets/logo\.png'
task_require "$TASK_SKILL" 'raw URLs.*All URL'
task_require "$TASK_SKILL" 'Protocol HTML.*dependenc'
task_require "$TASK_SKILL" 'Do not visit or probe real URLs'
task_require "$TASK_SKILL" 'Do not add a duplicate HTML file'
task_ordered "$TASK_SKILL" '5\. Immediately after that rename' '6\. After the guide is accepted'
task_ordered "$TASK_SKILL" '6\. After the guide is accepted' '7\. After every implementation'
task_require "$TASK_SKILL" 'bind each to its corresponding raw URL'
task_require "$TASK_README" '引导页'
task_require "$TASK_README" '依赖.*aduit.*不得残留'

print -r -- 'PASS: onboarding-guide content, exact placement, accessibility, acceptance order, Bridge fallback, and target viewports are specified across the workflow.'
