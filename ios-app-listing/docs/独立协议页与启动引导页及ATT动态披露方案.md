# 独立协议页、启动引导页与 ATT 动态披露方案

日期：2026-10-13

状态：待确认；本轮仅分析并新增本文档，不修改生成器、模板、校验器或现有预览页面。

## 1. 需求理解与范围

本次需求包含三个相关改动：

1. 去除生成页面间的 Tab / 顶部导航 / 底部导航，让 `PrivacyPolicy.html`、`Terms&Conditions.html`、`Support.html` 分别成为可直接打开的独立页面。
2. 将 `index.html` 从当前的产品概览站点首页改为当前应用的启动引导页。第一批提供两个模板，均支持 3–5 张产品介绍卡片、自动轮播、可点击分页圆点和进入应用按钮。
3. 隐私协议中的 ATT、追踪、分析、广告描述必须根据当前项目证据决定，不再无条件输出通用章节。

本轮不修改具体应用的 Swift / Flutter 启动流程，不新增 App 内入口，不部署页面。确认后先改造本 skill 的生成流程；宿主 App 的 WebView 桥接和启动展示由具体项目单独接入。

当前提供的是 skill 仓库，而非某个待上架 App 的源码。因此本文能确认生成流程的现状，不能据此判断某个具体 App 是否实际追踪用户。

## 2. 当前项目分析

### 2.1 生成流程

当前基本链路为：

```text
inspect_app.py
  → inspect_flutter_app.py / inspect_swift_app.py
  → inspect_common.py 中的共享能力与隐私分析
  → classify_app_listing.py + 分类校验
  → generate_app_listing.py 生成文案和渲染 payload
  → render_app_listing.py 输出四个 HTML
  → 本地校验
  → 可选 About 部署与已有 URL 替换
```

主要依据已阅读的 `SKILL.md`、`references/output-contract.md`、`references/privacy-ai-rules.md` 及上述脚本。此次方案继续遵守能力有证据、AI 披露有条件、账号文案有条件、输出文件名固定等既有约束。

### 2.2 页面为何存在联动导航

当前 HTML 已分别是完整文档，并不是同一个 HTML 内的 Tab 面板；问题是渲染器会统一添加跨页面导航。

| 位置 | 当前行为 | 改造方向 |
| --- | --- | --- |
| `scripts/render_app_listing.py:1873`，`base_links()` | 固定生成 Overview / Support / Privacy / Terms 四个链接 | 移除生成页的跨文件导航入口 |
| `scripts/render_app_listing.py:2227`，`footer_note()` | 提示用户使用相互关联的页面 | 改为本页相关说明，或省略无必要说明 |
| `render_top_nav()` / `render_footer_nav()` | 按模板决定导航位于顶部或底部 | 品牌头部、版权页脚与导航解耦 |
| `render_*_shell()` | 五种 shell 都接入上述公共结构 | 保留协议排版，移除导航占位和空白 |
| `build_pages()` | index、privacy、terms、support 共用同一模板体系 | index 改走独立引导页渲染分支 |

不能只隐藏导航 CSS，也不能只修改一个模板：否则其余模板仍会输出链接、辅助文案或多余空间。

协议内的 `On This Page` 目录属于本页锚点，不是跨 HTML 的 Tab 联动，可保留。邮箱、必要的第三方服务说明链接也不属于这次删除范围。默认不再添加用于切换四个生成文件的链接；若以后需要法务交叉引用，应另行明确用途。

### 2.3 现有模板与输出约定

`assets/site-render/templates-manifest.json` 当前有 15 个模板，混合了 shell、导航位置、导航样式、正文样式等配置。`tests/test_render_app_listing.py` 还明确断言了跨页面链接、导航位置和 15 个模板。

固定输出保持不变：

```text
AppListing/
  Intro.md
  site/
    index.html
    img/
      logo.png
    PrivacyPolicy.html
    Terms&Conditions.html
    Support.html
```

不能将额外 CSS、JavaScript、模板配置、截图或测试报告写入 AppListing 成品目录。`site/img/logo.png` 仍满足既有输出契约，但新的 index 不通过这个相对路径加载资源；需要显示 logo 时嵌入其 data URL。

## 3. 总体设计

### 3.1 协议页面与引导页面分别管理

建议不把两个引导模板追加到现有 15 个协议模板池中，以免随机抽到旧概览页或把轮播布局用于长篇协议。

- 协议页：保留现有 15 种正文排版与品牌配色能力，统一去掉跨文件导航和失效的导航配置。
- 引导页：新增独立模板清单，例如 `assets/site-render/onboarding-templates-manifest.json`，第一批仅注册两个轮播模板。
- 渲染入口：`build_pages()` 单独渲染 index；其余三页仍复用协议 / 支持页布局。
- 一致性：不同页面共享应用名称、品牌色、事实来源，但不再要求使用同一页面骨架。
- 清理范围：同步清理“Switch between…”、“Use the linked pages…”等依赖旧站点导航的文案，包括 payload 中实际用于页面的相关字段。

所有页面保留独立的 doctype、`html lang="en"`、head、title 和内联样式。支持页也可独立阅读，不依赖先打开 index。

### 3.2 引导内容根据项目生成

建议为 payload 增加一个明确的 `onboarding` 对象，以下字段为拟议结构，不是当前已有接口：

```json
{
  "onboarding": {
    "template_id": "onboarding-cards",
    "layout": "carousel",
    "app_name": "Example App",
    "tagline": "A short, evidence-based product introduction.",
    "cta_label": "Continue",
    "autoplay_interval_ms": 5000,
    "cards": [
      {
        "title": "Discover Your Space",
        "body": "A concise introduction grounded in the actual product.",
        "visual": "discover"
      }
    ]
  }
}
```

上例仅演示字段形状；正式 carousel 必须校验为 3–5 张卡片。

内容生成规则：

1. 输入来自 inspect、已校验 classification、`theme_hint` 和 agent 编写的 authoring JSON。
2. 第一张介绍产品定位，中间卡片介绍已证实的主要能力，最后一张介绍有证据的使用流程或价值；不要求每一张都对应不同功能。
3. 简单应用不足三个独立功能时，可将同一真实功能拆成“用途 / 操作 / 结果”三个介绍步骤，不能为凑卡片编造聊天、AI、购买、同步或离线能力。
4. 有 AI Preview 的应用将真实 Preview 流程放入一张卡片，保持已有专门披露要求；无可声明 AI 的应用不得引入 AI 文案。
5. 不把 `Category`、`UGC`、`Chat`、IAP 编码、能力分数等内部字段放进可见文案。
6. 全部可见文案使用英文，包括按钮、分页辅助标签、暂停 / 播放按钮、错误提示。若项目只有非英文名称，使用经确认的英文品牌名或 authoring 覆盖值，不擅自虚构英文品牌。
7. 建议每张卡片标题不超过约 40 个英文字符，正文不超过约 160 个字符，并进行浏览器实测；字符预算不能代替真实布局验收。
8. 内容不可信或缺失时校验失败并说明原因，不输出通用功能宣传填充页。

模板选择优先级建议为：显式指定 > 根据产品形态选择候选模板 > 稳定 seed 选择。现有 `--template-id` 继续指协议模板；新增引导模板选择项，避免更改原参数含义。具体新增参数名以实现时的最小兼容方案为准。

## 4. 第一批两个引导模板

### 模板 A：`onboarding-cards` — 居中卡片式

- 顶部：应用名称、简短定位，可选嵌入式 logo。
- 中间：单张活动卡片，包含内联视觉元素、标题和短说明。
- 底部：可点击分页圆点、轻量播放控制、`Continue` 按钮。
- 手机以纵向布局为主；桌面仍居中展示，设置合理最大宽度。
- 适用于工具、效率、教育等以流程说明为主的产品。

### 模板 B：`onboarding-spotlight` — 品牌聚焦式

- 手机：品牌标题区 + 视觉聚焦卡片 + 简短说明 + 圆点和按钮。
- 桌面：品牌介绍与活动卡片形成双栏，控制整体高度，按钮保持清晰可见。
- 使用与模板 A 不同的版式、背景、卡片层次和视觉风格，不只是换一套颜色。
- 适用于社区、生活方式、图片体验等更强调产品氛围的应用；内容仍取自项目事实。

两个模板均仅在活动卡片上展示完整内容，自动轮播并提供圆点切换。视觉使用 CSS 或内联 SVG，不使用外链字体、图标库、CDN、远程图片，也不制造未经证实的产品截图。

## 5. 页面技术要求

### 5.1 单文件与英文

- HTML、CSS、JavaScript 全部写入 `index.html`。
- 不使用外链 stylesheet、外部 script、远程字体、相对路径图片或运行时 fetch。
- logo 如需显示，使用生成时读取并嵌入的 data URL；背景和图形优先 CSS / 内联 SVG。
- 所有文本输出进行 HTML 转义；配置注入 JavaScript 时使用安全 JSON 序列化，不能直接拼接未经处理的文本。
- 无 JavaScript 时至少展示第一张卡片和说明；完整轮播、Continue 行为以 JavaScript 启用为验收条件。

### 5.2 手机、桌面与安全区

index 必须包含：

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
```

布局原则：

- 顶部 padding 使用基础间距加 `env(safe-area-inset-top, 0px)`。
- 底部按钮容器 padding 使用基础间距加 `env(safe-area-inset-bottom, 0px)`；左右安全区也可一并处理。
- 使用 `box-sizing: border-box`，确保安全区计入布局尺寸，不将按钮定位到屏幕边缘之外。
- 使用 grid / flex、`minmax(0, 1fr)`、受约束的视觉尺寸和合理最大宽度，避免绝对定位正文造成重叠。
- 视口高度使用 `svh` / `dvh` 渐进增强，并提供回退；短屏减少装饰高度、卡片间距和非必要留白。
- 不通过全页 `overflow: hidden`、固定正文高度或 line-clamp 掩盖内容溢出。
- 在指定四种尺寸、正常字体和约定文案预算下，以首屏完整展示为目标；极长名称、放大字体等超出条件时允许自然纵向滚动，优先保证内容完整且可操作。
- 协议正文较长，独立协议页正常滚动，不受引导页“一屏”目标限制。

### 5.3 轮播行为

- 默认每 5 秒切换到下一张，最后一张之后回到第一张；生成配置限制在合理区间。
- 点击圆点立即切换，圆点活动状态随之更新，并重新安排下一次切换，避免点击后马上再次跳转。
- 圆点使用真实 button，提供英文可访问名称及当前页状态，支持键盘操作。
- 非活动卡片不接收焦点，不覆盖当前卡片或按钮；自动切换不抢焦点。
- 桌面悬停、轮播内部获得键盘焦点以及页面进入后台时暂停；恢复时不补播后台期间错过的切换。
- 提供轻量 `Pause` / `Play` 控制；开启 `prefers-reduced-motion: reduce` 时默认关闭自动轮播，圆点仍可使用。
- 确保只有一个有效计时器，多次点击圆点、暂停 / 恢复不会叠加计时器。

自动轮播是默认体验；暂停机制用于避免影响用户阅读和可访问性，并非删除自动轮播要求。

### 5.4 Continue 调用必须保持原样

两个模板均使用同一个逻辑，严格保留用户指定的分支与返回行为：

```javascript
function continueToApp() {
  if (window.AppBridge && typeof window.AppBridge.postMessage === 'function') {
    window.AppBridge.postMessage('continue');
    return;
  }
  window.location.href = 'go://continue';
}
```

实现限制：

- 通过按钮的点击事件调用上述函数，不增加确认弹窗或跳转中间页。
- 不改成 `window.webkit.messageHandlers`，不更改消息大小写、参数形式或 URL。
- 不添加 try/catch 后静默回退：有可调用 bridge 时，必须执行 bridge 分支后返回。
- 按钮标题和协议行为分离。第一批标题固定为 `Continue`；以后标题改成 `Get Started`、`Start Exploring` 等英文时，消息仍为 `'continue'`，回退仍为 `go://continue`。
- 普通桌面浏览器没有 App 的协议处理器时，回退不保证能打开应用；应分别验证网页调用和宿主协议接入。
- 此点击不视为 ATT 授权、隐私同意、EULA 接受或其他法务同意，不借此伪造项目中的同意机制。

## 6. 后续模板扩展

此次只实现两个 carousel 模板，但数据结构和渲染分支预留：

- `carousel`：3–5 张卡片 + 圆点 + 自动轮播 + CTA。
- `compact`：更简短的产品介绍 + CTA，不强制轮播。
- `minimal`：应用名称 + 一段说明 + CTA。

模板清单记录 layout 与所需字段；卡片数量规则仅应用于 carousel，不能写成所有 index 模板的永久限制。CTA 文案可配置，但跳转行为只有一个实现，不按模板复制不同协议。

## 7. ATT 现状与改造方案

### 7.1 当前是否写死：结论是相关通用章节写死

准确地说，当前不是一套完整的 ATT 授权披露，而是无条件生成了“追踪、分析、广告”通用章节：

- `scripts/generate_app_listing.py:4817`：在 `build_privacy_sections()` 的 `trailing_sections` 中固定加入 `Tracking, Analytics, and Advertising`。
- 正文使用“如果追踪相关权限可用，可能使用追踪、分析和广告衡量信号”的泛化表达，没有按 `privacy_signals.tracking` 或真实实现决定是否生成。
- `scripts/inspect_common.py:1359`：`privacy_signals.tracking` 当前主要由是否存在 `NSUserTrackingUsageDescription` 对应的权限键决定。
- `scripts/inspect_common.py:1361`：analytics 根据依赖名称提示判断，不能直接证明 SDK 当前确实启用或发送什么数据。
- `scripts/validate_permission_privacy.py:17`：tracking 的检查接受 tracking / analytics / advertising 等任一宽泛关键词；有 tracking 信号时要求出现关键词，但没有相应的反向校验来阻止无追踪证据时输出广告追踪声明。
- 当前脚本未发现针对 `ATTrackingManager`、`requestTrackingAuthorization`、IDFA 或 `PrivacyInfo.xcprivacy` 的专项追踪分析逻辑。

因此，仅移除无条件章节可以修复一部分问题，但还需要加强证据分析和校验，避免将“有权限声明”误当成“实际追踪”，或将“没有权限声明”误当成“肯定不追踪”。

### 7.2 区分 ATT、分析与广告

Apple 官方对 tracking 的定义涉及把应用中收集的用户 / 设备数据与其他公司来源的数据关联，用于定向广告或广告衡量，以及向数据经纪商共享数据等行为。[1]

建议明确区分：

1. ATT 权限声明：plist 中是否有 usage description。
2. ATT 请求流程：是否调用授权 API，是否有可达调用与状态判断。
3. 实际 tracking：SDK / 自有逻辑是否进行 Apple 定义的追踪。
4. analytics：是否有实际启用的统计处理、数据类别和用途。
5. advertising：是否实际展示广告或处理广告相关数据；不能仅凭广告模块名称决定是否属于 tracking。

普通分析并不自动等同于跨公司追踪；反过来，仅没有 IDFA 代码也不能排除其他形式追踪。第三方 SDK 的真实数据用途同样要确认。[1]

### 7.3 建议新增证据模型

建议增加共享 `tracking_signals`，Swift / Flutter 最终归一到相同格式。可包含：

| 字段 | 用途 |
| --- | --- |
| `att_declared` | 是否存在 ATT usage description |
| `att_request_detected` | 是否发现授权请求及对应可达路径 |
| `att_authorization_gate_detected` | 是否发现授权状态控制相关处理 |
| `idfa_access_detected` | 是否读取广告标识符 |
| `tracking_sdk_candidates` | SDK 候选及其项目使用证据，不直接断言实际追踪 |
| `analytics_candidates` / `analytics_active` | 分析 SDK、初始化、事件发送及启用证据 |
| `advertising_candidates` / `advertising_active` | 广告集成及实际调用证据 |
| `privacy_manifest` | 相关 manifest 的 tracking 声明、域名、收集类别等 |
| `assessment` | `confirmed_tracking` / `confirmed_non_tracking` / `unknown` |
| `evidence` / `conflicts` | 文件位置、匹配依据以及相互矛盾的声明 |

注意：`confirmed_non_tracking` 不能只由“没搜到 tracking 关键词”推导。纯静态分析不足以确认时使用 `unknown`，并列出需开发者核实的具体事项。

证据来源包括：当前 App target 的 plist、第一方 Swift / Dart 调用、已启用依赖及配置、相关 `PrivacyInfo.xcprivacy`、授权门控、SDK 初始化与数据发送路径，以及有依据的开发者确认。

继续跳过项目中的 `package` / `packages` 目录，不绕过现有 skill 边界。第三方 SDK 仅通过允许范围内的依赖记录、manifest、第一方调用及官方说明核实；无法核实时显式保留不确定状态。

任何 authoring 覆盖值都不能无依据地覆盖明确的追踪证据。静态代码中的授权检查也不能被当作已验证运行时合规。

### 7.4 隐私协议条件生成决策

| 项目证据 | 页面输出 | 生成 / 发布处理 |
| --- | --- | --- |
| 没有 ATT 声明、没有追踪候选、没有分析 / 广告启用证据 | 不添加 ATT / 追踪 / 分析 / 广告模板章节；仍如实披露其他数据处理 | 不自动追加“我们绝不追踪 / 不收集任何数据”保证 |
| 仅存在 ATT usage description，未发现请求或实际使用证据 | 不按 usage description 虚构广告用途；输出诊断 | 作为待核实项，确认是残留配置还是未识别实现后再发布 |
| 仅确认非追踪型分析 | 独立 Analytics 章节，写明实际数据、用途、服务方 | 不写成 ATT 广告追踪；非追踪结论需有依据 |
| 确认广告功能，但 tracking 未确定 | 只按已证实事实描述广告服务 | 核实 SDK 数据用途，不自动归类为追踪或非追踪 |
| 确认实际 tracking，且有授权控制证据 | 条件生成 ATT / tracking 章节，描述数据、用途、接收方和授权选择 | 仍要求声明与 App 实现、manifest、商店隐私回答一致 |
| 确认实际 tracking，但授权门控缺失或证据矛盾 | 不靠“only with your permission”模板替项目补合规承诺 | 阻止自动发布，先修实现或确认行为 |
| 存在 SDK 候选、远程行为未知或 manifest / 代码冲突 | 不输出未经确认的肯定或否定结论 | 输出具体诊断，待核实后完成最终文案 |

ATT 披露在事实成立时应说明：涉及哪些数据、为什么追踪、谁接收数据、何时请求系统授权、拒绝或撤销后的行为，以及在 Settings 中管理选择的方式。具体拒绝后的功能行为必须来自项目，不能默认承诺不影响所有功能。

Apple 的 ATT 系统授权不能由网页按钮或网页中的通用同意替代；隐私文案也不能修复实际实现中的授权缺口。[1]

### 7.5 校验改造

- 有明确 tracking 证据时，不再以出现 `analytics` 一个单词作为 ATT 披露通过条件。
- 无追踪证据时，检查是否错误插入固定广告追踪章节；检查范围限于隐私语义，避免误伤健身进度 tracking 等产品术语。
- 有追踪候选但结论 unknown、授权缺口或证据冲突时，输出可定位问题并阻止未经确认的自动部署。
- analytics、advertising、ATT 分别校验，不混用同一关键词列表。
- 检查数据类别、用途和服务方与证据一致；“先授权后追踪”等承诺不能凭通用模板通过。
- 根据条件章节的实际组合统一顺序编号，避免删掉固定 tracking 章节后留下编号跳跃；不要借此重写无关法务正文。
- 更新当前只检测“缺少追踪关键词”的测试，增加错误披露和不确定证据用例。

## 8. 验收与测试计划

以下为确认后实施的验收计划，本轮没有运行布局、轮播或按钮测试。

### 8.1 自动化与浏览器验收分工

- Python 单元测试覆盖 payload、模板注册、输出结构、权限分析与条件章节。
- 浏览器自动化用于测量真实布局、检查轮播行为、截图和无外部资源依赖；优先采用本地可用工具，必要依赖仅用于开发测试，不进入生成页。
- 浏览器测试提取可见 DOM 文本，不把内联脚本里的配置键、CSS 类名当成用户可见英文内容。
- Playwright WebKit 等桌面引擎只能辅助验证，不能替代 iPhone WKWebView 的真实安全区与宿主桥接验收。
- 截图 / 报告写到仓库测试输出或临时目录，不写进固定 AppListing 成品。

### 8.2 四种视口布局

两个模板都覆盖以下四个尺寸，共至少 8 组基础布局：

| 尺寸 | 重点 |
| --- | --- |
| 390 × 667 | 紧凑短屏，完整卡片、圆点、播放控制与 Continue 不被裁切 |
| 390 × 844 | 较高手机屏幕，安全区内按钮可见、内容不松散失衡 |
| 1024 × 768 | 桌面 / 平板横向布局，双栏不挤压卡片文字 |
| 1440 × 900 | 桌面最大宽度、视觉比例和按钮位置 |

每组检查第一张、切换中间状态与最后一张，覆盖 3 / 4 / 5 张卡片、较长应用名和最长允许文案。基础条件下检查：

- 无横向滚动。
- 关键区块 bounding box 在视口内，按钮、圆点和播放控制不重叠。
- 卡片标题、正文完整呈现；不能仅测外框而漏掉内部文字溢出。
- 活动卡片之外的元素不拦截按钮点击。
- 首屏包含完整可操作内容，不依赖滚动才能点击 Continue。

另做安全区模拟和实际 iPhone 检查：模拟非零顶部 / 底部 inset、动态视口高度和字体放大。模拟值只用于测试，生成页仍直接读取系统 `env()`。真实刘海 / Dynamic Island 效果须在 iPhone 或对应模拟器的 WKWebView 核实，不能仅凭 390 像素宽度宣布通过。

### 8.3 轮播验收

- 自动前进、末张回到首张、圆点状态一致。
- 点击每个圆点切换正确，随后计时器按预期工作。
- 多次点击圆点和暂停 / 恢复不重复注册或加速轮播。
- 后台暂停、前台恢复、悬停 / 焦点暂停有效。
- Pause / Play 与 reduced-motion 行为符合约定。
- 控件键盘可操作，自动切换不抢焦点。

### 8.4 Continue 分支验收

| 条件 | 期望 |
| --- | --- |
| bridge 存在且 postMessage 是函数 | 只发送一次字符串 `continue`，不设置回退 URL |
| bridge 不存在 | 设置 `window.location.href` 为 `go://continue` |
| bridge 存在但 postMessage 不是函数 | 同样执行 `go://continue` 回退 |
| bridge 函数抛错 | 不增加与指定代码不同的自动回退行为 |
| 后续更换英文按钮标题 | 消息和 URL 不变 |

浏览器里用注入 bridge 验证真实按钮事件；回退逻辑同时用受控 JavaScript 环境记录 location 赋值，避免把浏览器“无自定义协议处理器”提示误判为网页失败。具体 App 接入后，再核实 bridge 注册或 `go://` 拦截确实继续进入原生流程。

### 8.5 页面独立性与 ATT 回归

- 所有 15 个协议模板生成的三页均无用于互相切换的页面导航，也无失效导航文案。
- 将 index 单独复制到临时目录、断网打开，仍可渲染和轮播；不请求图片、字体、CSS、JS 等外部资源。
- 四个 HTML 分别直接打开都能完整展示自身内容；协议内部锚点和邮件链接仍可用。
- Swift / Flutter 两条链路覆盖：无 ATT、仅 plist 声明、仅分析、仅广告候选、确认追踪、缺失授权门控、manifest 冲突等情况。
- 回归现有输出契约、账号文案、无 AI、AI / 人脸数据、UGC、IAP、Support 和产品声明校验。
- 不运行真实部署作为测试，不回写具体应用源代码，不修改 `package` / `packages`。

## 9. 预计修改位置与实施顺序

| 文件 / 目录 | 预计改动 |
| --- | --- |
| `SKILL.md` | 更新 index 角色、模板选择、事实驱动卡片、安全区、桥接和 ATT 规则 |
| `references/output-contract.md` | 将共享页面骨架要求改为共享品牌；定义独立页和引导页契约 |
| `references/privacy-ai-rules.md` | 保留 AI Preview 专门模块要求，明确可由专门引导卡片满足，不降低隐私披露要求 |
| `assets/site-render/templates-manifest.json` | 保留协议模板，移除不再生效的导航配置 |
| `assets/site-render/onboarding-templates-manifest.json`（新增） | 注册两个引导模板并预留 layout 与 CTA 扩展 |
| `scripts/render_app_listing.py` | 去除跨页面导航；独立引导页渲染、内联 CSS / JS、安全区和 Continue |
| `scripts/generate_app_listing.py` | 生成 onboarding payload、配置选择和 logo 嵌入数据；ATT 条件文案与校验接入 |
| `scripts/inspect_common.py` | 共享 tracking / analytics / advertising 证据模型 |
| `scripts/inspect_flutter_app.py`、`scripts/inspect_swift_app.py` | 收集两种技术栈对应的调用、配置和 manifest 证据 |
| `scripts/validate_permission_privacy.py` | ATT 语义覆盖、错误披露和不确定证据校验 |
| `scripts/validate_onboarding_output.py`（建议新增） | 单文件、语言、卡片、桥接与模板契约的静态检查 |
| `tests/` | 更新依赖旧导航的测试，新增引导页和 ATT 用例；补充浏览器验收入口 |
| `template_previews/` | 确认后重生成协议预览，并提供两个引导模板预览；预览索引仅用于开发浏览 |
| `docs/` 中相关使用说明 | 同步已变化的流程，不扩大为无关文档重写 |

实施顺序建议：

1. 先更新契约和模板分层，保持产物路径与 URL 逻辑不变。
2. 移除所有协议页跨文件导航和配套提示，更新旧测试。
3. 加入两个引导模板、项目事实驱动的卡片 payload 与严格 Continue 函数。
4. 加入 ATT / 分析 / 广告证据分层和条件生成，处理诊断与发布阻断。
5. 完成 Python 回归、四尺寸浏览器布局 / 轮播 / 按钮验收，生成预览与验收记录。

## 10. 确认时重点

建议按以下默认理解确认，不需要现在决定后续极简模板样式：

- 协议和支持页取消页面间导航，保留本页目录和必要业务链接。
- index 首批两个模板均为 3–5 张卡片轮播；以后新增 compact / minimal，不强制所有模板轮播。
- 第一批按钮显示 `Continue`；后续只扩展英文显示文案，桥接行为始终不变。
- 保留既有输出路径与 15 个协议正文模板，不将引导模板混入原随机池。
- ATT 文案按证据生成；缺乏确认或存在冲突时先核实，不用模板假设替代事实。
- 本次不默认修改 App 启动入口、桥接原生代码或实际发布。

## 11. 官方参考

以下页面用于设计依据，不是生成 HTML 的外部资源依赖；实现时应再次核实与目标项目 / SDK 相关的最新规则。

- [1] Apple — User Privacy and Data Use：`https://developer.apple.com/app-store/user-privacy-and-data-use/`。用于区分 tracking、ATT、SDK 用途和系统授权要求。
- [2] W3C WAI — Carousel Tutorial / Animations：`https://www.w3.org/WAI/tutorials/carousels/animations/`。用于自动轮播的暂停、悬停与键盘焦点处理。

最终隐私政策应与实际 App 行为、SDK 配置、隐私 manifest 和 App Store 隐私回答一致；本方案不承诺仅凭生成文案即可保证审核通过。

## 12. 全量动态条款补充审计

本节补充对隐私协议和用户协议的完整审计结论。原则是：**项目没有的能力、数据、供应商、年龄政策、购买类型和运营主体信息，不应通过默认 fallback 写入页面。**

### 12.1 当前存在的主要问题

下列内容目前仍可能由非目标应用的 fallback 产生，确认实施时必须拆成独立证据条件：

| 当前代码位置 | 当前默认或过宽表述 | 风险 | 改造要求 |
| --- | --- | --- | --- |
| `scripts/generate_app_listing.py:4570` | 非社区应用默认写入 photo editing、saved notes、optional purchases | 工具、天气、阅读等应用被误写成照片产品 | 按实际编辑、笔记、购买能力分别生成 |
| `scripts/generate_app_listing.py:4581` | 默认收集 saved preferences、saved edit notes、media uploads、purchase records、support requests | 未确认的数据类别被硬塞 | 每个数据类别单独绑定采集证据 |
| `scripts/generate_app_listing.py:4605` | 默认写入 photo editing、saved notes、photo exports、optional purchases | 将产品用途和数据用途混在一起推断 | 使用产品事实矩阵驱动 |
| `scripts/generate_app_listing.py:4716` | 相机 / 相册权限后推断 editing、saving、export 或 profile publishing | 权限不等于功能 | 分开判断拍摄、导入、上传、编辑、导出 |
| `scripts/generate_app_listing.py:4736` | microphone 默认生成 Audio Processing 及非生物识别承诺 | 未区分录音、识别、本地处理、远程发送 | 增加 audio_recording、speech_recognition、remote_audio_processing |
| `scripts/generate_app_listing.py:4747` | location 默认写 nearby places、地点确认、位置分享 | 定位权限不等于地图或位置发布 | 按地图、附近、位置选择和分享证据生成 |
| `scripts/generate_app_listing.py:4823` | 默认列出 hosting、support tools、payment processors、map providers 等 | 虚构第三方服务商类别 | 只输出有依赖、host、配置或代码证据的类别 |
| `scripts/generate_app_listing.py:4840` | 默认写 service history、disputes、fraud / abuse investigation | 夸大留存和风控能力 | 按真实数据流、风控和社区能力生成 |
| `scripts/generate_app_listing.py:4856` | 所有项目默认 `not directed to children` | 年龄定位是项目事实，不应自动断言 | 增加 `children_targeted`，unknown 时不作相反保证 |
| `scripts/generate_app_listing.py:4848` | 默认允许在 App 内更新 profile | 未确认资料编辑入口 | 按 profile_edit / privacy_controls 证据生成 |
| `scripts/generate_app_listing.py:4817` | 无条件 Tracking / Analytics / Advertising | ATT 和广告追踪被硬塞 | 按第 7 节的 tracking 证据模型条件生成 |
| `scripts/generate_app_listing.py:4958` | 非社区应用默认是 personal photo-editing / repeat-use | 产品类型被误判 | 使用 category、archetype 和 capability 生成使用范围 |
| `scripts/generate_app_listing.py:4971` | UGC 应用自动要求 18 岁 | 年龄政策未经确认 | 年龄限制必须是输入事实或人工确认 |
| `scripts/generate_app_listing.py:4979` | 无账号应用仍写 protecting access methods | 不适用于纯本地或匿名工具 | 区分 credential、local session、anonymous use |
| `scripts/generate_app_listing.py:4987` | 默认写 editing、saving、export、purchase、support 授权 | 版权授权范围超出真实功能 | 按本地处理、上传、保存、发布、购买分别生成 |
| `scripts/generate_app_listing.py:5001` | 非 UGC 应用默认使用 Saved Photos, Notes, User Materials | 普通应用可能完全没有这些内容 | 按实际用户数据类型选择章节名称和内容 |
| `scripts/generate_app_listing.py:5018` | IAP 统一按 virtual goods / consumable / restore 生成 | 订阅和非消耗型解锁被误写 | 识别 subscription、consumable、non-consumable 和 restore evidence |
| `scripts/generate_app_listing.py:5035` | AI 通用条款总是混合图片、人脸、法律、医疗等限制 | 普通文本 AI 被套用人脸条款 | 按 AI workflow 类型拆分限制 |
| `scripts/generate_app_listing.py:5071` | translate 只要命中就生成统一 Translation Accuracy | 未区分文本、图片、语音、OCR | 按 translation_text / translation_image / translation_voice 生成 |
| `scripts/generate_app_listing.py:5090` | availability scope 可能包含项目没有的 tools、purchases、support | 服务范围不准确 | 只列已确认的可用功能 |
| `scripts/generate_app_listing.py:5097` | 默认写“运营主体所在地法律” | 没有主体和司法辖区证据 | unknown 时要求人工补充，不伪造法律事实 |
| `scripts/generate_app_listing.py:5103` | Contact 默认写 reports、moderation、purchases、access restrictions | 联系事项超过产品实际范围 | 按 UGC、IAP、账号和安全能力动态列出 |

### 12.2 不应被误删的基础条款

动态化不等于把隐私协议和用户协议变成空壳。以下内容可以保留，但必须使用最小、不虚构产品能力的版本：

- Privacy：政策适用范围、实际收集的数据、实际用途、实际共享对象、留存 / 删除方式、用户可行使的权利、变更和联系方式。
- Terms：接受条款、合法使用、知识产权、服务可用性、责任限制、条款变更和联系方式。
- 如果项目真的存在社区、聊天、购买、AI、翻译、定位、媒体权限或账号体系，再追加对应专门章节。
- 法律上需要但项目资料缺失的字段（运营主体、年龄政策、留存期限、供应商合同关系）应标记为待确认并阻止发布，而不是用泛化句子冒充已确认事实。

### 12.3 统一产品事实矩阵

建议在 inspect 结果经过归一化后生成 `product_facts`，Privacy 和 Terms 共同使用，不再各自用 fallback 推断：

```json
{
  "product_facts": {
    "credential_auth": false,
    "local_session": false,
    "anonymous_use": true,
    "community_ugc": false,
    "messaging": false,
    "profile_view": false,
    "profile_edit": false,
    "photo_capture": false,
    "photo_import": false,
    "photo_upload": false,
    "photo_editing": false,
    "photo_export": false,
    "audio_recording": false,
    "speech_recognition": false,
    "remote_audio_processing": false,
    "location_features": false,
    "translation_text": false,
    "translation_image": false,
    "translation_voice": false,
    "ai": false,
    "ai_image_preview": false,
    "iap": false,
    "subscription": false,
    "consumable_iap": false,
    "non_consumable_iap": false,
    "analytics": false,
    "tracking": false,
    "children_targeted": "unknown",
    "data_retention": "unknown",
    "operator_jurisdiction": "unknown"
  },
  "evidence": {},
  "unknowns": []
}
```

字段原则：

- `true`：有代码、配置、依赖、manifest、界面或明确 authoring 事实支持。
- `false`：有足够检查范围且没有相应实现证据；不是简单“搜索不到”就强行判定 false。
- `unknown`：静态检查不足、证据冲突或需要业务确认；不能自动生成肯定性法律声明。
- 每个 true / false / unknown 都应保留 evidence，至少包含来源文件、匹配类型和置信度。
- authoring JSON 可以补充产品事实，但不能覆盖明确的代码、权限或 manifest 冲突；关键冲突应阻止发布。

### 12.4 Privacy 生成规则

Privacy 章节以数据流为最小单位生成：

1. `Information We Collect` 只列实际采集的数据类别，不以“非社区应用”作为照片、笔记、购买或上传的默认分支。
2. `How We Use Information` 只列对应功能用途；防欺诈、审核、法律义务、服务改进分别有证据或经确认后才出现。
3. 权限章节使用“权限 → 用户动作 → 数据处理 → 保存 / 发送位置”的映射，权限本身不能证明产品功能。
4. 第三方服务商按实际 provider / host / SDK 类别输出；无法确认的 provider 不得自动写入。
5. 留存章节按数据类别拆分。没有具体期限时只能使用真实的 active-request 或本地保存事实；不能虚构“24 小时审核”或长期 service history。
6. 儿童条款由 `children_targeted` 驱动：`targeted`、`not_targeted`、`unknown` 三种状态不能互相替代。
7. 权利和选择只描述项目真的提供的设置、删除、导出、资料修改或邮箱申请渠道。
8. ATT、分析、广告、AI、翻译、社区和账号章节继续按各自专门 evidence gate 控制。

### 12.5 Terms 生成规则

Terms 章节也按产品事实动态组合：

- 服务定义只列真实模块，不默认加入 photo editing、purchases、community 或 support processes。
- 使用规则按产品类型生成，不把所有应用写成个人照片编辑工具。
- 账号章节仅在 credential auth 存在时生成；local session 和 anonymous use 使用不同的访问说明。
- UGC、聊天、举报、屏蔽、审核、内容许可只在对应能力存在时生成。
- 年龄限制必须来自项目配置、商店年龄定位或人工确认；不得因有 UGC 自动写 18+。
- IAP 条款按订阅、消耗型、非消耗型和实际恢复流程区分，不把全部购买称为 virtual goods。
- AI 限制按 workflow 生成；人脸 / 生物特征限制仅用于有人脸图像或对应敏感视觉流程的证据场景。
- 翻译免责声明按文本、图片、语音等具体类型生成。
- 运营主体、司法辖区、退款和取消规则缺失时生成诊断并阻止发布，不能用泛化内容替代。
- 联系章节只列项目实际支持的报告、购买、账号、隐私或安全渠道。

### 12.6 发布阻断条件

以下问题不应继续自动部署：

- 页面声称项目没有的功能、数据类型、权限用途或第三方服务商。
- `unknown` / 冲突事实被渲染成确定性法律声明。
- 购买类型与 Terms 文案不一致。
- 追踪、AI、人脸、儿童、UGC、账号等高风险事实缺少实现或业务确认。
- 运营主体、联系邮箱、司法辖区等必要法务信息缺失或互相矛盾。

阻断信息应指出：文件、事实字段、生成章节和待确认问题；不应仅返回“validation failed”。

### 12.7 测试补充

新增测试矩阵至少覆盖：

- 纯工具 / 天气 / 阅读 / 教育项目：不得出现照片、笔记、购买、社区或地图条款。
- 只有相机：不得出现照片导入、保存到 Photos、发布或编辑条款。
- 只有定位：不得自动出现附近地点和位置分享。
- 只有 microphone：区分录音、本地识别和远程语音处理。
- UGC 无年龄配置：不得默认写 18 岁，应该阻断或要求确认。
- IAP 分别覆盖订阅、消耗型和非消耗型。
- AI 文本、AI 翻译、AI 图片预览分别检查不同限制组合。
- 无 provider 证据：不得列出 hosting、payment、map、moderation 等供应商类别。
- unknown / conflict：生成明确诊断并阻止发布。

## 13. 更新后的确认重点

确认实施时，默认范围应扩大为：

1. 实现独立协议页和两个启动引导模板。
2. 实现 ATT 动态披露。
3. 同时清理 Privacy 和 Terms 中上述所有无证据 fallback，建立共享 `product_facts`。
4. 将未知和冲突事实纳入校验与发布阻断，而不是静默生成泛化条款。
5. 更新现有测试，确保“项目没有的条款不会出现”。

## 14. 实施记录（2026-10-13）

- 已实现独立协议页、两个单文件启动引导模板、Continue 桥接回退逻辑，以及基于代码 / manifest / StoreKit 和人工确认事实的 Privacy、Terms 生成与部署门槛。
- 已增加启动页与动态法律输出校验；未知或冲突的关键法律事实允许生成供审阅，但会阻止 About 部署。
- 已将 AI 收件方、处理位置、保留和删除文案改为读取确认事实；不再默认声称使用第三方提供商或固定保留期限。
- 已通过 Python 编译检查及 214 项单元测试，`git diff --check` 通过。
- 按用户要求，本轮未执行 390×667、390×844、1024×768、1440×900 的布局 / 轮播验证，也未验证真实 WKWebView 的安全区和宿主桥接运行时行为。
