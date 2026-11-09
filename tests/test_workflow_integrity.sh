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

forbid_text() {
  if rg -q -- "$2" "$1"; then
    fail "残留旧版冲突规则：$1：$2"
  fi
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

for task_step in {1..21}; do
  rg -q -- "^${task_step}\\. " "$TASK_ORDER" || fail "实施顺序缺少第 ${task_step} 步"
done
[[ "$(rg -c -- '^([0-9]|1[0-9]|2[01])\. ' "$TASK_ORDER")" -ge 21 ]] || fail '实施顺序步骤数量不足'

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

# Apple 4.3/5.6 gates must remain executable contracts, not prose that can
# silently disappear while the runner still reports a green workflow.
TASK_CONVENTIONS="$TASK_DOCS_DIR/01-执行约定.md"
TASK_ARCHITECTURE="$TASK_DOCS_DIR/05-数据与工程架构.md"
TASK_QA="$TASK_DOCS_DIR/07-测试与质量验收.md"
TASK_RELEASE="$TASK_DOCS_DIR/08-发布与About材料.md"
TASK_RUNNER="$TASK_ROOT/flutter-engine-runner/SKILL.md"
TASK_README="$TASK_ROOT/README.md"

require_text "$TASK_CONVENTIONS" '0\.11 Apple 4\.3 与 5\.6 工程级发布门槛'
require_text "$TASK_CONVENTIONS" '0\.2\.1 随机范围与全量硬门槛'
require_text "$TASK_CONVENTIONS" '本流程只允许两类产品内容由智能体随机或自主变化'
require_text "$TASK_CONVENTIONS" '其余适用规格都是硬门槛'
require_text "$TASK_CONVENTIONS" '字体、点击特效、权限、资源、目录及验收仍须完整落实'
require_text "$TASK_CONVENTIONS" '所有适用 UI 视觉表现均属于硬门槛'
require_text "$TASK_CONVENTIONS" 'app-review-risk\.md'
require_text "$TASK_CONVENTIONS" '只更换名称、Logo、渐变、字体、图片、文案、卡片尺寸或导航外壳不构成差异化'
require_text "$TASK_CONVENTIONS" 'Release readiness: Ready for submission'
require_text "$TASK_CONVENTIONS" '0\.12 最新用户硬性覆盖与历史要求对照'
require_text "$TASK_CONVENTIONS" '共 12 张、每任务 1 张'
require_text "$TASK_CONVENTIONS" '旧的总共 1 张或 5 张不再适用'
require_text "$TASK_DOCS_DIR/00-总入口.md" '0\.12.*历史要求'
require_text "$TASK_README" '0\.12.*历史要求'

# Product depth must stay connected from the approved plan to observed delivery;
# do not let the older small seed-data floor become the completion target.
TASK_PRODUCT="$TASK_DOCS_DIR/03-产品定义与导航.md"
TASK_PLANNING="$TASK_DOCS_DIR/02-创意与思维导图.md"
require_text "$TASK_PRODUCT" '^### 4\.3 产品规模与深度表（硬门槛）'
require_text "$TASK_PRODUCT" '所有新项目默认制作.*复杂且内容丰富的完整成品'
require_text "$TASK_PRODUCT" '至少 8 个.*独立.*功能页面'
require_text "$TASK_PRODUCT" '至少 5 个.*核心模块'
require_text "$TASK_PRODUCT" '至少 8 个.*分类、情境族或领域分支'
require_text "$TASK_PRODUCT" '不少于 80 个.*内容条目、案例或领域场景记录'
require_text "$TASK_PRODUCT" '至少 8 条.*端到端任务'
require_text "$TASK_PRODUCT" '至少 5 种.*表达或操作形式'
require_text "$TASK_PRODUCT" '顶层主工作区.*至少 8 个独立功能页面'
require_text "$TASK_PRODUCT" '计划目标.*实际实现.*实际验证.*证据'
require_text "$TASK_PRODUCT" '未接入可达页面.*不计入交付数量'
require_text "$TASK_PLANNING" '^### 3\.2\.1 产品规模与深度映射'
require_text "$TASK_PLANNING" '复杂且内容丰富的完整成品'
require_text "$TASK_PLANNING" '不得以阶段划分、聚焦型工具或工期为由降低规模下限'
require_text "$TASK_PLANNING" '产品规模与深度表.*同一轮.*整体确认'
require_text "$TASK_PLANNING" '检查产品规模与深度'
require_text "$TASK_QA" '产品规模与深度逐项验收'
require_text "$TASK_QA" '复杂成品规模下限逐项核对'
require_text "$TASK_QA" '至少 8 条不同结果的端到端任务'
require_text "$TASK_QA" '计划目标 / 实际实现 / 实际验证 / 缺口'
require_text "$TASK_ORDER" '^2\. .*产品规模与深度表'
require_text "$TASK_ORDER" '^3\. .*产品规模与深度表'
require_text "$TASK_ORDER" '^16\. .*产品规模与深度'
require_text "$TASK_ORDER" '至少 8 条不同结果的端到端任务'
require_text "$TASK_RUNNER" 'Product scale and depth'
require_text "$TASK_RUNNER" 'section 4\.3'
require_text "$TASK_RUNNER" 'Every new project defaults to a complex, content-rich finished product'
require_text "$TASK_RUNNER" 'at least 80 distinct, verified domain entries, cases, or scenario records'
require_text "$TASK_CONVENTIONS" '产品规模与深度表'
require_text "$TASK_CONVENTIONS" '复杂且内容繁多的完整成品'
require_text "$TASK_README" '产品规模与深度表'
require_text "$TASK_README" '所有新项目默认交付复杂且内容繁多的完整成品'
require_text "$TASK_RELEASE" '至少 8 个不同用户结果的端到端任务'
forbid_text "$TASK_PRODUCT" '参考范围不是所有产品的统一数量硬门槛|工具型、聚焦单任务.*对应规模及理由|低于参考范围须.*解释'
forbid_text "$TASK_PLANNING" '参考范围仅帮助制定.*不强制所有产品|按主题允许工具型或聚焦型产品使用不同规模'
forbid_text "$TASK_RUNNER" 'not universal quotas|genuinely focused tool uses sufficient|Aim for the first useful result within about one minute'
forbid_text "$TASK_README" '工具型与聚焦型产品采用有依据的对应深度'
require_text "$TASK_DOCS_DIR/04-视觉与页面功能.md" '^### 6\.13 全项目逐页骨架差异与跨项目去重（硬门槛）'
require_text "$TASK_DOCS_DIR/04-视觉与页面功能.md" '任意两个独立页面至少三个维度有实质差异'
require_text "$TASK_DOCS_DIR/04-视觉与页面功能.md" 'layout-history\.json'
require_text "$TASK_DOCS_DIR/04-视觉与页面功能.md" 'same_layout_as'
require_text "$TASK_DOCS_DIR/04-视觉与页面功能.md" '不固定为顶部 Logo、中间一张卡片'
require_text "$TASK_PRODUCT" '^### 4\.4 大量有效内容与连续翻页（硬门槛）'
require_text "$TASK_PRODUCT" '至少形成三批有意义且非空的内容'
require_text "$TASK_PRODUCT" '不重复、不遗漏、不循环回填'
require_text "$TASK_ARCHITECTURE" '无重叠页边界'
require_text "$TASK_PLANNING" '逐页结构与内容翻页校验'
require_text "$TASK_QA" '全项目逐页骨架与内容翻页专项'
require_text "$TASK_QA" '^### 11\.8 完整视觉效果与功能正确性核验（按用户目标档位）'
require_text "$TASK_CONVENTIONS" '默认不设任何量化性能指标'
require_text "$TASK_RUNNER" 'Every independent page needs a distinct skeleton'
require_text "$TASK_RUNNER" 'at least three meaningful nonempty batches'
require_text "$TASK_RUNNER" 'Do not impose any performance requirements'
require_text "$TASK_README" '全项目每一个独立页面的骨架都不能重复'

# The third required user input must reach planning and acceptance, while
# numerical performance checks remain opt-in; hardware-tier semantics are explicit.
require_text "$TASK_PLANNING" '^### 1\.4 用户提供的性能与功能目标水平'
require_text "$TASK_PLANNING" 'Target level status.*Awaiting user target.*Ready'
require_text "$TASK_PLANNING" '用户原话.*规范化目标.*页面/功能.*验收方式.*实际结果.*证据.*缺口'
require_text "$TASK_RUNNER" 'All three inputs present'
require_text "$TASK_RUNNER" 'Explicit performance targets override the default only for this project'
require_text "$TASK_PLANNING" 'Target iPhone tier: mid-range'
require_text "$TASK_PLANNING" 'Target iPhone tier: extreme-high-end'
require_text "$TASK_PLANNING" '工期无限制.*不触发硬件升级'
require_text "$TASK_PLANNING" '只有高端设备或模拟器时不能据此声称中端真机达标'
forbid_text "$TASK_RUNNER" 'Treat top-tier high-end iPhone hardware as the baseline'
require_text "$TASK_QA" '性能与功能目标水平逐项验收'
require_text "$TASK_QA" '动画前.*进行中.*结束状态'
require_text "$TASK_ORDER" '目标水平 / 实际实现 / 实际验证 / 缺口'
for task_input_entry in "$TASK_START" "$TASK_ROOT/flutter-engine-runner/agents/openai.yaml" "$TASK_README"; do
  require_text "$task_input_entry" '性能与功能目标水平'
done

# Motion is a visual hard gate: reject slide-deck block motion and require
# theme-specific multi-layer animation plans, implementation and runtime proof.
require_text "$TASK_DOCS_DIR/04-视觉与页面功能.md" '^### 6\.14 主题化复杂动画与动态场景（硬门槛）'
require_text "$TASK_DOCS_DIR/04-视觉与页面功能.md" '^#### 6\.14\.1 每个目标页面的专属过场（硬门槛）'
require_text "$TASK_DOCS_DIR/04-视觉与页面功能.md" '^#### 6\.14\.2 Flutter 实时背景场景（硬门槛）'
require_text "$TASK_DOCS_DIR/04-视觉与页面功能.md" '^#### 6\.14\.3 逐页编排与运行验收'
require_text "$TASK_DOCS_DIR/04-视觉与页面功能.md" '至少在.*三个维度中的两个有实质差异'
require_text "$TASK_DOCS_DIR/04-视觉与页面功能.md" '每页背景至少有两个主题相关且运动规律不同'
require_text "$TASK_DOCS_DIR/04-视觉与页面功能.md" '普通 Flutter 页不能用 `exclusions` 豁免'
require_text "$TASK_PRODUCT" 'transition_id.*进入/退出编排'
require_text "$TASK_PLANNING" 'page_transitions\[\].*background_motion\[\]'
require_text "$TASK_ARCHITECTURE" '^#### 9\.3\.2 转场与动态背景的实际组织'
require_text "$TASK_QA" '逐页专属转场与 Flutter 动态背景专项'
require_text "$TASK_QA" 'page_transitions.*background_motion.*覆盖全部 kind 为 flutter'
require_text "$TASK_RUNNER" 'Every Flutter destination needs its own transition_id'
require_text "$TASK_RUNNER" 'Every Flutter page also needs a continuing Flutter-driven background scene'
require_text "$TASK_ORDER" '逐页专属转场与 Flutter 背景动效贯穿'
require_text "$TASK_CONVENTIONS" '逐页专属转场'
require_text "$TASK_README" '逐页专属转场与 Flutter 实时背景也是独立硬门槛'
require_text "$TASK_DOCS_DIR/04-视觉与页面功能.md" '每个 App 页面至少两个可见且不同的动态元素'
require_text "$TASK_DOCS_DIR/04-视觉与页面功能.md" '纯色块拼凑的动画和动态效果绝对禁止'
require_text "$TASK_DOCS_DIR/04-视觉与页面功能.md" '效果提示词公式'
for task_motion_tool in Rive Flame flutter_animate Lottie animator simple_animations FragmentProgram confetti particle_field particles_flutter shimmer liquid_swipe page_transition glassmorphism motion_tab_bar animated_text_kit flame_forge2d three_dart fl_chart CustomPainter PathMetric BlendMode BackdropFilter Ticker AnimationController Curves Matrix4; do
  require_text "$TASK_DOCS_DIR/04-视觉与页面功能.md" "$task_motion_tool"
done
require_text "$TASK_DOCS_DIR/04-视觉与页面功能.md" 'Native Launch Screen 为系统静态例外'
require_text "$TASK_QA" '复杂动态场景逐页验收'
require_text "$TASK_QA" '动画前.*进行中.*结束状态'
require_text "$TASK_RUNNER" 'Never construct animation or dynamic effects from solid color blocks'
require_text "$TASK_RUNNER" 'At least two distinct visible dynamic elements on every App-owned screen'
require_text "$TASK_README" '纯色块.*动画.*绝对禁止'

# Every logical page must have separate, detailed planning artifacts that are
# consumed during implementation and checked again at delivery.
require_text "$TASK_PLANNING" '^### 3\.6 逐页独立思维导图与执行文档（硬门槛）'
require_text "$TASK_PLANNING" '页面数 = 独立思维导图文件数 = 独立执行文档文件数'
require_text "$TASK_PLANNING" 'plan_version.*doc_rev'
require_text "$TASK_PLANNING" '同首页|同其他页面'
for task_page_doc in "$TASK_PLANNING" "$TASK_RUNNER" "$TASK_ARCHITECTURE" "$TASK_QA" "$TASK_ORDER" "$TASK_README"; do
  require_text "$task_page_doc" '\.codex-work/map/page/<page_id>\.md'
  require_text "$task_page_doc" '\.codex-work/exec/page/<page_id>\.md'
done
require_text "$TASK_RUNNER" 'Before implementing each page, read both'
require_text "$TASK_QA" '逐页文档配对与执行一致性验收'
forbid_text "$TASK_PLANNING" '另存规划文档只能作为补充|详细文案、尺寸和字段定义放到图下表格'
forbid_text "$TASK_PRODUCT" '不要求每个主要页面都完全不同'
forbid_text "$TASK_DOCS_DIR/04-视觉与页面功能.md" '不要求每个主要页面都完全不同|实现单卡轮播'
forbid_text "$TASK_RUNNER" 'Preserve the original Welcome UI|one card at a time|Maximum-performance iPhone'

forbid_text "$TASK_DOCS_DIR/02-创意与思维导图.md" '清除成功后返回 Welcome|清除成功.*返回欢迎页'
require_text "$TASK_DOCS_DIR/06-素材与真实照片.md" '之后仍须执行第 11\.6 节最终 iOS 权限双向校验'

require_text "$TASK_ARCHITECTURE" '9\.4 产品差异化与真实功能边界'
require_text "$TASK_ARCHITECTURE" '9\.3\.1 项目自有资源、文件夹与文件短名（硬门槛）'
require_text "$TASK_ARCHITECTURE" '改名与引用是同一任务'
require_text "$TASK_ARCHITECTURE" '父目录改名须更新全部后代引用'
require_text "$TASK_ARCHITECTURE" '四个原始协议 URL 逐字符不变'
require_text "$TASK_QA" 'path-names\.md'
require_text "$TASK_RUNNER" 'all project-owned resources, files and folders'
require_text "$TASK_README" '所有项目自有资源、文件夹与文件能简写就统一简写'
forbid_text "$TASK_ORDER" '直接维护到 `aduit/site/` 与 `aduit/intro.md` 并接入统一 WebView'
forbid_text "$TASK_QA" 'WebView 预览随包本地正文'
require_text "$TASK_ARCHITECTURE" 'differentiation-brief\.md'
require_text "$TASK_ARCHITECTURE" '4\.3 risk: Failed'

require_text "$TASK_QA" '11\.10 Apple 4\.3/5\.6 审核风险专项'
require_text "$TASK_QA" '评价与发现'
require_text "$TASK_QA" 'Release readiness: Blocked'
require_text "$TASK_QA" '11\.3\.1 视觉实现硬门槛'
require_text "$TASK_QA" 'validate_visual_implementation\.py'
require_text "$TASK_QA" 'validate_review_remarks\.py'
require_text "$TASK_QA" 'validate_public_copy\.py'
require_text "$TASK_QA" 'particle-evidence\.md'
require_text "$TASK_QA" 'ui-visual-gates\.json'
require_text "$TASK_QA" '任意配色均可通过色彩方向检查'
require_text "$TASK_QA" '不设色相、色温、饱和度或渐变数量门槛'
require_text "$TASK_QA" '背景文件只能位于对应的 `assets/backgrounds/<page_id>/`'

require_text "$TASK_RELEASE" '12\.4 4\.3/5\.6 发布材料与身份复核'
require_text "$TASK_RELEASE" 'Apple 系统评价 API'
require_text "$TASK_RELEASE" '未知或未提供的项目从最终备注中删除'
require_text "$TASK_RELEASE" '第 1 项固定为 `iPhone 18 Pro, iOS 27`'
require_text "$TASK_RELEASE" 'Screenshot size: 1206 x 2622 pixels \(portrait\)\.'
require_text "$TASK_RELEASE" 'https://www.apple.com/iphone-18-pro/specs/'
require_text "$TASK_RELEASE" '原始竖屏 PNG 的实际像素宽 1206、高 2622'
require_text "$TASK_RUNNER" 'Screenshot size: 1206 x 2622 pixels \(portrait\)\.'
require_text "$TASK_QA" '必须为宽 1206、高 2622'
require_text "$TASK_RELEASE" '第 6 项固定为 `All regions are the same.`'
require_text "$TASK_RELEASE" '不能当作每个新项目已经完成的测试'
require_text "$TASK_RELEASE" '不写 `Not provided; pending confirmation\.`'
require_text "$TASK_RELEASE" '不将验收通过作为后续材料生成的无限等待条件'
forbid_text "$TASK_RELEASE" '以引导页替换生成的 About Home|供离线 WebView 使用|在这些检查完成前不得开始 Review Remarks'
forbid_text "$TASK_RUNNER" 'four untouched site HTML pages|Do not modify the four files in|begin Review Remarks before the guide is accepted'

require_text "$TASK_ORDER" '15\.1 4\.3/5\.6 最终报告门槛'
require_text "$TASK_ORDER" '唯一 Bundle ID'
require_text "$TASK_ORDER" '差异化证据'

require_text "$TASK_RUNNER" 'Apple 4\.3 and 5\.6 release gate'
require_file "$TASK_ROOT/flutter-engine-runner/scripts/validate_visual_implementation.py"
require_file "$TASK_ROOT/flutter-engine-runner/scripts/validate_review_remarks.py"
require_file "$TASK_ROOT/flutter-engine-runner/scripts/validate_public_copy.py"
require_file "$TASK_ROOT/flutter-engine-runner/scripts/validate_path_names.py"
require_file "$TASK_ROOT/flutter-engine-runner/scripts/prepare_ios_config.py"
require_text "$TASK_ARCHITECTURE" '^### 9\.1\.2 打包前源配置补齐与复验'
for task_ios_doc in "$TASK_CONVENTIONS" "$TASK_ARCHITECTURE" "$TASK_QA" "$TASK_ORDER" "$TASK_RUNNER" "$TASK_README"; do
  require_text "$task_ios_doc" 'prepare_ios_config\.py'
  require_text "$task_ios_doc" 'MinimumOSVersion'
done
require_text "$TASK_QA" 'AppFrameworkInfo\.plist.*缺少.*MinimumOSVersion'
require_text "$TASK_CONVENTIONS" '最终报告单列这五项状态'
forbid_text "$TASK_CONVENTIONS" '报告四项状态|单列这四项状态'
require_text "$TASK_RUNNER" 'Report five separate results'
require_text "$TASK_ARCHITECTURE" 'build_verified: false'
require_text "$TASK_ARCHITECTURE" '去掉 `--apply`'
require_text "$TASK_RUNNER" 'Release readiness: Blocked'
require_text "$TASK_RUNNER" 'Delete every unknown, unconfirmed, pending, or not-provided field'
require_text "$TASK_RUNNER" 'Background variety is an explicit hard gate'
require_text "$TASK_RUNNER" 'background\.asset'
require_text "$TASK_README" '4\.3/5\.6 工程审核风险门槛'
require_text "$TASK_README" '背景点缀也是硬门槛'
require_text "$TASK_README" '任意色彩均可使用，不设色相、冷暖、饱和度、数量或渐变配额'
forbid_text "$TASK_ROOT/工作流文档/02-创意与思维导图.md" '建立配色矩阵|至少 4 个.*主色家族|最多 3 张|至少三种清晰可辨的鲜明色彩'
forbid_text "$TASK_QA" '至少两个不同的 `gradient_tokens`|至少三个 Logo 派生 `palette_hex`|至少四种用途明确的 Logo 派生渐变'
require_text "$TASK_README" 'validate_public_copy\.py'

# One reusable App installation must not bypass updates or runtime evidence.
require_text "$TASK_DOCS_DIR/01-执行约定.md" '^### 0\.9\.1 测试安装与构建产物复用'
require_text "$TASK_DOCS_DIR/01-执行约定.md" '增量构建并覆盖安装同一 Bundle ID'
require_text "$TASK_DOCS_DIR/07-测试与质量验收.md" '稳定输出目录、单一串行 runner'
require_text "$TASK_ORDER" '验证复用贯穿第 6–21 步'
require_text "$TASK_RUNNER" 'Unchanged builds need no reinstall'
require_text "$TASK_RUNNER" 'incrementally rebuild and overwrite the same installation'
require_text "$TASK_RUNNER" 'at most one necessary rollback artifact'
require_text "$TASK_README" '验证复用是硬门槛'

require_before '^17\. ' '^18\. \*\*验收首页引导页'
require_before '^18\. \*\*验收首页引导页' '^19\. \*\*最终图片加载检查'
require_before '^19\. \*\*最终图片加载检查' '^20\. \*\*最终 iOS 权限校验'
require_text "$TASK_ORDER" '首页引导页完成验收尝试并记录结果后.*生成不超过 4,000 字符的全英文'
require_before '^20\. \*\*最终 iOS 权限校验' '^21\. \*\*最终五张项目截图'
require_text "$TASK_ORDER" '第 19 步之后、第 21 步截图之前.*全部适用项完成后进入第 21 步'
require_text "$TASK_ORDER" '每个 Flutter 页面.*lib/welcome.*独立.*aduit/welcome.*四个 About HTML 页面和原生 Launch Screen.*独立背景图案'

require_text "$TASK_START" 'TASK_DOC_MANIFEST'
require_text "$TASK_START" 'TASK_RUNNER_SOURCE/scripts/validate_about_copy.py'
require_text "$TASK_START" 'TASK_RUNNER_SOURCE/scripts/validate_visual_implementation.py'
require_text "$TASK_START" 'TASK_RUNNER_SOURCE/scripts/validate_review_remarks.py'
require_text "$TASK_START" 'TASK_RUNNER_SOURCE/scripts/validate_public_copy.py'
require_text "$TASK_START" 'TASK_RUNNER_SOURCE/scripts/validate_path_names.py'
require_text "$TASK_START" 'TASK_RUNNER_SOURCE/scripts/prepare_ios_config.py'
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
for task_step in {1..21}; do
  [[ "$(task_execution_step_count "$task_step")" -eq 1 ]] || fail "第 13 节的实施顺序缺少或重复第 ${task_step} 步"
done

print -r -- 'PASS: workflow manifest, 00-10 document set, steps 1-21, cross-document gates, and final-stage ordering are executable.'
