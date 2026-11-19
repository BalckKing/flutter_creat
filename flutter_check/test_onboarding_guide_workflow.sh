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

task_require "$TASK_IDEA" '统一采用明亮色调'
task_require "$TASK_IDEA" '渐变实际消费是硬门槛，数量不设配额'
task_require "$TASK_IDEA" '不得采用简约线条.*色块'
task_require "$TASK_VISUAL" '统一采用明亮色调'
task_require "$TASK_VISUAL" '^### 6\.2 统一明亮外观与移除颜色调节'
task_require "$TASK_VISUAL" 'Settings 不提供调色盘、主题色选择、色相/饱和度/亮度滑杆或.*System.*Light.*Dark.*外观切换'
task_require "$TASK_VISUAL" 'ThemeMode\.light'
task_require "$TASK_VISUAL" 'UIUserInterfaceStyle.*Light'
task_require "$TASK_VISUAL" 'color-scheme: light'
task_require "$TASK_ARCHITECTURE" '不保存颜色、明暗模式或外观切换偏好'
task_require "$TASK_PUBLISH" '不宣传调色或明暗切换能力'
task_require "$TASK_QA" '系统外观变化.*保持明亮'
task_require "$TASK_SKILL" 'Remove color-adjustment controls and appearance switching'
task_require "$TASK_VISUAL" '这是每次启动 App 后唯一进入的 Flutter 入口文件.*lib/welcome\.dart'
task_require "$TASK_VISUAL" '只有采用 Clear Data 的项目在用户确认并真实清除成功后，才显示初始化页并提供 `Enter`'
task_require "$TASK_VISUAL" '采用 `Exit App` 的项目不得创建、注册或打开 Initialization'
task_require "$TASK_VISUAL" 'Exit App 成功不显示 Initialization'
task_require "$TASK_VISUAL" 'Settings 同时使用项目专属品牌头部、分组图标、摘要状态、真实选项值'
task_require "$TASK_VISUAL" '启动准备状态位于 Welcome 内部'
task_require "$TASK_VISUAL" 'Welcome 和独立引导页不显示协议文案'
task_require "$TASK_VISUAL" '协议通用文案只显示在 Initialization 底部'
task_require "$TASK_VISUAL" 'Welcome 和独立引导页不显示协议文案'
task_require "$TASK_IDEA" 'Initialization 页底部显示两行通用协议文案并链接 Terms/Privacy；Welcome 欢迎页不显示该文案'
task_forbid "$TASK_IDEA" '引导页提供 Terms/Privacy 文本链接'
task_require "$TASK_VISUAL" '初始化页.*底部.*`By continuing, you agree to our`'
task_require "$TASK_VISUAL" '初始化页.*底部.*`Terms of Use and Privacy Policy`'
task_require "$TASK_VISUAL" '全项目必须使用贴题渐变色彩'
task_require "$TASK_VISUAL" '渐变方向、色标、动态方式和 Logo 是否参与由主题决定，不设色系或数量配额'
task_require "$TASK_VISUAL" 'AnimationController.*CustomPainter'
task_require "$TASK_VISUAL" 'onTapUp'
task_require "$TASK_VISUAL" '位置、速度、重力、颜色和拖尾'
task_require "$TASK_VISUAL" '减少动态.*粒子'
task_require "$TASK_VISUAL" '所有由 AI 生成.*不得使用简约线条.*色块'
task_require "$TASK_VISUAL" '标题的斜体与色彩.*渐变文字必须消费主题渐变令牌'
task_require "$TASK_VISUAL" '至少三种有依据的字体风格'
task_require "$TASK_VISUAL" 'Logo 取色仅作可选品牌参考.*明亮'
task_require "$TASK_VISUAL" 'common_module.*app_theme\.dart.*全局'
task_require "$TASK_VISUAL" '明亮色调.*不设.*配额'
task_require "$TASK_VISUAL" '渐变令牌必须.*实际消费'
task_require "$TASK_MATERIALS" '统一采用明亮色调'
task_require "$TASK_MATERIALS" '所有由 AI 生成并进入项目的图像.*简约线条/细轮廓.*色块堆叠'
task_require "$TASK_QA" '统一采用明亮色调'
task_require "$TASK_QA" '^### 11\.1 真实 App 运行时调试与验收'
task_require "$TASK_QA" '资料包里的测试文件只验证工作流文档、脚本契约、安装器和检查器行为'
task_require "$TASK_QA" '每次操作后观察页面是否改变、按钮是否响应'
task_require "$TASK_EXECUTION" '^### 0\.9\.1 调试安装与构建产物复用'
task_require "$TASK_EXECUTION" '禁止用 App 测试文件替代运行时验收'
task_require "$TASK_EXECUTION" '运行时调试闭环'
task_require "$TASK_SKILL" '^## Real App runtime debugging contract'
task_require "$TASK_SKILL" 'test/` and `flutter_check/` files may validate this workflow bundle'
task_require "$TASK_IDEA" 'Simulator Build/Run \+ UI Interaction \+ Logs'
for runtime_file in "$TASK_README" "$TASK_EXECUTION" "$TASK_QA" "$TASK_ORDER" "$TASK_SKILL"; do
  task_forbid "$runtime_file" 'Widget \+ Integration Tests|widget/navigation checks|普通测试.*App 已通过|test App.*App 功能'
done
task_require "$TASK_QA" '不以.*亮度阈值.*代替.*检查'
task_require "$TASK_QA" '初始化页视觉专项.*至少一个实际消费的渐变令牌'
task_require "$TASK_QA" '非游戏项目每次新进程启动都只进入 Welcome 并显示 `Continue`'
task_require "$TASK_QA" '仅实际存在并采用 Clear Data 的项目在二次确认且清除成功后进入 Initialization 并显示 `Enter`'
task_require "$TASK_QA" 'Exit App 成功不得进入 Initialization'
task_require "$TASK_QA" '未采用 Clear Data.*Initialization.*Not applicable'
task_require "$TASK_QA" '通用协议文案仅初始化页显示.*运行时欢迎/游戏表面.*不得显示'
task_require "$TASK_QA" '检查 AI 生成图不得使用简约线条.*色块'
task_require "$TASK_ORDER" '非游戏项目每次启动只进入且含 `Continue` 的 Flutter Welcome；游戏/混合项目每次启动.*沉浸式游戏大厅.*Play.*Load.*Operation'
task_require "$TASK_ORDER" '准备步骤.*Welcome 页内状态'
task_require "$TASK_ORDER" 'Welcome 欢迎页、独立 HTML 交付页和原生启动页均不得显示该协议文案'
task_require "$TASK_ORDER" '至少三种有意且可复用的字体风格'
task_require "$TASK_ORDER" 'assets/logo\.png.*common_module/theme/app_theme\.dart'
task_forbid "$TASK_ORDER" 'Flutter Loading 和初始化欢迎页|Loading 后显示 Enter|初始化欢迎页|成功返回欢迎页|清除并回欢迎页|引导页提供 Terms/Privacy 文本链接'
for task_startup_doc in "$TASK_IDEA" "$TASK_VISUAL" "$TASK_ARCHITECTURE" "$TASK_QA" "$TASK_ORDER" "$TASK_SKILL" "$TASK_README"; do
  task_forbid "$task_startup_doc" 'Clear Data / Exit App.*实际成功后进入初始化|selected `Clear Data` or `Exit App` action and it actually succeeds, show the separate Initialization|所选 Clear Data / Exit App.*成功.*初始化页'
done
task_require "$TASK_SKILL" 'Use a bright visual tone throughout'
task_require "$TASK_SKILL" 'Every visual surface must consume at least one theme-appropriate gradient token'
task_require "$TASK_SKILL" 'Avoid minimalist line art, thin-outline-only artwork, flat geometric shapes, and color-block-only compositions'
task_require "$TASK_SKILL" 'For non-game projects, the native launch surface and Flutter Welcome are the only normal startup surfaces'
task_require "$TASK_SKILL" 'Every non-game app launch enters only the Welcome page with `Continue`'
task_require "$TASK_SKILL" 'Only a real, selected `Clear Data` capability may show the separate Initialization page'
task_require "$TASK_SKILL" '`Exit App` never routes to or creates Initialization'
task_require "$TASK_SKILL" 'If Clear Data is not appropriate, omit the Initialization route and page entirely'
task_require "$TASK_SKILL" 'Only the Initialization page shows the bottom protocol agreement copy'
task_require "$TASK_SKILL" 'The Welcome page has no protocol agreement footer'
task_require "$TASK_SKILL" 'The onboarding guide contains no protocol agreement copy'
task_require "$TASK_SKILL" 'Protocol agreement text belongs only at the bottom of the separate Initialization page'
task_require "$TASK_SKILL" 'Settings needs a branded header, icon-led groups, summary states, real option values and meaningful visual modules'
task_require "$TASK_SKILL" 'at least three intentional, reusable font treatments'
task_require "$TASK_SKILL" 'Centralize actual bright theme values in `common_module/theme/app_theme.dart`'
task_require "$TASK_README" '统一采用明亮色调'
task_require "$TASK_README" 'iOS 原生冷启动页之后，非游戏项目每次启动只进入含 `Continue` 的 Flutter Welcome 页；游戏/混合项目每次启动进入.*沉浸式游戏大厅.*Play.*Load.*Operation'
task_require "$TASK_README" '欢迎页.*不显示.*协议文本.*初始化页.*底部'
task_require "$TASK_README" 'Settings 页面必须重新设计为主题化品牌头部、分组图标、状态摘要、真实选项值'
task_require "$TASK_README" '任何 AI 生成图都不得采用简约线条.*纯色块堆叠'
task_forbid "$TASK_ORDER" '游戏.*at most one visible Play/Start action'
task_forbid "$TASK_ORDER" 'selected game must use one declared real engine'
task_require "$TASK_ORDER" '游戏大厅.*`Play`.*`Load`.*`Operation`'
task_require "$TASK_ORDER" '引擎必要性决策'
task_require "$TASK_ORDER" '明确 `implementation_mode`、`engine_required` 和 `decision_reason`'
task_require "$TASK_ORDER" '`engine` 或 `flutter_native` 路线'
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
task_require "$TASK_README" 'common_module/theme/app_theme\.dart.*AppPalette/AppTheme'
task_require "$TASK_README" 'Logo 取色仅作可选品牌参考.*明亮'
for task_color_file in "$TASK_ENTRY" "$TASK_IDEA" "$TASK_VISUAL" "$TASK_ARCHITECTURE" "$TASK_MATERIALS" "$TASK_QA" "$TASK_PUBLISH" "$TASK_ORDER" "$TASK_EXECUTION" "$TASK_README" "$TASK_SKILL"; do
  task_forbid "$task_color_file" '任意配色均可通过|任意色彩均可使用|任意色彩都可以使用|配色不受限制|色彩不受限制|自由配色|unrestricted color|Any color palette is allowed|Preserve appearance switching|Settings 必须提供 `System`|默认主题为 `System`|clear 成功后恢复 `System`|System、Light、Dark 正常持久化|恢复默认 System|已保存主题与偏好读取'
  task_forbid "$task_color_file" '再提取其真实色块制定主题色与渐变|完成配色提取前不推进|sole brand/palette source|multiple coordinated Logo-derived gradients|varied Logo-derived gradients/materials|Verify About palette against assets/logo'
  task_forbid "$task_color_file" '至少三种清晰可辨的鲜明色彩|at least three distinct vivid color families|至少 4 个.*主色家族|at least four dominant hue families|最多 3 张|at most three candidates|建立配色矩阵|write a color-diversity matrix|整体阴冷、灰暗或近乎单色.*重新生成|gloomy, austere or nearly monochromatic.*regenerate|不过度鲜艳|not excessively saturated|不得为纯白背景|禁止纯白整页背景|Never use pure-white page canvases|至少两个 Logo 派生渐变令牌|至少两个不同的 `gradient_tokens`|at least two distinct Logo-derived gradient_tokens|至少三个 Logo 派生 `palette_hex`|at least three real `palette_hex` values|至少四种用途明确的 Logo 派生渐变|at least four purpose-specific gradient tokens|四主色家族/最多三张橙黄'
done
task_require "$TASK_VISUAL" '每个 App 自有页面.*主题相关.*背景装饰图案'
task_require "$TASK_VISUAL" '使用 `http://stargate.local:3100/` 生成.*背景装饰图案'
task_require "$TASK_VISUAL" '按页面 ID.*背景模式.*真实消费者'
task_require "$TASK_VISUAL" 'assets/backgrounds/<page_id>/<page_id>_background\.png'
task_require "$TASK_VISUAL" '背景点缀不得只写在规范里'
task_require "$TASK_VISUAL" '各独立页面的场景构图、主体、轨迹或状态响应必须可辨认地不同'
task_require "$TASK_ARCHITECTURE" 'main\.dart.*仅负责.*启动'
task_require "$TASK_ARCHITECTURE" '每个实际 App 自有页面.*独立的 `lib/page_module'
task_require "$TASK_ARCHITECTURE" '页面清单.*对应实现文件'
task_require "$TASK_ARCHITECTURE" '不得将多个路由页面集中写在'
task_require "$TASK_ARCHITECTURE" 'assets/backgrounds/<page_id>/<page_id>_background\.png'
task_require "$TASK_ARCHITECTURE" 'common_module/theme/app_theme\.dart'
task_require "$TASK_ARCHITECTURE" 'app_theme\.dart.*全局主题入口.*Logo 取色仅作可选参考'
task_require "$TASK_MATERIALS" '页面背景装饰.*Stargate'
task_require "$TASK_SOURCES" 'Stargate 图像生成入口：http://stargate.local:3100/.*页面.*背景装饰图案'
task_require "$TASK_QA" '逐页面.*背景装饰.*image/hybrid.*procedural/animation'
task_require "$TASK_QA" '文件夹和命名.*page_id'
task_require "$TASK_ORDER" 'Stargate.*逐页主题背景装饰'
task_require "$TASK_SKILL" 'For each App-owned page.*background decoration, choose image, procedural, animation or hybrid'
task_require "$TASK_SKILL" 'retain a real translucent theme-image accent in every mode'
task_require "$TASK_SKILL" 'Image-generation websites, tools and models do not need to be uniform'
task_require "$TASK_SKILL" 'Project-owned folder and file names must not contain Codex or AI-related terms'
task_require "$TASK_SKILL" 'full-bleed bright gradient or hybrid background'
task_require "$TASK_SKILL" 'five required visual roles'
task_require "$TASK_SKILL" 'pure white or near-white background with a small centered image'
task_require "$TASK_MATERIALS" 'validate_launch_screen_visual.py'
task_require "$TASK_MATERIALS" '至少两种明亮背景令牌'
task_require "$TASK_QA" '不得出现纯白/近白底、居中小方图、大面积空白或单图一屏'
task_require "$TASK_QA" '全屏明亮渐变/混合背景、主题图片叠层、品牌层、项目名/定位文案和装饰层'
task_forbid "$TASK_SKILL" 'white background is acceptable as the only launch background'
task_require "$TASK_SKILL" 'Use `\.codex-work/` for all project development records'
if [[ -f "$TASK_INSTALLED_SKILL" ]]; then
  task_require "$TASK_INSTALLED_SKILL" 'Collect four required inputs together'
  task_require "$TASK_INSTALLED_SKILL" 'Git repository URL'
  task_require "$TASK_INSTALLED_SKILL" 'prepare_git_handoff\.py'
  task_require "$TASK_INSTALLED_SKILL" '^10\. After all acceptance gates'
  task_require "$TASK_INSTALLED_SKILL" 'feat/1\.0\.0'
  task_require "${TASK_INSTALLED_SKILL:h}/references/工作流文档/09-实施顺序与交付报告.md" '^22\. \*\*关联 Git 仓库与创建分支'
  task_require "$TASK_INSTALLED_SKILL" 'Use a bright visual tone throughout'
  task_require "$TASK_INSTALLED_SKILL" 'Every visual surface must consume at least one theme-appropriate gradient token'
  task_require "${TASK_INSTALLED_SKILL:h}/references/工作流文档/02-创意与思维导图.md" '统一采用明亮色调'
  task_forbid "$TASK_INSTALLED_SKILL" 'overall warm gradients|cold-dominant.*regenerate'
  task_require "$TASK_INSTALLED_SKILL" 'For each App-owned page.*background decoration, choose image, procedural, animation or hybrid'
  task_require "$TASK_INSTALLED_SKILL" 'Stargate is an optional image-generation source for Logo and page-specific UI background decoration'
  task_require "$TASK_INSTALLED_SKILL" 'Every mode requires background.asset, background.opacity'
  task_require "$TASK_INSTALLED_SKILL" 'Image-generation websites, tools and models do not need to be uniform'
  task_require "$TASK_INSTALLED_SKILL" 'Project-owned folder and file names must not contain Codex or AI-related terms'
  task_require "$TASK_INSTALLED_SKILL" 'Use `\.codex-work/` for all project development records'
  task_require "$TASK_INSTALLED_SKILL" 'Protocol agreement text belongs only at the bottom of the separate Initialization page'
  task_require "$TASK_INSTALLED_SKILL" 'The Welcome page and standalone HTML contain no protocol agreement copy'
  task_require "$TASK_INSTALLED_SKILL" 'Every non-game app launch enters only the Welcome page with `Continue`'
  task_require "$TASK_INSTALLED_SKILL" 'Only a real, selected `Clear Data` capability may show the separate Initialization page'
  task_require "$TASK_INSTALLED_SKILL" '`Exit App` never routes to or creates Initialization'
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
task_require "$TASK_PUBLISH" 'App 运行时只使用 `lib/welcome.dart`，不加载 `aduit/welcome.html`'
task_require "$TASK_PUBLISH" '保留 `aduit/welcome.html` 作为独立交付文件，不删除'
task_require "$TASK_SKILL" 'The App has exactly one runtime Welcome surface: `lib/welcome.dart`'
task_require "$TASK_SKILL" 'Keep `aduit/welcome.html` as a delivery-only file; never load, register, copy, bridge, or bundle it'
task_require "$TASK_PUBLISH" '保留.*aduit/welcome\.html.*但不使用'
task_require "$TASK_PUBLISH" 'PageView.*PageController'
task_require "$TASK_PUBLISH" 'Continue.*直接调用.*Dart callback'
task_require "$TASK_PUBLISH" '防重复点击/重复导航'
task_require "$TASK_PUBLISH" '图片/背景/GIF 使用已登记.*assets/'
task_require "$TASK_PUBLISH" 'SafeArea.*MediaQuery'
task_require "$TASK_PUBLISH" '通过 Dart import/路由编译，不登记为 Flutter asset'
task_require "$TASK_PUBLISH" '保留协议页面仍实际需要的 WebView 依赖'
task_require "$TASK_PUBLISH" 'aduit 生成完成后.*App 内.*WebView.*协议页面'
task_require "$TASK_PUBLISH" '不跳转到外部 App'
task_require "$TASK_PUBLISH" 'http://【项目名称】/PrivacyPolicy\.html'
task_require "$TASK_PUBLISH" 'http://【项目名称】/Terms&Conditions\.html'
task_require "$TASK_PUBLISH" 'http://【项目名称】/Support\.html'
task_require "$TASK_PUBLISH" '三个文件名.*不得改动'
task_require "$TASK_ARCHITECTURE" '三个协议 URL.*具体项目名称.*固定注册表'
task_require "$TASK_QA" '三个协议链接.*HTTP 模板.*WebView'
task_require "$TASK_ORDER" 'aduit.*完成.*协议页面.*App 内 WebView'
task_require "$TASK_SKILL" 'After `aduit` is generated.*in-app WebView'
task_require "$TASK_SKILL" 'Do not open an external App'
task_require "$TASK_SKILL" 'http://【项目名称】/PrivacyPolicy\.html'
task_require "$TASK_SKILL" 'http://【项目名称】/Terms&Conditions\.html'
task_require "$TASK_SKILL" 'http://【项目名称】/Support\.html'
task_require "$TASK_SKILL" 'Keep these three filenames unchanged'
task_require "$TASK_SKILL" 'user-provided project name at generation time'
task_require "$TASK_SKILL" 'reject them if they remain in the final App configuration'
task_require "$TASK_SKILL" 'failed request.*concrete URL.*WebView'
task_forbid "$TASK_SKILL" 'project-name placeholder is the only later replacement token'
task_forbid "$TASK_SKILL" 'unreplaced host is retained for later search/replace'
task_require "$TASK_README" '协议链接.*http://【项目名称】/xxx\.html'
task_require "$TASK_README" '不跳转外部 App'
task_forbid "$TASK_PUBLISH" '四个原始 URL.*原样接入|index\.html'
task_forbid "$TASK_PUBLISH" '四个原始值.*直接复制|index\.html'
task_forbid "$TASK_PUBLISH" '目标是否可达.*直接复制'
task_forbid "$TASK_ARCHITECTURE" '不得另行修补地址'
task_forbid "$TASK_README" '四个 `All URL` 原封不动接入|index\.html'
task_require "$TASK_PUBLISH" '删除根目录旧.*welcome\.html.*enter\.html'
task_require "$TASK_PUBLISH" '不能等待独立 HTML、DOM 或网页消息'
task_require "$TASK_PUBLISH" '250 毫秒再淡出'
task_require "$TASK_VISUAL" 'Welcome 不提供暂停按钮、暂停/恢复控件或 paused 状态'
task_require "$TASK_PUBLISH" 'Welcome Dart 与独立 HTML 不提供暂停按钮、暂停/恢复控件或 paused 状态'
task_require "$TASK_QA" 'Welcome 专项不得验收暂停/恢复控件'
task_require "$TASK_QA" 'Welcome 运行时只验收 `lib/welcome.dart`，HTML 只作独立交付验收'
task_forbid "$TASK_QA" '同时按第 7\.1 节验证两份欢迎页'
task_forbid "$TASK_PUBLISH" 'Dart 页与独立 HTML 分别在'
task_forbid "$TASK_PUBLISH" '两份欢迎产物共同按'
task_require "$TASK_SKILL" 'Welcome surfaces do not expose a pause button, pause/resume control, or paused state'
task_require "$TASK_SKILL" 'Media, game, and lifecycle pause/resume rules remain applicable outside Welcome'
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
task_require "$TASK_PUBLISH" '至少 12 个不同用户结果的端到端任务'
task_require "$TASK_PUBLISH" 'URL 完整保护'
task_require "$TASK_PUBLISH" '最多 4,000 字符'
task_require "$TASK_PUBLISH" '协议通用文案仅初始化页显示'
task_require "$TASK_PUBLISH" '引导页检查必须先执行并记录结果，再进入 URL 回接和 Review Remarks'
task_ordered "$TASK_ORDER" '17\. 按第 12\.1 节先核对' '18\. \*\*生成 Review Remarks'
task_ordered "$TASK_ORDER" '18\. \*\*生成 Review Remarks' '19\. \*\*最终图片加载检查'
task_ordered "$TASK_ORDER" '欢迎页完成验收尝试并记录结果后' '生成不超过 4,000 字符的全英文'
task_require "$TASK_MATERIALS" '最终依赖目录与 App bundle 中不得残留.*aduit'
task_require "$TASK_MATERIALS" '不访问或探测真实 URL'
task_require "$TASK_SKILL" 'Do not visit or probe real URLs'
task_require "$TASK_SKILL" 'bind each to its corresponding raw URL'
task_ordered "$TASK_SKILL" '5\. Immediately after that rename' '6\. After the guide checks are completed or their blockers recorded'
task_ordered "$TASK_SKILL" '6\. After the guide checks are completed or their blockers recorded' '7\. After implementation'
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
task_require "$TASK_IDEA" '记录可选的 Logo 色彩参考'
task_require "$TASK_IDEA" '主题级概括'
task_require "$TASK_IDEA" '不把创意中的每个细节'
task_require "$TASK_MATERIALS" '主题级概括'
task_require "$TASK_SKILL" 'theme-level summary'
task_require "$TASK_SKILL" 'Do not copy every creative detail into the Logo prompt'
task_require "$TASK_README" '主题级概括'
task_require "$TASK_IDEA" '全项目主要页面统一采用明亮色调.*不设数量或覆盖门槛.*至少两个真实可达.*主题粒子效果'
task_require "$TASK_VISUAL" '主题令牌 → 页面共享样式 → 当前构建截图'
task_require "$TASK_VISUAL" '色板可以跨页复用'
task_require "$TASK_VISUAL" '至少选择两个真实可达.*最低覆盖数量不是上限'
task_require "$TASK_VISUAL" '按第 1\.4 节选定的 iPhone 档位'
task_require "$TASK_MATERIALS" '没有 Logo 取色仍可继续，但每个视觉表面必须有实际消费的渐变令牌'
task_require "$TASK_QA" '至少三个实际页面 Dart 文件消费共享主题文字角色'
task_require "$TASK_ORDER" '截图证明主题令牌已被实际页面/组件消费'
task_require "$TASK_EXECUTION" '所有适用 UI 视觉表现均属于硬门槛'
task_require "$TASK_QA" '该硬门槛覆盖全部 UI 视觉效果'
task_require "$TASK_SKILL" 'All UI visual behavior is part of this hard gate'
task_require "$TASK_SKILL" 'shared typography consumption by at least three page files'
task_require "$TASK_SKILL" 'GetX is forbidden'
task_require "$TASK_SKILL" 'native `MaterialApp`'
# Game is an explicit optional project type. Non-game projects must not inherit game-only work.
task_require "$TASK_ENTRY" '游戏是可选主题分支，不是所有项目的默认类型'
task_require "$TASK_ENTRY" '非游戏项目不创建游戏引擎、游戏场景、游戏入口或游戏验收任务'
task_require "$TASK_IDEA" '项目类型必须明确记录为非游戏、游戏或混合'
task_require "$TASK_IDEA" '未选择游戏主题时按非游戏路线执行'
task_require "$TASK_PRODUCT" '游戏路线只在用户选择游戏主题或创意明确包含真实游戏模块时启用'
task_require "$TASK_PRODUCT" '非游戏主题不得为了满足游戏门槛添加游戏玩法或游戏引擎'
task_require "$TASK_PRODUCT" '主题工作台'
task_require "$TASK_PRODUCT" '至少 12 个.*独立.*功能页面'
task_require "$TASK_PRODUCT" '至少 8 个.*核心模块'
task_require "$TASK_PRODUCT" '不少于 120 个.*有效内容'
task_require "$TASK_ARCHITECTURE" '非游戏项目跳过第 9.6 节游戏决策和可玩闭环门槛'
task_require "$TASK_QA" '非游戏项目的游戏专项验收标记为 Not applicable'
task_require "$TASK_QA" '能力矩阵'
task_require "$TASK_QA" 'Selected / Implemented / Runtime verified / Declined fallback / Not appropriate'
task_require "$TASK_ORDER" '先判定项目类型，再决定是否执行游戏引擎与游戏闭环任务'
task_require "$TASK_SKILL" 'Game is an optional project type, not a default requirement'
task_require "$TASK_SKILL" 'Non-game projects still do not create a game engine, game scene, game entry, or game-only acceptance task'
task_require "$TASK_SKILL" 'theme workbench'
task_require "$TASK_SKILL" 'capability matrix'
for task_legacy_permissions in "$TASK_IDEA" "$TASK_PRODUCT" "$TASK_QA" "$TASK_PUBLISH" "$TASK_SKILL" "$TASK_README"; do
  task_forbid "$task_legacy_permissions" '三项全无|全部不选|全部不包含|任意组合.*全部|可任意组合|可自由或随机组合|including none|remain optional'
done
task_require "$TASK_README" '游戏是可选主题，不是每个项目都必须制作游戏'
task_require "$TASK_README" '非游戏项目不接入游戏引擎或游戏专项验收'
task_require "$TASK_ROOT/start.sh" '游戏是可选主题：只有我选择游戏主题或创意明确包含真实游戏模块时'
task_require "$TASK_ROOT/start.sh" '非游戏项目不接入游戏引擎或游戏专项验收'

# Non-game capabilities still require real tools, consumers and current-iPhone
# evidence. Keep these assertions in the onboarding test so installation cannot
# silently ship an older or weaker quality contract.
task_require "$TASK_IDEA" '^### 3\.2\.2 非游戏能力决策与真实工具记录（硬门槛）'
task_require "$TASK_VISUAL" '^#### 6\.14\.5 非游戏高级实现与真实能力门槛（硬门槛）'
task_require "$TASK_ARCHITECTURE" '^#### 9\.3\.3 非游戏真实能力实现边界（硬门槛）'
task_require "$TASK_QA" '^#### 11\.6\.0\.1 非游戏高级能力与真实工具验收（硬门槛）'
for task_non_game_field in real_tool_or_sdk 'license/source' actual_consumer runtime_evidence formula_record; do
  task_require "$TASK_IDEA" "$task_non_game_field"
  task_require "$TASK_VISUAL" "$task_non_game_field"
  task_require "$TASK_ARCHITECTURE" "$task_non_game_field"
  task_require "$TASK_QA" "$task_non_game_field"
  task_require "$TASK_SKILL" "$task_non_game_field"
done
for task_map_term in '真实地图 SDK' '真实地图瓦片' MapKit Mapbox flutter_map '许可地理数据' '静态地图截图' '假坐标网格' '组件目录'; do
  task_require "$TASK_VISUAL" "$task_map_term"
  task_require "$TASK_ARCHITECTURE" "$task_map_term"
  task_require "$TASK_QA" "$task_map_term"
done
for task_map_term in 'real map SDK' 'real map tiles' MapKit Mapbox flutter_map 'licensed geographic data' 'static screenshots' 'fake coordinate grids' 'reference component catalog'; do
  task_require "$TASK_SKILL" "$task_map_term"
done
task_require "$TASK_ORDER" '非游戏项目并行执行.*真实能力与视觉工具决策'
task_require "$TASK_README" '非游戏项目同样必须使用真实能力完成精致成品'
task_require "$TASK_README" '非游戏没有游戏引擎，但视觉质量、真实消费者和运行证据门槛不降低'
for task_non_game_bypass in \
  '非游戏可以使用简易线条地图' \
  '静态地图截图即可' \
  '包安装即通过' \
  '只要依赖存在即可' \
  '非游戏无需真实工具' \
  '非游戏可使用占位地图'; do
  for task_non_game_doc in "$TASK_IDEA" "$TASK_VISUAL" "$TASK_ARCHITECTURE" "$TASK_QA" "$TASK_ORDER" "$TASK_SKILL" "$TASK_README"; do
    task_forbid "$task_non_game_doc" "$task_non_game_bypass"
  done
done
# Game projects must be genuinely playable, directly reachable, and independently verifiable.
task_require "$TASK_PRODUCT" '游戏主玩法必须从 `lib/welcome\.dart` 的沉浸式游戏大厅直接可达'
task_require "$TASK_PRODUCT" 'Play.*Loading.*Load.*Save Slot.*主游戏'
task_require "$TASK_PRODUCT" '不得把主游戏入口藏在 Settings、About、二级菜单、隐藏手势或不可见路由'
task_require "$TASK_ARCHITECTURE" '游戏可玩闭环硬门槛'
task_require "$TASK_ARCHITECTURE" '完整一局必须覆盖开始、真实输入、规则更新、成功或失败结果、重开'
task_require "$TASK_ARCHITECTURE" '禁止用空场景、彩色方块、静态截图或点击穿透演示充当可玩游戏'
task_require "$TASK_ARCHITECTURE" '独立游戏验收记录'
task_require "$TASK_QA" '游戏首屏可达性专项'
task_require "$TASK_QA" '游戏首屏可达性专项.*Play.*Loading.*Load.*Save Slot.*主游戏目的地'
task_require "$TASK_QA" '完整一局.*真实输入.*成功或失败.*重开'
task_require "$TASK_QA" '游戏核心路径任一失败.*Release readiness.*Blocked'
task_require "$TASK_ORDER" '游戏可玩闭环先于全量内容扩展'
task_require "$TASK_ORDER" '独立任务并行处理.*游戏核心路径'
task_require "$TASK_SKILL" 'Game projects must reach the primary game destination from the immersive lobby'
task_require "$TASK_SKILL" 'Play.*Loading.*Game.*Load.*Save Slot.*Game'
task_require "$TASK_SKILL" 'Never hide the primary game entry in Settings, About, secondary menus, hidden gestures, or invisible routes'
task_require "$TASK_SKILL" 'playable game loop gate'
task_require "$TASK_SKILL" 'real input, rules, success or failure result, and restart'
task_require "$TASK_SKILL" 'empty scene, colored-block demo, static screenshot, or click-through mock'
task_require "$TASK_SKILL" 'Independent workstreams may run in parallel'
task_require "$TASK_SKILL" 'blocked workstream does not stall unrelated work'
task_require "$TASK_SKILL" 'Game engine quality contract \(game and mixed projects only\)'
task_require "$TASK_SKILL" '\.codex-work/game-engine\.json'
task_require "$TASK_SKILL" 'engine\.name.*engine\.version.*engine\.entrypoint'
task_require "$TASK_SKILL" 'engine environment.*scene boot.*authored asset load.*input.*update/physics.*success or failure result.*feedback.*restart'
task_require "$TASK_SKILL" 'validate_game_project\.py'
task_require "$TASK_SKILL" '--project-root <target-project-root> --json'
task_require "$TASK_SKILL" 'setState\(\) called during build'
task_require "$TASK_SKILL" 'RenderFlex overflow'
task_require "$TASK_SKILL" 'duplicate engine registration'
task_require "$TASK_SKILL" 'input hit-test mismatch'
task_require "$TASK_SKILL" 'Release readiness: Blocked'
task_require "$TASK_SKILL" 'explicit engine-necessity decision'
task_require "$TASK_SKILL" 'flutter-native'
task_require "$TASK_SKILL" 'six-part motion prompt formula'
task_require "$TASK_SKILL" 'ui_component_contract'
task_require "$TASK_SKILL" 'no_simple_line_art'
task_require "$TASK_SKILL" 'no_flat_color_blocks'
task_require "$TASK_SKILL" 'no_solid_color_background'
task_require "$TASK_SKILL" 'any suitable engine, renderer, SDK, package or third-party runtime'
task_require "$TASK_SKILL" 'visual_mode.*2\.5d.*3d'
task_require "$TASK_SKILL" 'immersive game lobby'
task_require "$TASK_SKILL" 'Play.*Load.*Operation'
task_require "$TASK_SKILL" 'Play.*Loading.*Game'
task_require "$TASK_SKILL" 'Load.*Save Slot.*Game'
task_require "$TASK_SKILL" 'game_lobby'
task_require "$TASK_VISUAL" 'ui_component_contract'
task_require "$TASK_VISUAL" 'no_simple_line_art.*no_flat_color_blocks.*no_solid_color_background'
task_require "$TASK_ARCHITECTURE" 'ui_component_contract'
task_require "$TASK_QA" 'ui_component_contract'
task_require "$TASK_IDEA" '是否需要专用引擎'
task_require "$TASK_IDEA" 'implementation_mode'
task_require "$TASK_IDEA" '引擎环境.*场景启动.*素材加载.*真实输入.*更新/物理.*结果.*反馈.*重开'
task_require "$TASK_IDEA" 'Flutter 原生路线.*六部分效果提示词公式'
task_require "$TASK_VISUAL" '6\.14\.4 游戏实现决策门'
task_require "$TASK_VISUAL" 'validate_game_project\.py'
task_require "$TASK_VISUAL" '前中后景空间.*材质与光影.*相机/遮挡'
task_require "$TASK_ARCHITECTURE" '\.codex-work/game-engine\.json'
task_require "$TASK_ARCHITECTURE" '引擎环境.*垂直切片'
task_require "$TASK_QA" 'setState\(\) called during build'
task_require "$TASK_QA" 'RenderFlex overflow'
task_require "$TASK_QA" 'Release readiness: Blocked'
task_require "$TASK_ORDER" '先执行 `engine`/`flutter_native` 决策'
task_require "$TASK_ORDER" '引擎路线为.*引擎环境'
task_require "$TASK_ORDER" 'Flutter 原生路线为.*Flutter 运行时'
task_require "$TASK_ORDER" '垂直切片通过后才扩展全部玩法'
task_require "$TASK_README" '专用引擎'
for task_game_bypass in 'Flutter-only game fallback' 'engine dependency alone passes' 'static screenshot as gameplay' 'expand content before vertical slice'; do
  task_forbid "$TASK_SKILL" "$task_game_bypass"
done
if [[ -f "$TASK_INSTALLED_SKILL" ]]; then
  task_require "$TASK_INSTALLED_SKILL" 'Game engine quality contract \(game and mixed projects only\)'
  task_require "$TASK_INSTALLED_SKILL" 'validate_game_project\.py'
  task_require "$TASK_INSTALLED_SKILL" '--project-root <target-project-root> --json'
fi
task_require "$TASK_SKILL" 'The gradients gate is mandatory for every visual surface'
task_forbid "$TASK_SKILL" 'multiple coordinated Logo-derived gradients|varied Logo-derived gradients/materials'
task_require "$TASK_SKILL" 'AnimationController` and `CustomPainter`'
task_require "$TASK_SKILL" 'at the `onTapUp` coordinates'
task_require "$TASK_SKILL" 'at least two real, reachable, semantically different tap actions'
task_require "$TASK_SKILL" 'Use the selected iPhone tier.*high-end by default; extreme-high-end'
task_require "$TASK_SKILL" 'minimum action coverage is not a cap'
task_require "$TASK_README" 'gradient_tokens.*必填渐变令牌列表.*palette_hex.*可选来源元数据'
task_require "$TASK_README" '所有适用 UI 视觉表现都须完成并验证'
task_require "$TASK_EXECUTION" '设计系统先行与全量 UI 硬门槛'
task_require "$TASK_IDEA" '主题确认后的设计系统决策（硬门槛）'
task_require "$TASK_VISUAL" '设计系统与 UI/UX 评测先行（硬门槛）'
task_require "$TASK_ARCHITECTURE" '设计系统记录与组件选择边界（硬门槛）'
task_require "$TASK_QA" '设计系统与完成度最终门禁（硬门槛）'
task_require "$TASK_ORDER" '设计系统顺序是所有实现任务的前置硬门槛'
task_require "$TASK_README" '主题确认后的设计系统与 UI 硬门槛'
task_require "$TASK_SKILL" 'Theme-confirmed design system and absolute UI quality gate'
task_require "$TASK_SKILL" 'awesome-design-md'
task_require "$TASK_SKILL" 'ui-ux-pro-max'
task_require "$TASK_SKILL" 'There are no soft UI requirements'

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
