#!/bin/zsh

emulate -L zsh
set -euo pipefail

TASK_ROOT="${0:A:h:h}"
TASK_IDEA="$TASK_ROOT/工作流文档/02-创意与思维导图.md"
TASK_VISUAL="$TASK_ROOT/工作流文档/04-视觉与页面功能.md"
TASK_MATERIALS="$TASK_ROOT/工作流文档/06-素材与真实照片.md"
TASK_PUBLISH="$TASK_ROOT/工作流文档/08-发布与About材料.md"
TASK_PRODUCT="$TASK_ROOT/工作流文档/03-产品定义与导航.md"
TASK_DESIGN="$TASK_ROOT/工作流文档/04-视觉与页面功能.md"
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

task_require "$TASK_IDEA" '不能呈现冷峻、灰暗或近乎单色的整体色调'
task_require "$TASK_IDEA" '至少三种清晰可辨的鲜明色彩'
task_require "$TASK_IDEA" '多色平滑渐变'
task_require "$TASK_VISUAL" '鲜明、非单调的 Logo 配色'
task_require "$TASK_MATERIALS" '不能呈现冷峻、灰暗或近乎单色的整体色调'
task_require "$TASK_MATERIALS" '多色平滑渐变'
task_require "$TASK_QA" '不能呈现冷峻或单调色调'
task_require "$TASK_ORDER" 'Logo 色调鲜明且不单调'
task_require "$TASK_SKILL" 'avoid a cold, austere, monochromatic look'
task_require "$TASK_SKILL" 'at least three distinct vivid color families'
task_require "$TASK_README" '不能呈现冷峻、灰暗或近乎单色的整体色调'

task_require "$TASK_PUBLISH" 'aduit/site/index\.html'
task_require "$TASK_PUBLISH" '3–5 张真实介绍卡片'
task_require "$TASK_PUBLISH" '单一自包含 HTML 文件'
task_require "$TASK_PUBLISH" '每张需在引导页显示的图片.*Base64 data URI.*直接内嵌在同一个 `aduit/site/index\.html`'
task_require "$TASK_PUBLISH" '不得让 `index\.html` 引用 Flutter assets、工程内相对图片路径、`file://` 路径或远程图片 URL'
task_require "$TASK_PUBLISH" 'site/img/logo\.png.*交付白名单保留.*内嵌数据'
task_require "$TASK_PUBLISH" '包含所有 Base64 图片内容'
task_require "$TASK_PUBLISH" '逐个解码.*Base64.*确认图像格式、尺寸与可读性'
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
task_require "$TASK_QA" 'Base64 图片内容'
task_require "$TASK_QA" '逐个解码并确认图像格式、尺寸与可读性'
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
task_require "$TASK_MATERIALS" '禁止 3D'
task_require "$TASK_MATERIALS" '明显 AI 生成感'
task_require "$TASK_ORDER" 'aduit/site/index\.html'
task_require "$TASK_ORDER" 'Base64 data URI'
task_require "$TASK_ORDER" 'UTF-8 字节数.*262,144'
task_ordered "$TASK_ORDER" '17\. 按第 12\.1 节先核对' '18\. \*\*验收首页引导页'
task_ordered "$TASK_ORDER" '18\. \*\*验收首页引导页' '19\. \*\*最终图片加载检查'
task_ordered "$TASK_ORDER" '引导页通过验收后' '生成不超过 4,000 字符的全英文'
task_require "$TASK_ORDER" '禁止 3D'
task_require "$TASK_ORDER" '主题元素.*模拟现实.*手绘.*油画.*艺术.*选定一种主画风'
task_require "$TASK_ORDER" '依赖树.*aduit.*不得残留'
task_require "$TASK_ORDER" '项目根目录.*aduit.*保留'
task_require "$TASK_ORDER" 'All URL.*原始地址'
task_require "$TASK_ORDER" '不访问或探测真实 URL'
task_require "$TASK_ENTRY" '首页引导页'
task_require "$TASK_ENTRY" 'Base64 data URI'
task_require "$TASK_ENTRY" '依赖.*aduit.*不得残留'
task_require "$TASK_PRODUCT" 'Base64 data URI'
task_require "$TASK_DESIGN" 'Base64 data URI'
task_require "$TASK_SKILL" 'aduit/site/index\.html'
task_require "$TASK_SKILL" 'Embed every displayed guide image.*directly in.*index\.html.*as a Base64 data URI'
task_require "$TASK_SKILL" 'Do not reference project assets, relative image files, `file://` URLs, or remote image URLs'
task_require "$TASK_SKILL" 'Count all Base64 image payload bytes against the 262144-byte limit'
task_require "$TASK_SKILL" 'Decode and inspect every embedded image'
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
task_require "$TASK_SKILL" 'Choose one primary style from.*realism.*hand-drawn.*oil painting.*artistic expression.*theme elements'
task_require "$TASK_SKILL" 'Avoid a conspicuous AI-generated look'
task_require "$TASK_SKILL" 'forbid 3D'
task_ordered "$TASK_SKILL" '5\. Immediately after that rename' '6\. After the guide is accepted'
task_ordered "$TASK_SKILL" '6\. After the guide is accepted' '7\. After every implementation'
task_require "$TASK_SKILL" 'bind each to its corresponding raw URL'
task_require "$TASK_README" '引导页'
task_require "$TASK_README" 'Base64 data URI'
task_require "$TASK_README" '依赖.*aduit.*不得残留'
task_require "$TASK_README" '主题元素.*模拟现实画风.*手绘画风.*油画画风.*艺术画风'
task_require "$TASK_README" '禁止 3D'
task_require "$TASK_README" '明显 AI 生成感'

task_require "$TASK_IDEA" '主题元素.*模拟现实画风.*手绘画风.*油画画风.*艺术画风'
task_require "$TASK_IDEA" '手绘画风.*精细线条.*不采用粗糙简笔'
task_require "$TASK_MATERIALS" '主题元素.*模拟现实.*手绘.*油画.*艺术.*四种画风'
task_require "$TASK_ROOT/工作流文档/02-创意与思维导图.md" '避免明显 AI 生成感'
task_require "$TASK_ROOT/工作流文档/02-创意与思维导图.md" '禁止 3D'
task_require "$TASK_IDEA" '至少三个实际 Flutter 页面/组件消费 Logo 派生色'
task_require "$TASK_VISUAL" 'Logo 原始 HEX → Flutter 主题令牌 → 实际页面/组件 → iPhone 截图'
task_require "$TASK_MATERIALS" '主页面、真实操作页和至少一个其他 App 页面'
task_require "$TASK_QA" '至少三个实际页面/组件的 iPhone 截图'
task_require "$TASK_ORDER" '截图证明主题令牌已被实际页面/组件消费'
task_require "$TASK_SKILL" 'at least three real App screens'
task_require "$TASK_README" '至少三个实际 App 页面/组件'

print -r -- 'PASS: onboarding-guide content, exact placement, accessibility, acceptance order, Bridge fallback, and target viewports are specified across the workflow.'
