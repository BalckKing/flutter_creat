
### 主题确认后的设计系统与 UI 硬门槛

主题确认后先使用 `awesome-design-md` 选择最小匹配的 `DESIGN.md` 参考；没有匹配项目时创建自有 `DESIGN.md` 并记录 custom 原因；随后使用 `ui-ux-pro-max --design-system` 针对 Flutter/iPhone 生成并持久化 `design-system/<slug>/MASTER.md`，完成 `.codex-work/ui-ux-review.md` 的九类 UI/UX 评测并全部标记 `Verified`，之后才选择组件和实现页面。现在没有软性 UI 要求：半成品、占位、低质、只换色换图、只安装组件、只有静态设计稿/截图或缺少当前 iPhone 证据的结果都不能交付；只有能力矩阵有事实依据的 `Not appropriate` 才能排除某项主题能力。

### 导航实现硬门槛

### 非游戏深度与 iOS 能力矩阵

非游戏项目默认生成主题工作台，至少包含 12 个独立功能页面、8 个核心模块、12 个主题分类或情境族、120 个有效内容/案例/领域记录、12 条不同结果的端到端任务和 6 种有价值的表达或交互形式。页面需要覆盖发现、创建、编辑、分析、历史/回访、设置、帮助、结果反馈和主题专属主任务等真实职责，不能用单一列表、详情或卡片壳交付。

按主题价值主动评估照片/相机、麦克风/语音、通知、定位/地图、日历/提醒事项、联系人/分享、文件、蓝牙/NFC、运动/HealthKit 等 iOS 能力；适用能力必须有真实入口、授权配置、运行时验证和拒绝后的可用路径，或记录明确的 `Not appropriate` / `Declined fallback` 依据。ATT、IDFA、追踪授权和广告能力继续移除。

非游戏项目同样必须使用真实能力完成精致成品，并使用主题匹配的 UI 组件：允许使用任何合适的 Flutter SDK、第三方 UI/动效包、着色器、渲染器、地图/图表/媒体 SDK 或制作服务，不受组件目录和供应商白名单限制。每个项目在 `ui_component_contract` 写入 `.codex-work/ui-visual-gates.json`，并记录至少两个真实组件的精确版本、来源/许可证、项目内 `actual_consumer`、runtime markers 和当前 iPhone 证据，并设置 `no_simple_line_art`、`no_flat_color_blocks`、`no_solid_color_background`；每个页面登记丰富的 `background.visual_treatment`。纯色背景、简易线条、扁平几何、色块拼接、只安装不消费或只靠渐变/阴影的 UI 均不合格。地图用真实地图 SDK、真实地图瓦片或许可地理数据，图表绑定真实数据，3D/媒体/时间线/扫描/定位/语音使用与主题匹配的真实工具。每项记录 `capability`、`real_tool_or_sdk`、`version`、`license/source`、`actual_consumer`、`fallback`、`runtime_evidence` 和 `formula_record`；包名、安装结果、设计稿或静态截图都不算实现。禁止线条地图、色块地图、静态地图截图、假坐标网格和手绘道路冒充地图。每个动态任务按六部分效果提示词公式记录风格锚定、动画清单、技术手段、数字参数、包授权、约束/Reduce Motion/回退，并在当前 iPhone 上操作和录制。非游戏没有游戏引擎，但视觉质量、真实消费者和运行证据门槛不降低。

最终资源、依赖、无障碍、恢复与安全证据统一写入 `.codex-work/quality-matrix.json`：资源必须有来源/许可、真实消费者、展示位、哈希、字节数和图片体积上限（默认不超过 262,144 字节，Welcome/Logo 可填写更窄限制）；依赖必须有精确版本、许可证和真实消费者；每个页面记录 VoiceOver、Dynamic Type、Reduce Motion 与对比度；离线冷启动、权限拒绝、前后台恢复和清除中断恢复都要有当前构建证据；源码和配置必须完成密钥扫描。运行 `python3 <Skill 根目录>/scripts/validate_quality_records.py --project-root <实际 App 根目录>`，缺少真实工程或证据时输出 `Not verified`，不得把资料包脚本回归当作 App 运行通过。最终 readiness 还必须包含 `asset_staging` 与 `generation_cleanup` 两个门，分别引用 `asset-staging.json`/`validate_asset_staging.py` 和下载完成后精确删除的 `generation-cleanup.json`/`cleanup_generation_history.py`。

工程全程禁用 GetX 和外部路由框架。使用 Flutter 原生 `MaterialApp`/`CupertinoApp`/`WidgetsApp`、`Navigator.of(context)`/`NavigatorState`、`MaterialPageRoute`/`CupertinoPageRoute`/`PageRouteBuilder` 与 `RouteSettings`；Welcome、Initialization、Settings、三个协议入口和主任务必须在原生 Navigator 图中可达。安装后可对真实工程运行 `python3 <Skill 根目录>/scripts/validate_flutter_navigation.py --project-root <实际 App 根目录>`，该检查同时拒绝 GetX 依赖/API 与缺少原生 Navigator 的工程。
# Flutter 工程：复制、安装、执行

这是可移植的 Codex 执行技能资料包。整个文件夹可以放在另一台 Mac 的任意位置，不要求用户名是 `admin`，也不要求放在桌面。

项目 UI 围绕主题、真实内容与 Logo 品牌色自主创作，不固定风格、页面构图或导航外观；交付目标统一为内容完整、视觉精致的成品。构图、排版、配色、图片与动效必须在当前 iPhone 实际页面逐项复核并精修，具体质量与证据标准见第 6.1、6.7、11.3、11.9 节。

历次修改的有效规则统一收录在 [执行约定第 0.12 节：历史要求对照](工作流文档/01-执行约定.md#012-最新用户硬性覆盖与历史要求对照)，同一主题以最新指令为准。仅获授权的主题和已确认范围内的页面/功能组合可随机，其余适用要求全部作为硬门槛，按对应正文检查真实结果。

运行入口需要安装 `$flutter-engine-runner`；没有统一必装的额外 Codex 插件。生成 App 仍需要可用的 Flutter、Xcode/iPhone SDK、适用的 CocoaPods，以及满足质量要求的生图工具/服务与浏览/下载能力，安装器不会自动安装这些工具。可选插件缺失时使用可用 CLI/工具；实际能力缺失则记录受影响项并继续独立任务。

执行确认后，互不依赖的 Logo、素材、页面、协议页、文案和静态校验任务可并行推进；单项受阻立即记录并跳过，不无限等待，只有真实依赖才等待并在恢复后补做。最终 iOS 验收、截图和 Git 交接仍按硬门槛顺序执行。项目实现会按类型分流。游戏是可选主题，不是每个项目都必须制作游戏：只有用户选择游戏主题，或创意明确包含真实游戏模块时，先判断是否需要专用引擎；持续世界、实时物理/碰撞、复杂 3D、高频实体或编辑器导出管线使用精确版本的 Flame/Godot/Unity 等引擎，回合制、卡牌、问答、轻量棋盘和有限状态解谜可用 Flutter 原生实现。游戏运行时使用保留的 `lib/welcome.dart` 沉浸式大厅：首屏只显示 Play、Load、Operation，顶部显示 Exit、Settings；Play 经过 Loading/初始化后进入主游戏，Load 经过 Save Slot/存档加载后进入主游戏，禁止把游戏藏在 Settings、About、二级菜单或隐藏路由；在同一 iPhone App 中验证真实输入、规则更新、成功/失败结果、反馈和重开。非游戏项目才使用普通 Welcome 的 Continue 规则。游戏/混合项目必须先建立 `.codex-work/game-engine.json`，声明 `implementation_mode`、`engine_required`、`decision_reason` 及对应运行时契约；引擎路线完成“引擎环境 → 场景启动 → 已创作资源加载 → 真实输入 → 更新/物理 → 结果 → 反馈 → 重开”，Flutter 原生路线完成“Flutter 运行时 → 场景启动 → 已创作资源加载 → 真实输入 → 规则更新 → 结果 → 反馈 → 重开”，并按原生路线使用动画/效果目录和六部分效果提示词公式。切片未通过不得扩展全量玩法、制作最终截图或执行 Git 交接。非游戏项目不接入游戏引擎或游戏专项验收，按自身主题在多个主要场景使用贴题的本地动态图。 iOS 工程验收只保留 iPhone destination，移除 iPad、Mac、Mac Catalyst 和 Apple Vision；`iPhone Orientation` 只保留 `Portrait`，其余方向全部取消并在修正后重建复验。每个项目独立设计领域架构、导航、页面骨架和视觉样式，不套用同一套底栏/列表壳；素材、运行效果与结构差异均须实测验收。详见第 6.10.2、9.5–9.6、11.11 节。

## 第一次使用

1. 把整个 `Flutter工程` 文件夹复制到新机器，保留下面列出的文件和目录。
2. 双击 `start.command`。它会安装执行技能、复制完整规范，并从远程仓库的 `feature/1.2.1-A1` 分支同步完整 `ios-app-listing` checkout，然后打开 Codex 并将启动语句复制到剪贴板。只安装而不打开 Codex 时，可双击 `install.command`。
3. 首次安装或更新后重新打开 Codex，选择你要存放工程的项目/工作目录，再进入新对话。
4. 在技能列表搜索 `Flutter 工程执行` 或 `flutter-engine-runner` 并选择；也可以直接粘贴并发送：

```text
使用 $flutter-engine-runner，请开始执行。
```

5. 缺少输入时提供项目名称、创意主题、Git 仓库地址，并从极低/低/中/高/极高五档直接选择性能与功能目标水平（功能标准自动制定），仓库地址与主题一并给出，查看完整导图及目标验收标准并回复“确认，按此执行”，随后自主开发。质量复核后按远程 AppListing → `/Users/admin/Desktop/config/ios-app-listing` → 随包契约生成完整材料，不因来源/资源失败取消后续步骤。详尽英文 Description 覆盖真实用途、主模块、任务、实际媒体、成果回访和数据边界，最多 4,000 字符；Intro 仅保留 `All URL` 三个协议 URL；生成阶段将用户提供的项目名称写入主机名，文件名和大小写不变；教育展示标签改 `Popular Science`。改名 `aduit/` 后保留三协议页，按项目类型更新并接入 `lib/welcome.dart`：非游戏项目依第 7.1 节自由设计精致的多章节欢迎构图并保留轮播/分页点、品牌配色和 `Continue`；游戏/混合项目将同一文件实现为一屏式沉浸游戏大厅，只保留 `Play`、`Load`、`Operation` 及顶部 `Exit`、`Settings`。原自包含 `welcome.html` 保留在 `aduit/`，不被 App 加载或打包。非游戏 Welcome 禁止纵向滚动，只允许卡片横向切换；游戏大厅使用竖屏沉浸布局，不混入普通引导卡片。Dart 页用本地 assets、SafeArea 与直接 Dart callback；HTML 保留 Base64 data URI 图片、内联内容，完整 UTF-8 文件尽量逼近 256 KB（建议至少 250,000 字节）且严格小于 262,144 字节，独立验收。两份无协议页脚。完成检查后、Remarks 前，将用户提供的项目名称写入三条具体 HTTP URL 的固定配置；协议文本仅加入结束操作成功后的 Initialization 底部：

```text
By continuing, you agree to our
Terms of Use and Privacy Policy
```

随后接入 Settings 中仅有的 Privacy Policy、Terms of Use、Support 三个 WebView 入口；地址失效不会阻断 App 流程。无需提供域名，也不公开部署。

安装器会先运行 `flutter_check/test_workflow_integrity.sh`，核对 `manifest.txt` 的完整文档集、实施步骤 1–22、跨文档硬性门槛以及第 17–22 步的最终顺序；检查失败时不会覆盖现有技能安装。手动复核可运行：

```bash
zsh flutter_check/test_workflow_integrity.sh
```

选择游戏主题后的通过条件是精细可玩闭环而不是“有一个页面”：保留 `lib/welcome.dart`，但运行时把它作为一屏式沉浸竖屏游戏大厅，首屏只显示 `Play`、`Load`、`Operation`，顶部显示 `Exit`、`Settings`；不显示普通多章节 Welcome、`Continue` 或额外引导卡片。`Play` 必须走 `Loading/初始化 → Game`，`Load` 必须走 `Save Slot/存档加载 → Game`，`Operation` 必须能调节音量和画质并按手机性能适配。必须从游戏大厅到主游戏入口完成至少一局真实操作并能重开，并完成主题化角色/场景、HUD、反馈和交互 UI；空场景、彩色方块、静态截图、无效按钮、点击穿透或隐藏路由均不计入。必须先完成并记录 `.codex-work/game-engine.json` 的 `game_lobby`、引擎必要性、2.5D/3D 视觉契约与可玩垂直切片；引擎路线按引擎环境、场景启动、已创作资源加载、真实输入、更新/物理、结果、反馈、重开执行，Flutter 原生路线按 Flutter 运行时、场景启动、已创作资源加载、真实输入、规则更新、结果、反馈、重开执行，并提交动画/效果目录与六部分效果提示词。未选择游戏主题的项目不执行这组游戏专项门槛。入口/路由、引擎或原生场景、规则结果、美术反馈、生命周期和交付材料允许并行推进，但已选择游戏时核心路径任一失败都会阻断发布结论；`setState() called during build`、RenderFlex overflow、dispose 后旧回调、重复引擎注册、引擎超时、输入命中错误、HUD 遮挡、前后台恢复重复更新、崩溃/白屏/卡死均为阻断项。

需要一次性回归全部资料包契约时，运行 `flutter_check/run_all.sh`。它先检查检查目录布局、默认性能档位和工作流完整性，再按引导页、视觉实现、Review Remarks、公开文案、远程 AppListing 安装器、About 文案、记录与证据矩阵顺序检查资料包自身；任一项失败都会返回非零状态，但这些脚本结果不代表用户 App 已构建、安装、点击或通过运行验收。Review Remarks 检查器固定要求第 1 项依次为 `- iPhone 18 Pro, iOS 27` 与 `- Screenshot size: 1206 x 2622 pixels (portrait).` 两条项目符号：按 2026-10-30 Apple 官方规格选择原生尺寸符合要求且搭载 A20 Pro 的最新 Pro 机型，不使用尺寸不符的 Pro Max；实际截图须读取像素宽高核验，不能裁切/缩放其他机型截图凑尺寸。第 2 项固定按顺序为 `iPhone 15 Pro, iOS 18.6` 和 `iPhone 13, iOS 17.7.1`，两项设备章独立且非空，不随机替换、遗漏、重复或新增设备、第 6 项为 `All regions are the same.`，并拒绝待确认占位语、非 iPhone 设备、网页容器术语、中文、`**` 和超过 4,000 字符的公开备注。固定设备配置来自用户指定，不自动证明当前 App 已完成测试；测试范围和完成结果须另对照当前 App 的记录或用户明确确认，缺少结果依据时保留配置、不编造通过声明。公开文案检查器提供 Dart 直接 UI 字符串、独立 `aduit/welcome.html`、About 静态 HTML 与无障碍属性的补充扫描；间接字符串、脚本动态内容、图片嵌字及运行画面仍需按第 11.4 节复核。它不扫描内部记录，也不替代 Remarks 中真实外部服务的披露。

欢迎页按第 7.1、10.5.1 节先选精细主视觉，再围绕主题与素材自由排版；不同介绍章节有各自的图文关系和视觉节奏，不能整页同骨架换图换字。主图、插画、场景和主要背景图片须有清楚主体、材质/笔触、光影/色彩和空间层次；所有来源及 SVG、Canvas/CustomPainter、代码绘图的位图导出均不得仅以简单线条或色块拼接充当成图。景深、纹理、透明材质与过渡按主题自主编排，静态/减少动态状态仍须精致。独立 `aduit/welcome.html` 的完整 UTF-8 文件尽量逼近 256 KB（建议至少 250,000 字节）且严格小于 262,144 字节；HTML/CSS/JavaScript、Logo、Base64 图片和编码开销全部计入，运行 `validate_public_copy.py --check-welcome-budget --require-near-cap`，不得用无意义填充。`lib/welcome.dart` 同步修改并保持章节 ID、核心文案、图片语义、明亮视觉、轮播/分页节奏及 Continue/准备/错误行为一致，记录 `.codex-work/welcome-sync.md`。四指定视口离线检查各章节和压缩后的实际画质。若已拉取图片资源不足以覆盖已确认的非摄影视觉位，可使用生图软件补充；必须先建立已拉取素材的 `style_reference`，按主体、构图、画幅、光线、色彩、材质/笔触、透明度和视觉密度保持同一视觉风格，逐张并排复核后接入。补充图标记为 `generated`，不冒充真实摄影、实景封面或用户媒体；生图来源不要求统一网站。

```bash
./flutter_check/run_all.sh
```

`@Flutter工程` 是文件夹引用，不等于安装或调用技能。`@` 是否列出技能取决于客户端版本与技能加载状态；看到资料文件不代表执行技能已注册。优先使用技能选择器或 `$flutter-engine-runner`。如果仍未出现，复制安装器打印的“读取并使用……/SKILL.md，开始执行工作流”语句，直接让 Codex 使用已安装技能。

启动器完成的是安装与启动语句准备；它不会自动发送聊天消息。请将语句发送给 Codex 才会执行工作流。

## 验收后的 Git 交接

全部项目验收、修复复验及五张最终截图通过后，最后执行第 22 步：在实际 Flutter 工程根目录运行随技能安装的 `scripts/prepare_git_handoff.py`，用用户提供的 Git 地址完成本地 Git 初始化、关联 remote，并创建/切换到 `feat/1.0.0`。脚本会确认工程拥有自己的 `.git`、读取提交身份、记录 unborn/HEAD、保留已有暂存与未暂存改动，并写入 `.codex-work/git-handoff.md`，这样 Git 界面可以识别工程并允许你直接暂存和提交。新仓库可以保持没有首个提交，但必须已经完成本地初始化；缺少 `user.name` 或 `user.email` 时会如实报告“无法直接提交”，不会编造身份。

示例命令（`<target-project-root>` 必须是真实 Flutter 工程根目录，包含 `pubspec.yaml`、`lib/` 和 `ios/`）：

```bash
python3 <Skill 根目录>/scripts/prepare_git_handoff.py \
  --project-root <target-project-root> \
  --repository-url '<用户提供的 Git 地址>'
```

该命令绝不执行 `git add`、`git commit` 或 `git push`，也不创建初始空提交。已有不同 `origin` 时保留原配置并新增独立的 `user-origin`（必要时带序号）；同名 `feat/1.0.0` 指向其他提交、父仓库控制目标目录或工程边界不安全时停止并保留原状。

启动时只记录仓库地址，不提前关联或创建分支。已有不同远程或同名分支时保留原配置与代码，按第 13.1 节复用安全配置或记录具体冲突，不强制覆盖；验收未通过则延后 Git 操作。最终报告列出实际 remote、分支、HEAD/无提交状态和工作区结果。用户工程仓库与安装器的 AppListing 工具仓库互相独立，详细规则见第 1.5、11.13、13.1 节。

## 一次提供输入，直接进入思维导图

在 Codex 中发送，例如：

```text
使用 $flutter-engine-runner。
创意主题：帮助用户记录旅行见闻，整理照片与语音。
项目名称：Journey Notes
性能档位：3（中，推荐）
Git 仓库地址：https://example.invalid/your-account/journey-notes.git
完整工程目录：/你指定的位置/Journey Notes
请先展示完整思维导图，确认后全权执行。
```

需要智能体生成创意时：

```text
使用 $flutter-engine-runner，请自行生成一个创意主题。
项目名称：Journey Notes
性能档位：5（极高）
Git 仓库地址：git@example.invalid:your-account/journey-notes.git
完整工程目录：/你指定的位置/Journey Notes
```

第三项“性能与功能目标水平”改为五选一，只需点选或回复编号/档名，不用自己写性能参数、具体机型或功能标准；功能完成度、内容深度、交互和验收标准会根据主题自动制定。缺少本项时会完整展示以下五档：

| 选择 | 目标 iPhone 范围 |
| --- | --- |
| 1 · 极低 | 满足最低系统、依赖与必需 API 的性能下沿机型 |
| 2 · 低 | 较旧或较低算力的兼容主流机型 |
| 3 · 中 | 典型中端主流机型 |
| 4 · 高（推荐、默认） | 较新的高端或 Pro 级机型 |
| 5 · 极高 | 当前适用范围内的顶级旗舰能力机型 |

具体参考 iPhone 自动核对后写入导图，不需要用户补报；所有五档完整保留复杂成品、内容与 UI 效果。只询问仍然缺失且没有默认值的输入，已有明确选择不重问；性能档位未明确给出时自动采用第 4 档高端 iPhone。“默认/由你制定”采用高档，针对性能说“不在乎/无限制/不考虑性能”映射极高档；仅工期/内容数量不限不切换档位。用户已明确的机型/指标继续优先，具体标准与验证方法随同一份导图确认，不新增审批。

第四项 Git 仓库地址由你在提供主题时一并给出，已有地址不会重问。示例中的名称、路径与仓库地址请换成自己的；它们不是默认主题、默认项目或真实执行目录。项目名称由你提供，不能由智能体取名；仅 Flutter 内部标识会按工具要求规范化，App 显示名称保留你给定的名称。

## 每个页面分别生成思维导图和执行文档

第 3.6 节规定：每个实际逻辑页面各生成两份详细文件，图与执行正文分开保存：

```text
.codex-work/map/page/<page_id>.md     # 本页详细 Mermaid 与节点对照
.codex-work/exec/page/<page_id>.md    # 本页完整执行规格、任务、验收与结果
.codex-work/map/index.md             # 全局图、跨页关系与逐页图索引
.codex-work/exec/index.md             # 全局依赖、实施顺序与逐页任务索引
.codex-work/page-inventory.md         # 全部页面与两份同版文档的对应关系
```

每页详细展开区域/元素/文案/尺寸、六维骨架、真实内容与翻页、图片/背景/GIF、渐变/字体/图标/Emoji/点击粒子、每个操作与结果、适用状态/恢复、数据/保存/清除、路由/返回、iOS 权限与可访问性、逐步实施和可复现验收。图文件承担关系与流程，执行文件承担具体参数与行动，不用“同首页”、空目录、通用模板或大段重复文字凑详细。

覆盖原生启动页/承接层、Welcome、Initialization、全部实际业务页和独立弹窗、三个协议 HTML 及独立交付 Welcome HTML；同一逻辑页的内容实例和状态写在本页内。所有文件在原有一次确认前写齐并核验，全部页面图在对话中连续分批展示，附各页执行链接和关键摘要，最后只确认一次。实施或恢复某页前完整读取对应两份文件，完成后更新真实状态与证据；改名/增删同步所有引用，最终逐页对照设计、任务、代码/资源和当前 iPhone 结果，不把文件齐全当成实际通过。文档只留在 `.codex-work/`，不放进 `aduit/` 或 App bundle。

## 工程创建在哪里

你当前新建或明确指定的工程文件夹本身就是工程根目录：`pubspec.yaml`、`lib/`、`assets/`、`ios/`、`aduit/` 等直接创建在其中。不要在该目录下再创建“项目名称”子文件夹。项目名称只用作 App 显示名称及合法化后的 Flutter 内部标识，不改变文件夹层级。

未提供位置时，使用 Codex 当前选定项目/工作目录本身作为目标；优先复用本任务的匹配工程，否则直接在该文件夹中创建新工程，不再创建同名子目录。资料包目录和技能安装目录只用于读取流程，不是默认输出位置；若当前工作目录恰好在资料包或技能内，回退到当前用户的 `Documents/FlutterProjects/` 下一个直接目标文件夹，并在思维导图方案中说明，该目标文件夹本身就是工程根目录。

不会再询问项目位置，也不会因为目标文件夹尚不存在而改到资料包里。不要只在 Finder 中选中一个目录就认为 Codex 已获得输出位置；请选定 Codex 工作目录或在启动消息里写明。

## 跨机器与更新

复制时至少包含：

```text
Flutter工程/
├── 工作流文档/              # 整个目录：总入口、十一份正文与 manifest.txt
├── flutter-engine-runner/
│   ├── SKILL.md
│   ├── scripts/             # About、视觉、iOS 配置与 Git 交接检查器
│   └── agents/openai.yaml
├── start.sh
├── start.command
├── install.command
├── flutter_check/
│   ├── run_all.sh
│   ├── test_bundle_layout.sh
│   ├── test_default_performance_tier.sh
│   ├── test_workflow_integrity.sh
│   ├── test_onboarding_guide_workflow.sh
│   ├── test_start_remote_listing.sh
│   ├── test_prepare_git_handoff.py
│   ├── test_prepare_ios_config.py
│   ├── test_validate_about_copy.py
│   ├── test_validate_flutter_navigation.py
│   ├── test_validate_game_project.py
│   ├── test_validate_launch_screen_visual.py
│   ├── test_validate_path_names.py
│   ├── test_validate_protocol_urls.py
│   ├── test_validate_visual_implementation.py
│   ├── test_validate_review_remarks.py
│   ├── test_validate_public_copy.py
│   ├── test_validate_work_records.py
│   ├── test_validate_ios_artifacts.py
│   ├── test_validate_aduit_allowlist.py
│   ├── test_validate_welcome_flow.py
│   ├── test_validate_execution_state.py
│   ├── test_validate_capability_matrix.py
│   ├── test_validate_quality_records.py
│   ├── test_asset_staging.py
│   ├── test_cleanup_generation_history.py
│   ├── test_validate_logo_quality.py
│   └── test_validate_release_readiness.py
└── README.md
```

无需复制个人机器上的 `.codex` 文件夹，也不要只复制 Markdown 或启动器。安装器默认使用当前用户的 `CODEX_HOME/skills`，未设置 `CODEX_HOME` 时使用 `~/.codex/skills`；另在 `~/.agents/skills` 建立指向同一安装的兼容链接。会复用旧版的 `flutter工程执行` 安装目录，避免留下同名的旧规则。实际安装路径以启动器输出为准。

安装后的工作流文档来自资料包，AppListing 则每次由安装器优先从远程仓库 `feature/1.2.1-A1` 分支重新同步为 Git checkout；不会把资料包中的同名目录、旧安装或手写页面作为运行时来源。修改 `工作流文档/` 中的正文或执行技能后，重新双击 `start.command` 同步更新，再重新加载 Codex。安装器会在更新前逐项检查文档清单，缺少任何列出的正文或远程 AppListing 必要文件时不覆盖现有技能。远程同步失败或 checkout 不完整时，自动尝试 `/Users/admin/Desktop/config/ios-app-listing`；两者均不可用时仍安装核心流程并按随包契约继续生成全部材料，单独记录受阻校验，不中断后续任务。旧安装保存在技能目录同级的 `skill-backups/flutter-engine-runner/`，可恢复；不会覆盖其他技能。

Mac 若不允许双击启动器，可在终端输入 `/bin/zsh `，拖入 `start.sh` 并回车。终端入口也支持 `--project-dir` 指定完整工程目录；该路径会加入待发送的启动语句，不会直接创建工程。`--install-only` 只安装，`--help` 查看选项。

生图网站、工具和模型不要求统一，Logo 与背景可按题材选择不同来源，以精致美观、细节/材质/光影、主题准确及页面适配验收，不以同一供应商代替质量。Stargate（`http://stargate.local:3100/`）为可选入口；该地址是生成界面，不是图片下载接口；不能直接 `curl` 后把网页、JSON 或错误响应保存为 `assets/logo.png`。必须从真实任务结果取得二进制图片，并再次检查 MIME、文件签名、尺寸、可解码性和 Alpha。另一台机器需要能使用所选生图工具/服务；路径可移植不代表服务或 Flutter/Xcode 会自动安装。服务失败时记录正式 Logo 为 `Blocked`，优先复用有效 AppIcon 或明确标记的 `unverified` 开发资源继续本地页面和材料生成，不把回退资源宣称为正式品牌。

全局配色契约：Logo、App、Welcome、Initialization、原生启动和 About 统一采用明亮色调。使用清晰、通透、有活力的背景与主题强调色，所有视觉表面都必须实际消费至少一个贴题渐变令牌；渐变方向、色标和材质由主题决定，不能用单一渐变代替图片、纹理、光影或空间层次。避免整体灰暗、压黑或默认套用橙黄夕阳。不再生成调色盘、主题色选择、色相/饱和度/亮度滑杆或 System/Light/Dark 外观切换功能，也不保存这些偏好；系统外观变化时仍保持明亮。项目主题令牌集中写入 `common_module/theme/app_theme.dart`，由 AppPalette/AppTheme 统一管理，Logo 取色仅作可选品牌参考，选用色彩须符合明亮方向。颜色数量、色相家族和渐变数量不设配额，但渐变实际消费是硬门槛；用当前 iPhone 页面检查真实效果与阅读对比度。

Logo 下载或导出后先命名为 `用户提供的项目名称.png`，验收后以该名称放入目标工程 `assets/`，再改为 `logo.png`：`项目名称.png → assets/项目名称.png → assets/logo.png`。取色、App 引用和 Listing 统一使用最终文件，下载路径与改名链路写入品牌记录；项目名称只用于文件名，Logo 画面仍不含文字。

Logo 按主题元素生成 12 张独立候选：模拟现实、手绘、油画、艺术表现四种画风各 3 张。每张用独立提示词和独立任务，实际查看全部候选的主题表达、生成瑕疵、材质/笔触与图标辨识，优先选择可见生成痕迹最少且合格的一张；不按候选色系覆盖、配色差异或比例补图。候选先放在本项目专属暂存目录 `~/Downloads/<sanitized-project-name>/logo-candidates/c01/` 至 `c12/`（本机默认为 `/Users/admin/Downloads/<sanitized-project-name>/`），仅选中图按原命名链路进入 `assets/logo.png` 并继续称为 Logo；其余图按第 6.12 节逐张评估，合适者尽量改为主题/用途短名接入 Flutter 界面，未用项记录原因；比较记录和哈希放在 `.codex-work/`。四种画风都需精致好看、小尺寸可辨。候选统一使用明亮色调，背景与渐变按主题设计；保持主题造型、材质/笔触与完整构图，避免几何色块堆叠、简陋图案，禁止 3D 与明显 AI 生成感。其余生成规格和文件命名条件不变，详细话术见 `工作流文档/02-创意与思维导图.md` 第 2.5 节。

Logo 采用主题级概括：只保留大致行业/对象、一个清楚的主轮廓或关系、画风、克制的材质/光线提示和明亮方向，不把创意中的每个细节复制进提示词。大楼建造主题只需一个可辨识的建筑主体和一个施工提示；楼层、设备、人物、流程、数据和业务模块由 App 页面表达。每个 Logo prompt 最多一个主主体和两个辅助线索，优先保证 60–120 像素辨识度；过度堆叠、拼贴拥挤、缩小后无法识别的结果直接淘汰。

Logo 的光照、主体和题材按主题自主设计，不将每个题材默认套成橙黄色夕阳。太阳、日落和其他环境可按主题使用，但整体保持明亮；不固定色相，也不为某类光照追加审批。

Logo 还需检查主题造型、比例、材质和光线是否自然协调，修复明显畸变、断裂边缘、重复纹理、随机碎片、伪文字或廉价塑料/强光效等生成瑕疵；“自然可信”不要求 Logo 做成照片，也不限制其色彩与渐变选择。每个主要内容列表至少包含两种有意义的明显尺寸；`featured` / `standard` / `compact` 三档按内容在主要浏览体验跨页面覆盖，不要求每页都有三档。多个列表型主要页面至少使用两种有意区分的主编排，例如分组列表、双列网格、精选大卡加横向滚动、瀑布流/不规则卡片或分段式复合布局；单个页面也可以复合使用多种形式。卡片可以长短不齐、大小不一、图片比例不同，但必须由内容重要性、任务优先级、信息密度、媒体比例或排序依据决定，并记录响应式降级与无障碍顺序；不允许随机错落、只为装饰改变尺寸、固定高度截断文字或拉伸图片。设置、协议、权限等便于扫描的功能列表保持整齐。完整实现及验收标准见工作流文档第 6.9 节。

Logo 实际生成失败时，会切换其他实际可用且支持相同质量/格式的模型、工具或网站，再尝试生成；不是只修改提示词。保持高质量、每任务 1 张、总计 12 张独立候选、`1024x1024` 与最终无 Alpha 要求；12 次初始提交加最多 12 次补图，所有模型/候选共用最多 24 次提交与整组 30 分钟预算，不再询问用户。没有可用替代模型或尝试仍失败时，保留真实记录并继续本地 Listing、`aduit/` 和 Remarks。

Logo 下载后还必须实际替换 iPhone 桌面 App 图标、iOS 原生启动品牌图、Welcome/Initialization 页面及现有 App/About 品牌位置，重新构建并检查最终显示，不能仅保存图片。详见 `工作流文档/06-素材与真实照片.md` 第 10.4 节；内容照片封面仍使用贴题的第三方素材，`aduit/site/img/` 仍只保留 `logo.png`。

最后检查还会扫描项目解析出的本地依赖、构建目录和 App bundle，清除其中的 `aduit/` 副本并确认依赖中不得残留；项目根目录的 `aduit/` 交付物必须保留。App 品牌引用 `assets/logo.png`；`aduit` 生成完成后，Entry/Settings 协议链接在 App 内用 WebView 显示，统一写入用户提供项目名称对应的完整 HTTP URL；文档中的 `http://【项目名称】/...` 只作为可搜索定位模板，不能留在最终 App 配置。不跳转外部 App；三个文件名保持原样和大小写，目标不可达时仍显示已写入的具体 URL，并在 WebView 中提供可读失败、返回和有限重试。通过无网络 stub 核对映射，不访问或探测真实 URL，也不把本地协议 HTML 打包进依赖。详细边界见第 10.7 节。

运行时边界：App 只运行 `lib/welcome.dart` 的 Flutter Welcome 表面；非游戏项目显示普通 WelcomePage，游戏/混合项目显示游戏大厅，不使用欢迎 HTML 或桥接。`aduit/welcome.html` 只作独立交付；不写入 lib、pubspec 资源声明、iOS copy/build phase、依赖或 bundle，不另复制/改名打包。`aduit/` 不被运行代码引用；仍保留 Settings/Initialization 的原协议 WebView。最终依赖与 bundle 中 `aduit/` 不得残留，根目录交付目录保留。

页面边界固定：iOS 原生启动页、欢迎页和初始化页三者彼此独立。欢迎页不显示协议文本；协议文本只在初始化页底部显示。

全项目固定明亮外观，不提供颜色调节或明暗模式切换。Flutter 使用 `ThemeMode.light`，iOS 自有界面使用 `UIUserInterfaceStyle = Light`，独立 HTML 与 About 使用 `color-scheme: light`，清理旧的深色自动覆盖和切换脚本；实现边界及旧偏好迁移见第 6.2 节。根据页面任务管理背景、文字与控件令牌；每个视觉表面必须实际消费至少一个主题渐变令牌。系统明暗外观变化时检查 App 仍明亮、正文及控件保持可读，系统减少动态行为照常执行。

Settings 页面必须重新设计为主题化品牌头部、分组图标、状态摘要、真实选项值和有层次的操作区域，不能退化为单调的连续文字行。设置页的结束按钮按项目真实数据选择：有用户上传、导入或创建并保存的内容需要清理时使用 `Clear Data`；确实没有这类数据、仅有随包内容或使用偏好时改为 `Exit App`。不因当前记录为空临时换名，也不为清除按钮增加数据功能。入口、确认框、进行中、失败、成功和无障碍文案一起同步；Intro、协议和 Remarks 描述实际操作。仍是一个二次确认流程：取消原处返回，确认后执行；只有实际采用 Clear Data 且真实清除成功，才清空导航栈并进入 Initialization/`Enter`。Exit App 只结束当前使用，保留偏好和随包内容，成功后不进入 Initialization，不强制终止 iOS 进程。详见第 7.7 节。

启动体验有严格条件边界：iOS 原生冷启动页之后，非游戏项目每次启动只进入含 `Continue` 的 Flutter Welcome 页；游戏/混合项目每次启动进入 `lib/welcome.dart` 的沉浸式游戏大厅（Play、Load、Operation，顶部 Exit、Settings），其中 Play 经过 Loading/初始化、Load 经过 Save Slot 后进入 Game；只有项目实际采用 `Clear Data` 且用户确认、清除真实成功后才创建并显示含 `Enter` 的 Flutter Initialization 页。采用 Exit App 的项目不创建、不注册、不打开 Initialization。这些表面各自独立；非游戏启动准备、百分比、进度和错误恢复均为 Welcome 内部状态，不创建普通 Flutter Loading 页面；游戏 Loading/Save Slot 只在 Play/Load 流程中出现。协议文本只在 Initialization 页底部显示：`By continuing, you agree to our` 换行 `Terms of Use and Privacy Policy`；Welcome、独立 `aduit/welcome.html` 交付页和原生启动页都没有这段文案。用户可见按钮必须使用 `Enter`，`/entry` 仅是内部路由名，禁止 `Entry`、`ertyr`、`entryr`、`entyr`、`entery`、`enrty` 等错误文案。正常启动与条件返回页各自按主题设计完整背景与装饰。游戏大厅、Loading 和 Save Slot 也必须按游戏主题设计完整背景、材质、层次和反馈。原生冷启动页禁止“纯白/近白底 + 居中小方图 + 大面积空白”的正规一图式屏，也禁止只放单张图片或孤立文本；必须使用全屏明亮渐变/混合背景、主题图片层、品牌层、项目名与真实定位文案、装饰层组成有层次的静态构图。启动页必须实际消费至少两种贴题的明亮背景渐变令牌，并将主题图以边缘延展或叠层方式融入画面。原生页以完整静态构图衬托更大 Logo、独立 `PRYRIN` 字标、项目名、定位文案与装饰线，不包含动画、进度或交互；非游戏 Welcome 保留丰富的主题引导卡片与 `Continue`，并在页面内部显示真实准备状态，不提供暂停按钮、暂停/恢复控件或 paused 状态；游戏大厅不显示这些普通引导卡片，按游戏契约使用 Play/Load/Operation；若项目采用 Clear Data，Initialization 提供与实际清除结果一致的说明、`Enter` 和唯一协议页脚；Exit App 项目没有 Initialization。每个视觉表面必须按页面任务实际消费协调渐变令牌，令牌数量不设上限；文字与控件始终保持可读。主任务中至少两个真实可达、语义不同的点击位必须实现主题化烟花/喷泉/拖尾反馈；若产品只有一个可操作点击位则覆盖该唯一点击位。使用 `AnimationController` + `CustomPainter` 在 `onTapUp` 坐标生成具有位置、速度、重力、颜色和拖尾的粒子，定义清晰的结束条件并随生命周期释放控制器，穿透触摸且不遮挡内容。按第 1.4 节选定的 iPhone 档位实现，不以低端性能为理由删减效果或改成占位闪烁；系统减少动态设置开启时关闭粒子与拖尾并保留静态按下反馈。任何 AI 生成图都不得采用简约线条、细轮廓、扁平几何或纯色块堆叠风格，且不能代替规定的真实内容照片。先呈现 Welcome 首帧，再异步准备；进度只由真实必需里程碑驱动，准备就绪且原生承接层淡出完成后启用 `Continue`，必须保持同款原生启动画面至 Welcome 实际加载/首绘就绪后 0.25 秒，再淡出原生承接层；除此以外不为展示动画人为停留，系统减少动态设置即时生效。Welcome 错误态保留 `Try again` 与复用现有确认流程的所选 `Clear Data` / `Exit App`；只有 Clear Data 成功后进入 Initialization，Exit App 成功留在当前可恢复边界。需实际验证小屏/大屏 iPhone、大字号、原生冷启动、Welcome 首帧/受控慢准备、适用的 Initialization、结束操作后返回、错误态及每个选定点击位的点击前/粒子进行中/结果落地证据，并核对重复点击、前后台切换、对比度与无障碍；只改文档或热重载不代表 UI 验收通过。详情见第 6.5、7.1–7.2、10.4、11.3 节。

Listing 生成器优先使用有效的 `assets/logo.png`，不再优先选旧 AppIcon。没有正式 Logo 时可用已有有效图标或项目内的 `assets/dev_brand.png` 继续本地生成，来源记录放 `.codex-work/` 并保留品牌未验证状态；完全无有效图片时仍输出介绍与三页 HTML，缺图和目录契约检查如实失败，后续 `aduit/` 整理及 Remarks 继续执行。

所有页面还须按第 6.10 节落实与任务相关的图文表达，不只美化首页：内容/详情结合主题摄影或图解与有信息价值的模块，搜索使用缩略图/分类图标和元信息，Settings 有品牌区与分组图标，媒体页呈现真实预览与反馈，空/错误态有对应图形和下一步。确认框保持风险清楚、操作简洁，协议保留完整易读正文与品牌层次。每页及适用状态都纳入规划和当前构建验收；纯文字堆叠、反复贴 Logo、同文换容器、假统计或无关装饰不算丰富，必要实景照片仍从已列第三方网站取得并核许可。

内部 UI 使用唯一正式 Logo 并减少重复：AppIcon、iOS 原生启动页及其同款承接层保留选中 Logo；所有 HTML 不因这次调整改动，继续按原规则使用正式 Logo，Welcome Flutter 外层不额外叠加。Initialization、Settings、内容等普通 Flutter 页面优先用其余生成图中合格贴题的图，逐张评估并尽量利用，进入 assets 前按主题/用途另起短名，不叫 `logo2`、`logo_alt` 或备用 Logo。资源放入 `assets/illustrations/<feature_or_page_id>/` 并实际接入；记录每张的源候选/哈希、新名称、消费位置、当前截图与未用理由。明显瑕疵或不适用图不强塞，转用图不替代真实摄影，正式 Logo 来源保持不变，主题色仍可自由选择；可自行绘制图解补足需要。详见第 6.12、10.4 节。

所有自有界面的图片统一使用圆角，覆盖 Logo、列表/详情图片、缩略图、视频封面、媒体预览及 HTML 内嵌图；图片本身须实际裁剪，加载、错误、放大与转场中也不能露出尖角。按主题适当增加 Logo 配色的细边框，同类图片圆角与边框保持一致。原始 Logo 仍为无 Alpha 图片，AppIcon 使用系统蒙版。最终逐页检查实际显示，详见第 6.3、11.3、10.7 节。

协议链接文档示例使用完整 HTTP 搜索模板 `http://【项目名称】/xxx.html`，其中 `xxx.html` 仅对应 `PrivacyPolicy.html`、`Terms&Conditions.html`、`Support.html` 三个固定文件；协议链接统一使用三个完整 HTTP 模板：`http://【项目名称】/PrivacyPolicy.html`、`http://【项目名称】/Terms&Conditions.html`、`http://【项目名称】/Support.html`。三个文件名 `PrivacyPolicy.html`、`Terms&Conditions.html`、`Support.html` 千万不要改动或改大小写。App 内使用 WebView 显示，不跳转外部 App；生成时直接写入用户提供的项目名称；`【项目名称】` 仅保留在文档搜索模板中，不得留在最终 App 配置。

`.codex-work/` 只保存开发计划、记录、证据和备份。确认可提交后可以整目录删除，主项目的源码、资源、依赖、测试、构建配置和最终 `aduit/` 材料都不得依赖它；实际图片、主题令牌、协议 URL 和必需工具保存在各自项目目录，不通过软链接指回工作记录。最终第 19 步会可逆地把该目录移出工程，实际验证缺席时的依赖解析、测试、构建和 iPhone 运行，再恢复记录供你保留或删除。规则和验收见第 9.2.1、11.12 节。

## 文档集与原入口

原长文档已拆分到同一资料包下的 `工作流文档/`。唯一维护源是总入口 `工作流文档/00-总入口.md` 和按清单列出的十一份正文；旧版长文档兼容入口不是必需文件。

```text
工作流文档/
├── 00-总入口.md
├── 01-执行约定.md
├── 02-创意与思维导图.md
├── 03-产品定义与导航.md
├── 04-视觉与页面功能.md
├── 05-数据与工程架构.md
├── 06-素材与真实照片.md
├── 07-测试与质量验收.md
├── 08-发布与About材料.md
├── 09-实施顺序与交付报告.md
├── 10-第三方资源来源.md
└── manifest.txt
```

运行语句、执行顺序和原第 0–16 节编号不变。技能会读取总入口并按顺序完整读取十一份正文，不是只看目录或按标题猜测内容。规范资源根仍是文档集的父目录；AppListing 运行时目录由安装器从远程仓库同步，工程输出位置不受拆分影响。跨机器复制时必须带上整个文档集、执行技能和启动器，不能只复制启动器或兼容入口；资料包不需要也不应携带本地 AppListing 副本。安装器在旧版长文档不存在时，会用总入口生成安装副本中的旧路径兼容文件。

拆分时只调整了文件组织，没有改写规范正文；后续修改需求时编辑对应章节，并同步有实际关联的摘要或引用。拆分前原长文档备份在本机的 `skill-backups/flutter-engine-runner/source-documents/`，不参与执行。

## 页面拆分与品牌视觉

Logo 生成保留 12 张候选跨画风比较（四种画风各 3 张）；可选地参考成品取色，设计明亮的项目主题并在每个视觉表面实际消费渐变令牌，颜色与渐变数量不设上限。最终 About 三页使用项目选定的品牌视觉，包括按钮、链接与明亮阅读表面；页面正文、引导卡片、Intro 和 Remarks 做事实核对与去重编辑，使用具体自然的英语，减少套话和重复信息。

About 使用由正式 Logo 派生的小尺寸 PNG（通常 128–256 像素，目标 8–20 KiB，尽量不超过 24 KiB），按清晰度与实际体积选择最小可用版本，保留主 `assets/logo.png` 原规格。引导页内嵌压缩字节并计入整个 HTML 预算；正文和按钮不等待图片下载/解码，必须检查 Logo 延迟、损坏或失败时仍可操作，详见第 12.1 节。

三个协议 HTML 页面与独立 `aduit/welcome.html` 不得含草稿/开发分发/待配置/发布前待补提示。生成与最终精修后对三协议页运行 `validate_about_copy.py`，并单独检查 HTML 交付页与实际 Dart 页文案/渲染；事实缺口仅记内部，不编造联系方式或改三个协议文件名。

用户可见的 Dart 文案、Welcome/About 文案、按钮、错误/空态和 VoiceOver 文本必须是自然英语，不出现中文或 `H5`、`SDK`、`广告`、`第三方框架`、`技术实现`、`内部模块`、`lib`、`package`、`packages`、`local`、`device`、`测试`、`模板`、`马甲`、`过审` 及其变体。运行 `scripts/validate_public_copy.py` 扫描可见字符串；源码标识、注释和 `.codex-work/` 内部记录不属于公开文案。

每个项目的产品结构都从用户当前提供或明确要求生成的创意推导，不固定套用 `Home / Explore`、通用卡片墙或同一套媒体入口。规划中写清目标用户的具体问题、现在的替代做法、主题专属的标志性动作、首个有用结果和可在本机保存/回访的成果；摄像机、相册、麦克风、通知、定位、日历、联系人、文件、蓝牙/NFC、运动/HealthKit 等能力先按主题能力矩阵评估；适用项服务真实主题任务并提供拒绝降级，不再用媒体能力全部跳过作为默认规则。差异化必须体现在内容模型、任务顺序或交互规则中，不能只靠换 Logo、渐变或卡片样式。以上内容随既有思维导图和一次整体确认，不增加审批步骤；无依据的竞品结论标为未验证。

非游戏项目默认按主题工作台交付，必须覆盖发现、创建、编辑、分析、历史/回访、设置、帮助和结果反馈等真实职责，不能退化为单一列表、详情或卡片壳。规划时新增第 4.3 节“产品规模与深度表”，与既有思维导图在同一轮整体确认。所有新项目默认交付复杂且内容繁多的完整成品，硬性下限为至少 12 个独立功能页面、8 个核心模块、3 层结构、12 个主题分类/场景族、120 个有效内容/案例/领域记录、12 条不同结果的完整任务及 6 种信息/交互形式；重要详情至少含 4 个有价值的信息模块。该下限适用于内容型、工具型和混合项目，工具型可以采用真实案例/场景表达但不能减量，且所有维度都没有人为上限。不以阶段划分、工期、工具/聚焦型定位或“后续版本再做”缩小交付范围，也不虚构或重复内容凑数。先定义领域对象/关系，再规划分类覆盖、模块数据承接、真实动作、可回访结果及适用状态；确认后对照计划目标、实际实现、实际验证与缺口。要求执行到实施和最终质量复核，不以字数、页数或耗时代替实际质量；详细规则仅维护在第 4.3 节。

全项目每一个独立页面的骨架都不能重复，Welcome 与 Initialization 也不再固定居中卡片或完成图标样式。按第 6.13 节记录构图、区域顺序、图文关系、内容层级、操作区和导航结构，任意两页至少三个维度有真实差异；对照可取得的跨项目历史，换色换图换文案不算。统一主题与通用控件仍可共享，布局差异通过当前 iPhone 页面证据核验。

主内容必须丰富且可继续翻页：按第 4.4 节规划至少三批有意义的非空主内容，检查首、中、末批、终点、详情返回及筛选后分页，稳定 ID 与实质信息均不重复、不回填循环。欢迎介绍轮播不计入主内容量，Welcome 仍单屏不可纵向滚动。

整体 UI 与导航由当前主题、核心任务和 iPhone 操作方式决定；Tab 没有最低数量，不要求多个 Tab，也不强制顶部标签或底部导航栏，允许零 Tab 与单一主工作区。功能页面、模块及分类数量不代表 Tab 数量；可以采用目录、工作台、画布、步骤流程、顶部/分段切换、按需面板或其他合适组合，参考形式不是固定模板。用户未指定导航时，规划中比较至少两种结构不同的可行导航（考虑无固定底栏方案，不适用时说明任务原因），在既有一次思维导图确认中说明选定理由；有真实高频平级切换需求时仍可选择底部导航。首屏、排版、内容组织、控件和动效也要随主题设计，不能只把底栏改成悬浮样式。全项目按第 6.6.1 节使用按创意选择的标题色彩、斜体/斜切标题、至少三种有意且可复用的字体风格、sentence case 正文和有语义依据的重点词强调，保持可读对比度和 Dynamic Type/VoiceOver 顺序；排版与 UI 精修必须覆盖每个页面、状态和当前构建的 iPhone 检查。按实际方案生成路由与状态，并验证全部入口可达、返回/任务恢复和无障碍，详见第 5.1、6.1、6.6.1、11.1、11.3 节。

每个独立 App 页面都使用自己的 Dart 文件，并按稳定 `page_id` 分类；`main.dart` 只启动并装配根 App，不集中编写所有页面。每页按第 6.11 节实现独立主题背景，必须保留真实半透明主题图片点缀，并可叠加程序场景、生成/制作的动画或混合效果。动画工具与服务不限，可自由组合第三方组件，不要求先把动画生成成图片，但不能省略独立图片层。实际背景图片按 `assets/backgrounds/<page_id>/<page_id>_background.png` 或真实格式保存和引用；程序/动画场景另登记实际代码、入口及所用资源，同时登记图片 asset、opacity、placement，不创建占位文件。装饰不得代替真实照片。

图标、Emoji 和文字密度均为独立硬门槛：普通页面与 Welcome 引导卡片使用统一语义图标、首屏贴题 Emoji、简短摘要和有内容价值的图文/步骤模块，详细内容合理分层且完整可达；不能做成连续文字墙、只加背景或只在代码中声明装饰。`ui-visual-gates.json` 分别记录 `icons`、`emoji`、`text_density`，用实际实现与当前 iPhone 构建证据逐页验收；文字拥挤的页面还须按第 6.10.1 节重组内容并加入贴题图片、图解或 GIF，GIF 本地打包并实测播放、暂停/恢复和减少动态静态预览，不以首帧截图冒充播放正常。原生启动页、法律正文和关键媒体/警示控件按第 6.8 节保留各自边界，详细 Intro 不缩减。

全项目主要页面统一采用明亮色调并实际消费主题渐变令牌，并保留高对比阅读区域；采用动态渐变时，系统减少动态设置开启后回退为同配色静态画面。主任务中至少两个真实可达、语义不同的点击位必须采用 `AnimationController` + `CustomPainter` 在 `onTapUp` 坐标绘制主题粒子，若产品只有一个可操作点击位则覆盖该唯一点击位；控制位置、速度、重力、颜色和拖尾，明确生命周期结束条件，触摸穿透，不遮挡内容。粒子必须有主题对应的具体形态/材质/纹理，不能是统一纯色圆点/色块拼贴。按第 1.4 节选定的 iPhone 档位实现，不以低端性能为理由删减效果或改成占位闪烁；减少动态时关闭粒子与拖尾并保留静态按下反馈。必须在当前 iPhone 构建逐个点击并保存点击前/进行中/结果落地证据，核对重复点击、前后台切换、对比度与无障碍；源码、热重载或静态演示不能代替运行验收。

动画动态效果另设独立硬门槛：纯色块拼凑的动画和动态效果绝对禁止；每个 App 页面（系统强制静态的 iOS 原生 Launch Screen 除外）默认至少有两个不同的、主题相关的可见动态元素。纯色几何块移动、简单线性渐变加淡入/缓动不能充数。逐页执行文档写清主体材质/纹理、前中后景、不同轨迹与因果状态、技术手段、具体数值、循环/结束和 Reduce Motion 替代；使用 Rive、Flame、flutter_animate、Lottie、着色器、粒子或 Flutter 原生绘制工具时，只按真实需求选取，先核对精确包、版本、iOS 兼容、维护状态和许可证，不默认全装。`.codex-work/ui-motion-gates.json` 逐屏记录场景、实现引用与录屏证据；用当前 iPhone 实际播放录制并逐帧检查块状拼贴、对象失真、轨迹僵直、循环断裂和文字遮挡，修复后复录。静态 Reduce Motion 画面不代替默认动态验收。详见第 6.14、11.8 节。

所有适用 UI 视觉表现都须完成并验证；明亮色调与渐变实际消费按第 6.5 节落实，渐变令牌数量不设上限。除随机主题和随机页面/功能组合外，页面层级、五类字体角色、标题斜体/斜切、所选色彩及适用渐变的 Reduce Motion 回退、点击按下/焦点/禁用/成功/失败态、页面专属装饰、圆角图片与边框、真实图文模块、列表尺寸层级与差异化编排、空/错误/权限/清除状态、系统明暗变化时仍保持明亮、Dynamic Type、VoiceOver、安全区、对比度、横竖屏 iPhone 适配都必须实际落到页面代码并由当前 iPhone 构建截图或录屏证明。发布材料前必须运行 `python3 flutter-engine-runner/scripts/validate_visual_implementation.py --project-root <target-project-root>`；预检、运行证据或适用视觉项任一缺失都标记为 `Blocked`/`Not verified`，不能用主题令牌、设计稿、源码关键词、热重载或单一首页截图声称完成。

逐页专属转场与 Flutter 实时背景也是独立硬门槛：每个目标页面绑定不同的 transition_id，在揭示机制、运动轨迹/空间、图层编排中至少两个维度有实质差异，覆盖实际路由与主目的地切换、对应返回和侧滑取消；同页再次进入保持一致，不随机抽效果，也不只换时长/方向。每页进入后持续运行至少两个主题化 Flutter 背景层，保持明亮色调，可用任意可运行的动画生成/制作工具、引擎、着色器、第三方组件及其合成，实际素材随包，半透明图片点缀仍为独立必需项。静态画面、缺少主题动态层的单片循环或简单渐变不能充数。page_transitions、background_motion 两项覆盖全部 Flutter 表面并提供当前 iPhone 录屏，缺页或只有截图时预检失败；默认动效、减少动态、生命周期、触摸/阅读边界与静态原生启动衔接分别实测。详见第 6.14.1–6.14.3、11.3.1 节。

背景点缀也是硬门槛：每个页面和交付 HTML/原生启动表面都须实际显示各自的主题图案、纹理或完整场景。在 `.codex-work/ui-visual-gates.json` 按第 6.11 节登记 image/procedural/animation/hybrid，保留真实调用和当前截图/录屏；`gradient_tokens` 是每个视觉表面的必填渐变令牌列表，必须有实际页面/组件消费者；`palette_hex` 是可选来源元数据，允许省略或空列表，不设条目数量。所有模式均检查真实半透明图片的文件/注册/引用，以及数值 background.opacity（0 与 1 之间）、非空 background.placement；程序或动画模式另检查独立 scene_id、implementation、entrypoint、实际随包 resources 和 Flutter 的当前 iPhone recording。正常与减少动态状态实查图片可见且不被不透明容器遮挡，静态字段通过不能代替当前构建截图。混合模式两项都满足；原生启动保持静态。制作工具、服务及第三方组件合成不限，仍须有主题层次、真实接入与播放，不能用重复场景、色块拼凑、单一渐变或占位文件通过。

硬件提供极低、低、中、高、极高五档供直接选择，默认推荐高端 iPhone；性能“不在乎/无限制”等表述映射极高档。未给出具体量化指标时，不自行设定帧率、帧耗时、内存、CPU/GPU、耗电、启动/响应速度、安装体积或性能测试/报告要求；用户明确指标才按确认的条件执行相应测量。五档均完整保留内容和 UI 效果，崩溃、黑白屏、图片失败、操作失效及数据问题照常修复并验证；实际设备与目标不符时如实记录，不冒充真机达标。系统减少动态、正确生命周期、可读性/无障碍、250 毫秒启动衔接、故障恢复边界和既定 HTML/Logo/文件契约保留。详见第 0.2.2、1.4、11.8 节。

Settings 页最底部的版本文案也是硬门槛：只显示 `项目名称 · 数字版本号`，例如 `ProjectName · 1.2.3`。使用当前 App 的真实版本，`1.2.3+45` 只显示 `1.2.3`；版本不含 `feat`、`release`、分支/渠道、`Version`/`v` 或构建号。规则与最终画面核验见第 7.6、11.3 节。

工程制作不限总时长，以质量决定完成：不因已运行数小时、首次构建成功或达到三轮 UI/两轮资源的最低要求提前交付。持续处理已发现且可执行的功能、视觉和素材细节问题，实际修改后在当前构建复验，保留全部 UI 效果；完成条件与执行方式见第 0.2.3、6.7、11.9 节。外部请求超时与重试上限继续用于避免无效等待，不构成工程制作时限；不空等凑时长、不编造工时，也不以主观完美无限增加无关工作。

最终图片检验是必须完成的修复闭环：在最终 iPhone 构建逐一打开全部适用展示位，发现图片不显示、错图、解码错误、遮挡或持续占位就定位、实际修改、重建更新安装并在原位置复验；仍异常就继续修，直到全部图片正常显示。不能只写问题清单、用占位图遮掩或留给用户修。按第 10.7–10.7.1 节保留当前构建的逐图/逐位置证据，失败和未验证项均为 0 才能通过；后续资源或配置变更后补做受影响复验。客观外部阻断保留真实缺口，不能将项目宣告为全部完成。

## 真实照片素材要求

可通过 Google 图片搜索找到并下载许可适用的原图，也可使用下述素材网站；文件先进入本项目专属 `~/Downloads/<sanitized-project-name>/content/` 暂存区，再复制到当前项目 `assets/`，实际生成/下载的背景图片先进入 `~/Downloads/<sanitized-project-name>/backgrounds/<page_id>/`，再复制到 `assets/backgrounds/<page_id>/`；不把公共 Downloads 当项目资源库。不同独立内容展示位使用不同原图，不用改名/裁切图凑数。制作阶段完成下载与打包，App 不运行网络图片加载或首次打开再下载缓存；按本地 key 加载并完成最终构建的断网冷启动/逐图解码检查，避免图片异常卡住页面或崩溃。

图片生成或下载开始前，先依据用户提供的项目名称生成一个仅用于素材暂存的安全目录：`/Users/admin/Downloads/<project-name>/`（在其他机器上等价为 `~/Downloads/<sanitized-project-name>/`）。项目名称只做文件系统安全化，不改变 App 显示名称；目录至少分为 `logo-candidates/`、`backgrounds/`、`content/` 和 `exports/`，所有本项目生成图、下载图和导出中间文件都写入该目录，禁止直接写入公共 Downloads 根目录或其他项目目录。验证格式、许可、哈希和去重后，将需要随包的文件复制到当前项目 `assets/` 对应目录并记录旧路径→新路径映射；运行时代码只能引用项目内 `assets/`，绝不引用 Downloads 的绝对路径。保留项目专属暂存目录以便复核，不把它打包进 App 或 `aduit/`，也不扫描、移动或覆盖其他项目的下载文件。

统一资源暂存根目录由 `scripts/prepare_asset_staging.py` 实际创建并写入 `.codex-work/asset-staging.json`；所有生图、拉取、浏览器导出和转码文件只能进入 `/Users/admin/Downloads/<sanitized-project-name>/` 下的 `logo-candidates/`、`backgrounds/`、`content/`、`exports/`。运行 `validate_asset_staging.py` 拒绝公共 Downloads 根目录散落图片、其他项目文件、工程内伪目录、未登记子目录和符号链接。生图下载完成后必须通过 Stargate 页面或明确记录的官方删除动作删除本批生成记录，并以 `.codex-work/generation-cleanup.json` 留存 task IDs、已下载路径、精确删除 IDs、时间和证据；这一步就是生成记录删除门，运行 `cleanup_generation_history.py` 验证，删除不完整或执行方式不明不能通过。

项目自有文件夹和文件名禁止出现 Codex 或 AI 相关词：包括工程根目录名、源码、资源、测试、工具、原生自定义文件、`aduit/` 材料及开发记录，按词及常见变体检查 `codex`、`ai`、`openai`、`genai`、`aigc`、`llm`、`gpt` 等；普通 `main.dart`、`rain.jpg` 不因字母组合误判。内部记录统一改为 `.codex-work/`，历史工作记录须实际迁移并同步引用、核对冲突，不覆盖记录或保留旧名软链接。`validate_path_names.py` 扫描真实目录，`keep` 不得豁免；外部技能路径、工程外父路径和真实构建/依赖强制路径保留工具边界。用户指定磁盘名冲突如实说明，不擅自移动工程或改展示品牌。具体见第 9.3.1 节。

所有项目自有资源、文件夹与文件能简写就统一简写，但只修改有准确、清楚缩写的名称；已简短、无合适缩写或缩写会歧义的保留，不机械截断。生成前建立主题词表，架构建立后、资源整理后和交付前运行 `validate_path_names.py` 扫描实际工程；可缩写项未改不能通过命名验收。具体词表/保留项格式与命令见第 9.3.1 节；改名必须同步代码/配置/数据/原生工程及测试中的全部引用，并检查受影响构建和断网加载。符合禁用词规则的固定路径与用户项目磁盘名、用户显示名和三个协议文件名保持原样，详见第 9.3.1 节。`assets/` 内项目自有资源使用简短的英文主题/用途名称，例如 `assets/media/city/cbd_cover.jpg`；去掉下载附带的网站名、日期/时间戳、供应商编号和随机串，专有名词统一使用可辨认的缩写。完整名称、缩写及旧新路径映射保留在 `.codex-work/asset-names.md`，来源与许可记录继续保留；固定 `assets/logo.png` 和逐页背景路径不变。既有资源改名后同步声明、代码与数据引用，并重建确认实际加载，详见第 10.1.2、11.1 节。

如果返回 403、429、超时、登录墙、验证码或许可证无法核验，将对应照片项记为 `Blocked`/`Not verified`；继续生成本地 AppListing、About、`aduit/` 和 `aduit/review/remarks.md`，不能再以素材失败停止整个交付流程。

执行流程必须实际搜索 Pexels、Pixabay、Unsplash、Wikimedia Commons 等第三方网站，核对主题与许可，下载真实实物/实景摄影到目标工程的 `assets/media/` 并接入 App 页面。`http://stargate.local:3100/` 用于生成 Logo，也可生成选定图片路线的逐页主题化背景装饰；复杂背景可直接动画生成或第三方组件合成，动画工具/服务不限且不强制为动画生图，但每页半透明图片点缀仍须实际取得、接入并验收。图像生成不得用于生成或替代内容照片、实景封面、视频帧或其他真实摄影。实际背景图片须按 `assets/backgrounds/<page_id>/<page_id>_background.png` 或真实格式单独保存并由对应页面引用；程序/动画场景按第 6.11 节记录代码入口、所用资源与真实运行。原生图标、代码矢量符号、其他装饰插画与渐变等非摄影 UI 素材不需要从照片网站取得，也不计作真实照片。没有 API Key 或资源下载技能时仍尝试可用公开网页与合法下载方式；来源失败则切换其他来源，按规范有限尝试，不无限等待。

Emoji、渐变、矢量插画、AI 拟真图或仅写素材清单不能代替真实照片。验收要有来源与许可、实际页面截图及离线展示证据；不能只下载不使用，也不能用一张图填满所有分类。所有可用途径确实失败时可继续独立开发，但照片缺口必须明确报告，不能把该项资源质量标为通过。搜索记录与接触表在目标工程 `.codex-work/`，内容照片不进入 `aduit/`。

### iPhone 与权限配置

项目完成后，第 20 步按第 11.6.1 节单列五项最终检查：`Info.plist` 缺失/路径/格式/用途键报错、`ios/Flutter/AppFrameworkInfo.plist` 缺少标准 `MinimumOSVersion`、CocoaPods 工程的 `Podfile` 不存在或无效、实际插件/API 必需的照片权限宏缺失，以及 ATT 清理。查看实际 target 的 plist 输入/生成设置、最新命令日志、权限插件所属 pod target 的有效宏与最终构建产物；发现缺陷就修复、重建和复验。ATT 的专用依赖、请求/状态流程、`NSUserTrackingUsageDescription`、框架链接、启用宏、IDFA 与追踪初始化都须移除或禁用，不能只隐藏弹窗。合法自动生成 plist、已验证的无 CocoaPods 接入和纯系统照片选择器按实际情况判定，不添加假文件或多余权限。五项的报错、修复和证据写入既有 `.codex-work/ios-permissions.md`，最终报告逐项给结果，未实测不写通过。

每个新建及复用项目都必须适配执行当日最新稳定版 iOS 生命周期，最低部署版本仍为 15.6 或真实依赖要求的更高值。流程会核实稳定 iOS/Xcode/Flutter 组合，成套核验 UIScene、AppDelegate/SceneDelegate、engine/插件/通道注册与原生窗口时机，并在当前 iPhone 构建检查冷启动、前后台、系统中断、Scene 恢复及清除恢复；原生承接层在 Welcome 实际就绪后前台保持 250ms 再淡出的规定继续生效。源码和编译成功不等于运行通过，缺最新 runtime 或真机时如实记录，不用旧系统结果冒充兼容证明；独立 AppListing/About/Remarks 继续生成。详见第 9.1.1、11.1.1 节，证据纳入已有 `.codex-work/quality.md`。

本流程只创建、构建和验证 iOS iPhone App，最低 iOS 部署版本为 15.6；实际依赖要求更高时保留更高版本，并按正文核对 Podfile、所有构建 target 的解析设置及可用产物。运行与截图必须明确指定 iPhone 机型及 UDID；没有可用 iPhone 时继续可执行检查，不回退到其他设备或平台。按实际权限插件检查 `ios/Podfile` 并尽力设置最小权限宏；使用 PhotoKit 整库读取 API 时，必须设置并从 Pods 解析后的编译设置证实 `PERMISSION_PHOTOS=1`；只用系统照片选择器时不启用整库权限宏。宏配置失败需记录，但不得因此中止 Pods 安装或 iOS 打包尝试。不集成追踪功能；ATT 权限申请、弹窗、四状态、触发条件与启动任务全部移除，同时清除请求 API、用途键、框架链接、启用宏、IDFA 访问和追踪依赖。发现仍会追踪的组件时禁用、移除或替换，不恢复该授权流程；核验实际数据流与最终产物，并据实披露。宏配置、构建结果与权限运行验证分开报告，失败的权限路径不能标为通过。摄像机、相册、录音、通知、定位、日历、联系人、文件、蓝牙/NFC、运动/HealthKit 等能力按主题能力矩阵评估；适用项添加真实页面、插件或权限，不适用项记录依据。全部实现、发布材料、图片及依赖检查结束后，执行第 11.6 节 iOS 权限双向校验：实际 API 必需的用途键/宏/能力配置必须完整有效，无真实用途的配置、请求和依赖全部移除；无受保护能力时验证零无关权限。若修正后重建，刷新受影响的最终显示证据并再次核对产物权限；随后按第 12.5 节完成最后的五张项目截图。详情见工作流文档第 0.7、11.6–11.7 节，证据记录于项目 `.codex-work/ios-permissions.md`。

为避免只写规范却漏配，已提供可执行的 `flutter-engine-runner/scripts/prepare_ios_config.py`，并随启动器安装到技能目录。按第 9.1.2 节在实际 App 上运行：`--project-root "<App根目录>" --photo-access read-write --permission-handler --minimum-ios 15.6 --apply` 适用于通过 CocoaPods 接入 `permission_handler_apple` 且需要 PhotoKit 读写的工程。它保留既有 plist 字段及更高版本，补标准 `MinimumOSVersion`，在唯一现有 Hook 末尾配置插件全部配置的 `PERMISSION_PHOTOS=1` 并禁用其 ATT 宏，保留其他宏；先验证、备份再写入，可重复执行。只添加照片改用 `add-only`，纯系统选择器用 `picker`、无照片能力用 `none`，非该宏体系不传 `--permission-handler`。去掉 `--apply` 是只读复查；缺文件/无效语法会报错，不能伪造空文件。部分 Flutter 模板省略源版本键，迁移也可能移除它，须在迁移后重新检查源文件；源补齐成功与真实 Pods/构建/运行结果分开，仍核验有效宏和 App/App.framework 产物，不宣称所有旧工程已自动修复。

最终 `aduit/intro.md` 的 `## Description` 会依据项目实际功能充分展开，覆盖定位与受众、各主模块、典型使用过程、实际媒体能力（如有）、可回访成果、进入与清除流程和数据边界；遵守生成器选定的文案结构及最多 4,000 字符限制。生成后重新读取并核对覆盖，避免只留下几句短文或功能清单；仅在 `All URL` 保留隐私政策、用户协议、Support 三个具体项目名 HTTP URL；移除重复的独立 URL 栏目及其他多余网址，生成阶段立即将用户提供的项目名称写入这三个 URL，文件名和大小写保持不变；文档中的 `【项目名称】` 只作为搜索定位示例，其他事实字段仅允许按第 12.1 节统一科普展示标签；具体项目名 URL 不可访问时仍保留具体 URL并显示错误，不删改文件名。详细写作与验收见第 12.1、11.1 节，审核备注仍单独按其格式生成。

## 最终交付目录

运行验收是硬门槛：首次安装真实 App 后复用同一 Bundle ID、配置和现有 iPhone Simulator，不为每页、用例、截图或精修轮次创建测试 App、测试工程、测试 runner/host、临时 package 或 IPA。App 功能必须通过 Simulator 上真实点击、滑动、输入、返回、截图、录屏和原生日志观察；资料包 `flutter_check/` 只检查工作流、脚本和安装器，不能证明 App 已运行。无变更直接冷启动，必要变更增量构建并覆盖同一安装，最终仍验证最新完整构建。构建/安装/调试串行、输出目录复用，结束本任务多余调试、录屏及日志进程；精确清理失效副本，只保留当前产物、最多一份必要回滚产物和必需证据，不清用户数据或全局缓存，不删减 UI。详见第 0.9.1、11.1 节，结果写入项目已有 `.codex-work/quality.md`。

目标工程中的 `aduit/` 必须严格保持（由最终生成的 `AppListing/` 改名/整理而来，不执行公开部署）。改名完成后立即在其根目录新建 `imgs/` 文件夹，创建时为空。工程、材料、最终图片/依赖及 iOS 权限校验和修复复验结束后，最后自主截取五个体现核心功能或操作成果的不同 App 画面放入其中。五张均须为原始竖屏 1206×2622 PNG，复用现有 iPhone 和最终调试安装，逐张检查尺寸、解码、内容差异和无占位；不裁切/缩放/补边凑尺寸。最终 imgs/ 恰好五张，无 `.gitkeep`、隐藏文件或其他产物，记录/旧图留 `.codex-work/`，报告提供五张链接。完整规则见第 12.5 节；原有 `site/img/logo.png` 保持原位置：

```text
lib/welcome.dart  # Actual Flutter Welcome page; routed at /welcome
aduit/
├── intro.md
├── welcome.html  # Standalone delivery only; never loaded or bundled
├── imgs/  # 最后截取的五张项目画面，均为原始 1206×2622 PNG
│   ├── 01_<short_id>.png
│   ├── 02_<short_id>.png
│   ├── 03_<short_id>.png
│   ├── 04_<short_id>.png
│   └── 05_<short_id>.png
├── site/
│   ├── PrivacyPolicy.html
│   ├── Terms&Conditions.html
│   ├── Support.html
│   └── img/
│       └── logo.png
└── review/
    └── remarks.md
```

## 4.3/5.6 工程审核风险门槛

工作流会在工程阶段建立 `.codex-work/differentiation-brief.md`，明确目标用户问题、现有替代做法、主题领域模型、专属核心动作、任务顺序、首个有用结果和可回访成果。每个项目必须在真实数据、路由、交互规则和结果状态中体现这些差异；只换名称、Logo、配色、渐变、图片、字体、文案、卡片样式或底部导航外壳不能证明差异化，也不能批量生成地区/品牌/主题克隆。

发布前会使用唯一 Bundle ID 核对产品身份，并扫描隐藏审核模式、远程换功能、虚假账号/计费/服务/权限、伪造测试记录、评价诱导、评分奖励、搜索/榜单/引荐/安装量操纵，以及崩溃、白屏、占位图、死链接、错误权限、数据丢失和核心流程失败。App Store 元数据、截图、About、Intro、Support 和 Remarks 只能写已确认事实，且必须互相一致。专项结果写入 `.codex-work/app-review-risk.md`；关键项失败会记录为 `Release readiness: Blocked`，不会因为其他材料已生成而报告为可上架。外部网络或素材失败仍按现有回退继续独立任务。

免责与版权说明合并到原法律页。最终 `aduit/site/` 只保留三个协议 HTML 和 `img/logo.png`；站点目录只保留三个协议页面与 `img/logo.png`，不生成或保留首页。Logo 配色、草稿清理等只做有记录的必要定点修正；保存原副本/哈希，在 Dart 运行 Welcome 与 HTML 交付文件制作和清理后复核其余内容字节一致。`aduit/` 顶层仅 `intro.md`、`welcome.html`、`imgs/`（最终五张截图）、`site/`、`review/`，review 仅 remarks.md。Welcome 运行时唯一使用 `lib/welcome.dart`；`aduit/welcome.html` 保留为独立交付文件，不删除、不加载、不注册、不桥接、不复制或打包到 App，仍内联全部内容与 Base64 图片并严格小于 262,144 字节。HTML 只做独立离线验收，不能作为第二个 App Welcome 或运行证据。五张最终项目截图只放 `aduit/imgs/`，过程证据/备份/额外产物只放 `.codex-work/`。Remarks 全英文、最多 4,000 字符、七章分点、设置按顺序编号、仅指定 iPhone 记录和已确认事实，无 WebView/WebKit/内部模块描述。清理旧 AppListing、首页 HTML、aduit/html 和根目录旧 welcome/enter HTML，保留三个协议页与三个 URL。
