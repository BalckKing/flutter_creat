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
TASK_EXECUTION="$TASK_ROOT/工作流文档/01-执行约定.md"
TASK_ARCHITECTURE="$TASK_ROOT/工作流文档/05-数据与工程架构.md"
TASK_SOURCES="$TASK_ROOT/工作流文档/10-第三方资源来源.md"
TASK_SKILL="$TASK_ROOT/flutter-engine-runner/SKILL.md"
TASK_CODEX_SKILLS_ROOT="${CODEX_HOME:-$HOME/.codex}/skills"
TASK_INSTALLED_SKILL="$TASK_CODEX_SKILLS_ROOT/flutter工程执行/SKILL.md"
TASK_README="$TASK_ROOT/README.md"

task_require() {
  local task_file="$1"
  local task_pattern="$2"
  rg -q -- "$task_pattern" "$task_file" || {
    print -u2 -- "Missing onboarding-guide workflow requirement in $task_file: $task_pattern"
    return 1
  }
}

task_forbid() {
  local task_file="$1"
  local task_pattern="$2"
  if rg -q -- "$task_pattern" "$task_file"; then
    print -u2 -- "Conflicting onboarding-page rule in $task_file: $task_pattern"
    return 1
  fi
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
task_require "$TASK_IDEA" '不得采用简约线条.*色块'
task_require "$TASK_VISUAL" '鲜明、非单调的 Logo 配色'
task_require "$TASK_VISUAL" '恰好三个不同页面'
task_require "$TASK_VISUAL" '每次启动.*欢迎页.*`Continue`'
task_require "$TASK_VISUAL" '`Clear Data`.*成功.*初始化页.*`Entry`'
task_require "$TASK_VISUAL" '启动准备状态.*显示在欢迎页内部'
task_require "$TASK_VISUAL" '欢迎页.*不显示.*协议文案'
task_require "$TASK_VISUAL" '协议通用文案.*仅初始化页显示'
task_require "$TASK_VISUAL" '引导页不含.*协议通用文案'
task_require "$TASK_IDEA" 'Initialization 页底部显示两行通用协议文案并链接 Terms/Privacy；Welcome 欢迎页不显示该文案'
task_forbid "$TASK_IDEA" '引导页提供 Terms/Privacy 文本链接'
task_require "$TASK_VISUAL" '初始化页.*底部.*`By continuing, you agree to our`'
task_require "$TASK_VISUAL" '初始化页.*底部.*`Terms of Use and Privacy Policy`'
task_require "$TASK_VISUAL" '全项目.*多色渐变'
task_require "$TASK_VISUAL" '全项目.*Logo 派生.*渐变'
task_require "$TASK_VISUAL" 'AnimationController.*CustomPainter'
task_require "$TASK_VISUAL" 'onTapUp'
task_require "$TASK_VISUAL" '位置、速度、重力、颜色和拖尾'
task_require "$TASK_VISUAL" '减少动态.*粒子'
task_require "$TASK_VISUAL" '所有由 AI 生成.*不得使用简约线条.*色块'
task_require "$TASK_VISUAL" '标题的斜体与渐变.*同时使用.*Logo.*渐变文字'
task_require "$TASK_VISUAL" '至少三种有依据的字体风格'
task_require "$TASK_VISUAL" 'assets/logo\.png.*app_theme\.dart'
task_require "$TASK_VISUAL" 'common_module.*app_theme\.dart.*全局'
task_require "$TASK_VISUAL" '冷色主导.*重新生成或重选 Logo'
task_require "$TASK_VISUAL" '不过度鲜艳'
task_require "$TASK_MATERIALS" '不能呈现冷峻、灰暗或近乎单色的整体色调'
task_require "$TASK_MATERIALS" '多色平滑渐变'
task_require "$TASK_MATERIALS" '所有由 AI 生成并进入项目的图像.*简约线条/细轮廓.*色块堆叠'
task_require "$TASK_QA" '不能呈现冷峻或单调色调'
task_require "$TASK_QA" '初始化页视觉专项.*纯白色/近白空白画布'
task_require "$TASK_QA" '每次启动.*欢迎页.*`Continue`'
task_require "$TASK_QA" '清除成功后进入初始化页并显示 `Entry`'
task_require "$TASK_QA" '协议文案.*仅初始化页.*欢迎页.*不得显示'
task_require "$TASK_QA" '检查 AI 生成图不得使用简约线条.*色块'
task_require "$TASK_ORDER" 'Logo 色调鲜明且不单调'
task_require "$TASK_ORDER" '每次启动进入且含.*Flutter Welcome.*Clear Data.*清理成功后出现且含.*Flutter Initialization'
task_require "$TASK_ORDER" '准备步骤.*Welcome 页内状态'
task_require "$TASK_ORDER" 'Welcome 欢迎页、其 HTML 引导页和原生启动页均不得显示该协议文案'
task_require "$TASK_ORDER" '至少三种有意且可复用的字体风格'
task_require "$TASK_ORDER" 'assets/logo\.png.*common_module/theme/app_theme\.dart'
task_require "$TASK_ORDER" '冷色主导.*不进入主题令牌'
task_forbid "$TASK_ORDER" 'Flutter Loading 和初始化欢迎页|Loading 后显示 Entry|初始化欢迎页|成功返回欢迎页|清除并回欢迎页|引导页提供 Terms/Privacy 文本链接'
task_require "$TASK_SKILL" 'avoid a cold, austere, monochromatic look'
task_require "$TASK_SKILL" 'at least three distinct vivid color families'
task_require "$TASK_SKILL" 'Avoid minimalist line art, thin-outline-only artwork, flat geometric shapes, and color-block-only compositions'
task_require "$TASK_SKILL" 'There are exactly three distinct startup/return pages'
task_require "$TASK_SKILL" 'Every app launch enters the Welcome page with `Continue`'
task_require "$TASK_SKILL" 'Only after the user confirms `Clear Data` and clearing actually succeeds, show the separate Initialization page with `Entry`'
task_require "$TASK_SKILL" 'Only the Initialization page shows the bottom protocol agreement copy'
task_require "$TASK_SKILL" 'The Welcome page has no protocol agreement footer'
task_require "$TASK_SKILL" 'The onboarding guide contains no protocol agreement copy'
task_require "$TASK_SKILL" 'Protocol agreement text belongs only at the bottom of the separate Initialization page'
task_require "$TASK_SKILL" 'at least three intentional, reusable font treatments'
task_require "$TASK_SKILL" 'assets/logo\.png.*common_module/theme/app_theme\.dart'
task_require "$TASK_SKILL" 'cold-dominant.*regenerate or reselect the Logo'
task_require "$TASK_SKILL" 'not excessively saturated'
task_require "$TASK_README" '不能呈现冷峻、灰暗或近乎单色的整体色调'
task_require "$TASK_README" 'iOS 原生启动页.*欢迎页.*初始化页'
task_require "$TASK_README" '欢迎页.*不显示.*协议文本.*初始化页.*底部'
task_require "$TASK_README" '任何 AI 生成图都不得采用简约线条.*纯色块堆叠'
task_require "$TASK_README" 'AnimationController.*CustomPainter'
task_require "$TASK_README" 'onTapUp'
task_require "$TASK_README" '至少三种有意且可复用的字体风格'
task_require "$TASK_README" 'assets/logo\.png.*common_module/theme/app_theme\.dart'
task_require "$TASK_README" '冷色主导.*重新生成或重选 Logo'
task_require "$TASK_VISUAL" '每个 App 自有页面.*主题相关.*背景装饰图案'
task_require "$TASK_VISUAL" '使用 `http://stargate.local:3100/image` 生成.*背景装饰图案'
task_require "$TASK_VISUAL" '按页面 ID.*装饰素材.*实际引用'
task_require "$TASK_VISUAL" 'assets/backgrounds/<page_id>/<page_id>_background\.png'
task_require "$TASK_ARCHITECTURE" 'main\.dart.*仅负责.*启动'
task_require "$TASK_ARCHITECTURE" '每个实际 App 自有页面.*独立的 `lib/page_module'
task_require "$TASK_ARCHITECTURE" '页面清单.*对应 Dart 文件'
task_require "$TASK_ARCHITECTURE" '不得将多个路由页面集中写在'
task_require "$TASK_ARCHITECTURE" 'assets/backgrounds/<page_id>/<page_id>_background\.png'
task_require "$TASK_ARCHITECTURE" 'common_module/theme/app_theme\.dart'
task_require "$TASK_ARCHITECTURE" 'Logo.*app_theme\.dart.*全局'
task_require "$TASK_MATERIALS" '页面背景装饰.*Stargate'
task_require "$TASK_SOURCES" 'Stargate 图像生成入口：http://stargate.local:3100/image.*页面.*背景装饰图案'
task_require "$TASK_QA" '逐页面.*背景装饰.*素材路径'
task_require "$TASK_QA" '文件夹和命名.*page_id'
task_require "$TASK_ORDER" 'Stargate.*逐页主题背景装饰'
task_require "$TASK_SKILL" 'Use `http://stargate.local:3100/image` for the Logo and each App-owned page.*background decoration'
if [[ -f "$TASK_INSTALLED_SKILL" ]]; then
  task_require "$TASK_INSTALLED_SKILL" 'Use `http://stargate.local:3100/image` for the Logo and each App-owned page.*background decoration'
  task_require "$TASK_INSTALLED_SKILL" 'Stargate generates the Logo and page-specific UI background decorations'
  task_require "$TASK_INSTALLED_SKILL" 'Protocol agreement text belongs only at the bottom of the separate Initialization page'
  task_require "$TASK_INSTALLED_SKILL" 'The Welcome page and its HTML guide contain no protocol agreement copy'
  task_require "$TASK_INSTALLED_SKILL" 'Only after the user confirms `Clear Data` and clearing actually succeeds'
  task_require "$TASK_INSTALLED_SKILL" 'never attach particle effects to every button'
  task_require "$TASK_INSTALLED_SKILL" 'at least three intentional, reusable font treatments'
  if rg -q -- 'Stargate is Logo-only|Stargate-only Logo source|Stargate for Logo only' "$TASK_INSTALLED_SKILL"; then
    print -u2 -- "Conflicting installed-skill rule: Stargate may generate page decorations as well as the Logo."
    return 1
  fi
fi
task_require "$TASK_SKILL" 'Keep each page in its own focused Dart file organized by page ID'
task_require "$TASK_SKILL" 'verify that the corresponding page actually uses it as a low-opacity overlay or edge/border motif'
task_require "$TASK_README" '逐页主题化背景装饰'
task_require "$TASK_README" '每个独立 App 页面都使用自己的 Dart 文件'
task_require "$TASK_README" 'assets/backgrounds/<page_id>/<page_id>_background\.png'
task_require "$TASK_EXECUTION" '所有新建项目.*目标文件夹本身直接作为 Flutter 工程根目录'
task_require "$TASK_EXECUTION" '不要再创建或嵌套一个以项目名称命名的子文件夹'
task_require "$TASK_SKILL" 'The current newly created folder or explicitly specified target folder is always the app root itself'
task_require "$TASK_README" '当前新建或明确指定的工程文件夹本身就是工程根目录'
if rg -q -- 'create a user-named subdirectory|receives the user-named subdirectory|明确指定父目录时，才在其中创建.*子目录|否则创建同名子目录' "$TASK_SKILL" "$TASK_README"; then
  print -u2 -- 'Conflicting project-root rule: a selected/new target folder must not be wrapped in a project-name subdirectory.'
  return 1
fi

task_require "$TASK_PUBLISH" 'aduit/site/index\.html'
task_require "$TASK_PUBLISH" '完整英文产品介绍'
task_require "$TASK_PUBLISH" '目标用户和主要用途.*用户在什么场景遇到什么问题'
task_require "$TASK_PUBLISH" '每个主要模块至少写清'
task_require "$TASK_PUBLISH" '至少三个不同用户结果的任务'
task_require "$TASK_PUBLISH" '摄像机、相册与麦克风'
task_require "$TASK_PUBLISH" '数据、权限与服务边界'
task_require "$TASK_PUBLISH" 'URL 完整保护'
task_require "$TASK_PUBLISH" 'description_style_label` 必须与其实际选定结果一致'
task_require "$TASK_PUBLISH" '最多 4,000 字符'
task_require "$TASK_QA" 'Intro 描述深度专项'
task_require "$TASK_ORDER" 'description 由当前智能体按第 12\.1 节以真实功能充分展开'
task_require "$TASK_SKILL" 'fully describe the verified product experience'
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
task_require "$TASK_PUBLISH" '引导页不含协议通用文案'
task_require "$TASK_PUBLISH" '协议通用文案.*仅初始化页显示'
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
task_require "$TASK_ORDER" '主题元素.*覆盖模拟现实.*手绘.*油画.*艺术.*第五张'
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
task_require "$TASK_SKILL" 'Generate five independent Logo candidates from.*theme elements.*realism.*hand-drawn.*oil painting.*artistic expression.*fifth candidate'
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

task_require "$TASK_IDEA" '五张候选覆盖四种已约定画风'
task_require "$TASK_IDEA" 'c02.*手绘.*笔触.*层次.*简笔'
task_require "$TASK_MATERIALS" '主题元素.*模拟现实.*手绘.*油画.*艺术.*四种画风'
task_require "$TASK_ROOT/工作流文档/02-创意与思维导图.md" '避免明显 AI 生成感'
task_require "$TASK_ROOT/工作流文档/02-创意与思维导图.md" '禁止 3D'
task_require "$TASK_IDEA" '至少三个实际 Flutter 页面/组件消费 Logo 派生色'
task_require "$TASK_IDEA" '全项目主要页面.*Logo 主题色派生.*渐变.*至少两个真实可达.*主题粒子效果'
task_require "$TASK_VISUAL" 'Logo 原始 HEX → Flutter 主题令牌 → 实际页面/组件 → iPhone 截图'
task_require "$TASK_VISUAL" '全项目多使用与 Logo 派生主题色对应的协调多色渐变'
task_require "$TASK_VISUAL" '至少选择两个真实可达.*不得.*每个按钮'
task_require "$TASK_VISUAL" '高端 iPhone 目标'
task_require "$TASK_MATERIALS" '主页面、真实操作页和至少一个其他 App 页面'
task_require "$TASK_QA" '至少三个实际页面/组件的 iPhone 截图'
task_require "$TASK_ORDER" '截图证明主题令牌已被实际页面/组件消费'
task_require "$TASK_SKILL" 'at least three real App screens'
task_require "$TASK_SKILL" 'varied, coordinated gradients derived from the approved Logo palette'
task_require "$TASK_SKILL" 'AnimationController` and `CustomPainter`'
task_require "$TASK_SKILL" 'at the `onTapUp` coordinates'
task_require "$TASK_SKILL" 'at least two real, reachable, semantically different tap actions'
task_require "$TASK_SKILL" 'high-end iPhone hardware as the baseline'
task_require "$TASK_SKILL" 'never attach particle effects to every button'
task_require "$TASK_README" '至少三个实际 App 页面/组件'

# Final iOS permission review must catch a missing macro when the selected API requires it,
# while not requesting broad photo-library access for picker-only imports. ATT is removed
# from the no-tracking app rather than left as a dormant prompt path.
task_require "$TASK_EXECUTION" 'PERMISSION_PHOTOS=1'
task_require "$TASK_EXECUTION" 'PhotoKit'
task_require "$TASK_EXECUTION" '仅取得用户选中的项目.*不额外请求整库权限'
task_require "$TASK_QA" 'PERMISSION_PHOTOS=1'
task_require "$TASK_QA" 'Pods.*解析.*宏'
task_require "$TASK_QA" 'NSUserTrackingUsageDescription'
task_require "$TASK_QA" 'AppTrackingTransparency'
task_require "$TASK_QA" 'IDFA'
task_require "$TASK_ARCHITECTURE" '不启用.*ATT'
task_require "$TASK_SKILL" 'PERMISSION_PHOTOS=1'
task_require "$TASK_SKILL" 'NSUserTrackingUsageDescription'
task_require "$TASK_SKILL" 'AppTrackingTransparency'
task_require "$TASK_README" 'PERMISSION_PHOTOS=1'
task_require "$TASK_README" 'ATT.*移除'

print -r -- 'PASS: onboarding-guide content, exact placement, accessibility, acceptance order, Bridge fallback, and target viewports are specified across the workflow.'
