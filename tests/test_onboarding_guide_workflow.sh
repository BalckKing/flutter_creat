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
task_require "$TASK_VISUAL" '每次启动.*Welcome.*`Continue`'
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
task_require "$TASK_QA" '每次启动.*Welcome.*`Continue`'
task_require "$TASK_QA" '清除成功后进入初始化页并显示 `Entry`'
task_require "$TASK_QA" '协议文案.*仅初始化页.*欢迎页.*不得显示'
task_require "$TASK_QA" '检查 AI 生成图不得使用简约线条.*色块'
task_require "$TASK_ORDER" 'Logo 色调鲜明且不单调'
task_require "$TASK_ORDER" '每次启动进入且含.*Flutter Welcome.*Clear Data.*清理成功后出现且含.*Flutter Initialization'
task_require "$TASK_ORDER" '准备步骤.*Welcome 页内状态'
task_require "$TASK_ORDER" 'Welcome 欢迎页、独立 HTML 交付页和原生启动页均不得显示该协议文案'
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
task_require "$TASK_VISUAL" '^### 6\.14 主题化复杂动画与动态场景（硬门槛）'
task_require "$TASK_VISUAL" '纯色几何形状沿直线平移'
task_require "$TASK_VISUAL" '每个 App 自有 Flutter 页面.*至少两个'
for task_motion_tool in Rive Flame flutter_animate Lottie animator simple_animations FragmentProgram confetti particle_field particles_flutter shimmer liquid_swipe page_transition glassmorphism motion_tab_bar animated_text_kit flame_forge2d three_dart fl_chart CustomPainter PathMetric BlendMode BackdropFilter Ticker AnimationController Curves Matrix4; do
  task_require "$TASK_VISUAL" "$task_motion_tool"
done
task_require "$TASK_VISUAL" '动画前、进行中、结束/完成'
task_require "$TASK_QA" '复杂动态场景逐页验收'
task_require "$TASK_SKILL" 'Never construct animation or dynamic effects from solid color blocks'
task_require "$TASK_SKILL" 'Verify each exact package'
task_require "$TASK_README" 'onTapUp'
task_require "$TASK_README" '至少三种有意且可复用的字体风格'
task_require "$TASK_README" 'assets/logo\.png.*common_module/theme/app_theme\.dart'
task_require "$TASK_README" '冷色主导.*重新生成或重选 Logo'
task_require "$TASK_VISUAL" '每个 App 自有页面.*主题相关.*背景装饰图案'
task_require "$TASK_VISUAL" '使用 `http://stargate.local:3100/image` 生成.*背景装饰图案'
task_require "$TASK_VISUAL" '按页面 ID.*装饰素材.*实际引用'
task_require "$TASK_VISUAL" 'assets/backgrounds/<page_id>/<page_id>_background\.png'
task_require "$TASK_VISUAL" '背景点缀不得只写在规范里'
task_require "$TASK_VISUAL" '禁止单一背景体系'
task_require "$TASK_VISUAL" '至少两个 Logo 派生渐变令牌'
task_require "$TASK_ARCHITECTURE" 'main\.dart.*仅负责.*启动'
task_require "$TASK_ARCHITECTURE" '每个实际 App 自有页面.*独立的 `lib/page_module'
task_require "$TASK_ARCHITECTURE" '页面清单.*对应实现文件'
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
  task_require "$TASK_INSTALLED_SKILL" 'The Welcome page and standalone HTML contain no protocol agreement copy'
  task_require "$TASK_INSTALLED_SKILL" 'Only after the user confirms `Clear Data` and clearing actually succeeds'
  task_require "$TASK_INSTALLED_SKILL" 'minimum action coverage is not a cap'
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

# Runtime Dart and retained HTML have distinct acceptance contracts.
for task_file in "$TASK_PUBLISH" "$TASK_PRODUCT" "$TASK_ORDER" "$TASK_ENTRY" "$TASK_SKILL" "$TASK_README"; do
  task_require "$task_file" 'lib/welcome\.dart'
  task_require "$task_file" 'aduit/welcome\.html'
done
task_require "$TASK_PUBLISH" 'App 实际使用.*lib/welcome\.dart'
task_require "$TASK_PUBLISH" '保留.*aduit/welcome\.html.*但不使用'
task_require "$TASK_PUBLISH" 'PageView.*PageController'
task_require "$TASK_PUBLISH" 'Continue.*直接调用.*Dart callback'
task_require "$TASK_PUBLISH" '防重复点击/重复导航'
task_require "$TASK_PUBLISH" '图片/背景/GIF 使用已登记.*assets/'
task_require "$TASK_PUBLISH" 'SafeArea.*MediaQuery'
task_require "$TASK_PUBLISH" '通过 Dart import/路由编译，不登记为 Flutter asset'
task_require "$TASK_PUBLISH" '保留协议页面仍实际需要的 WebView 依赖'
task_require "$TASK_PUBLISH" '删除根目录旧.*welcome\.html.*enter\.html'
task_require "$TASK_PUBLISH" '不能等待独立 HTML、DOM 或网页消息'
task_require "$TASK_PUBLISH" '250 毫秒再淡出'
task_require "$TASK_VISUAL" '欢迎页不可滚动（硬门槛）'
task_require "$TASK_VISUAL" '禁止整页或内部纵向滚动'
task_require "$TASK_VISUAL" '仅允许介绍卡片横向滑动'
task_require "$TASK_VISUAL" '纵向滚动范围为零、按钮始终完整可见'
task_require "$TASK_VISUAL" '不能仅设置 overflow:hidden 隐藏溢出'
task_require "$TASK_QA" '无纵向滚动范围、内容与 Continue 完整可见'
task_require "$TASK_SKILL" 'Neither welcome surface may scroll vertically'
task_require "$TASK_SKILL" 'Continue calls the existing Dart entry callback directly'
task_require "$TASK_SKILL" 'standalone delivery file only: never load it in the App'
task_require "$TASK_SKILL" 'Preserve the WebView dependency and security rules still used for protocol viewing'
task_require "$TASK_SKILL" 'no HTML/aduit runtime reference or packaged copy'
task_require "$TASK_PUBLISH" '所有图片 Base64 data URI 内嵌'
task_require "$TASK_PUBLISH" '严格小于 262,144 字节'
task_require "$TASK_PUBLISH" 'viewport-fit=cover'
task_require "$TASK_PUBLISH" 'safe-area-inset-top'
task_require "$TASK_PUBLISH" 'safe-area-inset-bottom'
task_require "$TASK_PUBLISH" 'function continueToApp'
task_require "$TASK_PUBLISH" 'App 不为它注册消息桥'
task_require "$TASK_PUBLISH" 'prefers-reduced-motion'
for task_size in '390×667' '390×844' '1024×768' '1440×900'; do
  task_require "$TASK_PUBLISH" "$task_size"
  task_require "$TASK_SKILL" "$task_size"
done
task_require "$TASK_PUBLISH" '直接子项恰好为.*intro\.md.*welcome\.html.*imgs/.*site/.*review/'
task_require "$TASK_PUBLISH" '完整英文产品介绍'
task_require "$TASK_PUBLISH" '每个主要模块至少写清'
task_require "$TASK_PUBLISH" '至少 8 个不同用户结果的端到端任务'
task_require "$TASK_PUBLISH" 'URL 完整保护'
task_require "$TASK_PUBLISH" '最多 4,000 字符'
task_require "$TASK_PUBLISH" '协议通用文案仅初始化页显示'
task_require "$TASK_PUBLISH" '引导页检查必须先执行并记录结果，再进入 URL 回接和 Review Remarks'
task_ordered "$TASK_ORDER" '17\. 按第 12\.1 节先核对' '18\. \*\*验收首页引导页'
task_ordered "$TASK_ORDER" '18\. \*\*验收首页引导页' '19\. \*\*最终图片加载检查'
task_ordered "$TASK_ORDER" '首页引导页完成验收尝试并记录结果后' '生成不超过 4,000 字符的全英文'
task_require "$TASK_MATERIALS" '最终依赖目录与 App bundle 中不得残留.*aduit'
task_require "$TASK_MATERIALS" '不访问或探测真实 URL'
task_require "$TASK_SKILL" 'Do not visit or probe real URLs'
task_require "$TASK_SKILL" 'bind each to its corresponding raw URL'
task_ordered "$TASK_SKILL" '5\. Immediately after that rename' '6\. After the guide checks are completed or their blockers recorded'
task_ordered "$TASK_SKILL" '6\. After the guide checks are completed or their blockers recorded' '7\. After every implementation'
task_require "$TASK_SKILL" 'Generate 12 independent Logo candidates from.*three each.*reality-inspired realism.*hand-drawn.*oil painting.*artistic expression'
task_require "$TASK_SKILL" 'c01/.*c12/'
task_require "$TASK_SKILL" '12-image comparison must cover all four groups'
task_require "$TASK_SKILL" 'Avoid a conspicuous AI-generated look'
task_require "$TASK_SKILL" 'forbid 3D'
task_require "$TASK_IDEA" '12 张候选覆盖四种已约定画风'
task_require "$TASK_IDEA" '四组各 3 张'
task_require "$TASK_IDEA" '比较全部 12 张'
task_require "$TASK_IDEA" 'c04.*手绘.*笔触.*层次.*简笔'
task_require "$TASK_MATERIALS" '主题元素.*模拟现实.*手绘.*油画.*艺术.*四种画风'
task_require "$TASK_ROOT/工作流文档/02-创意与思维导图.md" '避免明显 AI 生成感'
task_require "$TASK_ROOT/工作流文档/02-创意与思维导图.md" '禁止 3D'
task_require "$TASK_IDEA" '至少三个实际 Flutter 页面/组件消费 Logo 派生色'
task_require "$TASK_IDEA" '全项目主要页面.*Logo 主题色派生.*渐变.*至少两个真实可达.*主题粒子效果'
task_require "$TASK_VISUAL" 'Logo 原始 HEX → Flutter 主题令牌 → 实际页面/组件 → iPhone 截图'
task_require "$TASK_VISUAL" '全项目多使用与 Logo 派生主题色对应的协调多色渐变'
task_require "$TASK_VISUAL" '至少选择两个真实可达.*最低覆盖数量不是上限'
task_require "$TASK_VISUAL" '按第 1\.4 节选定的 iPhone 档位'
task_require "$TASK_MATERIALS" '主页面、真实操作页和至少一个其他 App 页面'
task_require "$TASK_QA" '至少三个实际页面/组件的 iPhone 截图'
task_require "$TASK_ORDER" '截图证明主题令牌已被实际页面/组件消费'
task_require "$TASK_EXECUTION" '所有 UI 视觉表现均属于硬门槛'
task_require "$TASK_QA" '该硬门槛覆盖全部 UI 视觉效果'
task_require "$TASK_SKILL" 'All UI visual behavior is part of this hard gate'
task_require "$TASK_SKILL" 'at least three real App screens'
task_require "$TASK_SKILL" 'varied, coordinated gradients derived from the approved Logo palette'
task_require "$TASK_SKILL" 'AnimationController` and `CustomPainter`'
task_require "$TASK_SKILL" 'at the `onTapUp` coordinates'
task_require "$TASK_SKILL" 'at least two real, reachable, semantically different tap actions'
task_require "$TASK_SKILL" 'Use the selected iPhone tier.*mid-range by default; extreme-high-end'
task_require "$TASK_SKILL" 'minimum action coverage is not a cap'
task_require "$TASK_README" '至少三个实际 App 页面/组件'
task_require "$TASK_README" '所有 UI 视觉表现都是发布硬门槛'

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

print -r -- 'PASS: onboarding-guide content, exact placement, accessibility, acceptance order, Dart navigation, delivery-only HTML, non-scrolling layout, and target viewports are specified across the workflow.'
