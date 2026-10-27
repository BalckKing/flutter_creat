## 12. App Store、法律与 About 材料

思维导图整体确认并开始实现后，所有公开材料从实际实现生成，并且 App 内公开文案保持英语：

**发布范围固定为 iOS iPhone。** AppListing、About、Support、协议、商店文案、预览和截图均只面向 iPhone；不出现其他设备版本、兼容性声明、商店分发选项或下载入口。最终核对构建产物与商店配置时，只有 iPhone 可用；若后台无法验证这一点，明确记为未验证，不将其描述为已限制完成。

- `Privacy Policy`：只说明实际功能的数据处理；若选用摄像机、相册选择/读取或麦克风，再说明对应具体用途、按实际 API 的授权时机及拒绝/撤销后的行为，并描述实际照片/录音的处理、保存、保留、删除、临时文件、备份边界与安全措施。三项均无时不添加相关使用或授权声明；按第 8.5 节准确说明 `Clear Data` 二次确认后清除 App 自有媒体、记录、偏好和缓存，成功后进入 Initialization，失败可重试，系统相册原件、App 外导出文件、现存备份和系统权限不由此删除或重置。说明实际的第三方 SDK、WebView 请求、诊断/网络元数据、接收方和 实际数据处理情况。App 无需账号、不要求邮箱输入或身份认证数据、不上传用户媒体；若真实支持渠道接收用户主动发送的信息，按第 0.3 节准确披露，不将无账号扩大为未经核验的“所有数据绝不离开设备”。包含真实开发者身份、联系渠道、生效日期、政策变更及适用的隐私权利说明，不声称保存个人协议同意记录。
- `Terms of Use`：完整说明功能范围、内容来源、许可、可用性、用户责任和禁止滥用，以及实际涉及的用户内容权利、保存与删除、重要内容备份、服务限制和联系方式；仅实际提供拍摄/录音时加入对应权利与使用条款；不得将这些条款变为隐蔽免责。准确描述每次启动进入 Welcome 并点击 `Continue` 即可进入主流程（仅改名前开发预览可显示 `Enter`），`Clear Data` 须二次确认、无法通过 App 撤销，清理成功后进入 Initialization；不加入不存在的退出、登录、会员、上传或社交功能，也不宣称按钮代表勾选协议、授予系统权限。
- `Disclaimer` 章节：在 `Terms&Conditions.html` 或 `PrivacyPolicy.html` 中根据主题提供仅供参考的说明，以及适当的专业意见排除条款。
- `Content & Copyright Notice` 章节：在现有法律页中用简洁、真实的内容使用与权利说明及更正/删除联系渠道表达，不默认逐项列举图片/视频供应商、作者、来源链接或素材许可。按第 10.1.1 节仅加入实际许可要求的最小必要声明；没有公开署名义务的素材只留内部核验记录。若存在用户本地拍摄/导入/录音，则与随包内容区分；不声称拥有用户媒体，不把私有媒体列入公开清单，也不作虚假的全部原创或自有版权声明。
- About Home 与 Support：使用清晰、友好的产品介绍和支持说明，通过同一 WebView 页面展示，不把 About Home 误写成 App 主首页。

开发期根据实际实现持续维护应用介绍、About、支持页和协议正文，四个 HTML 页面始终保持完整、自然、可独立阅读的成品文案，不显示 `Draft` 等页面状态标签、待补提示或作者备注。最终生成的 `site/index.html` 与其余三个页面在 AppListing 改名为 `aduit/` 后保持原样；将当前引导页写入工程根目录 `welcome.html`；当前 App 只将根目录文件作为自包含引导页接入。缺失的开发者、联系、司法辖区等事实不得猜测，也不得以填空语写入页面；仅在内部生成摘要中记录具体缺口，并标记公开法律审阅未完成。页面生成、接入与本地校验不因此卡住；这不等于宣称法律材料已可公开发布。全流程不依赖域名、公开部署或线上访问。App 功能、UI、资源和第 11.9 节质量复核完成后，依次使用安装器从远程指定分支同步的完整 `ios-app-listing` 目录生成 AppListing 与 About 页面、核对 Logo 配色并整理为 `aduit/`，按本节生成并接入根目录 Welcome 引导页，再更新 Entry/Settings 的 WebView URL，最后按第 12.2 节依据已核实事实生成英文 Review Remarks。质量复核的完成含义是已执行适用检查、修复可修复问题并记录外部失败；图库许可或正式 Logo 仍为 `Blocked` 时，不得把相应质量项写成通过，但不能阻断已独立的本地材料步骤。远程来源缺失、来源不符、同步失败或生成器失败时，先记录远程失败并自动使用 `/Applications/config/ios-app-listing`；本机后备也不可用时，按随包生成契约继续完成 AppListing、About、`aduit/` 整理、引导页与 Review Remarks，并把对应阶段准确标记为 `Blocked`/`Not verified`，不得等待用户或中断后续步骤。均由智能体自主完成，不新增询问关卡；不要求或查询域名，不公开部署。

### 12.1 AppListing 与本地 About 页面生成、改名为 aduit 并清理

#### 最终页面不得包含草稿或开发分发说明

每次生成或重新生成后、改名为 `aduit/` 后、替换首页引导页后以及最终交付前，检查四个 HTML 页面。正文、标题、页眉/页脚、横幅、描述元数据、图片替代文本、无障碍标签和脚本实际渲染的内容都不得出现草稿、开发版本、待配置资料或发布前待完善提示。特别禁止 `Publication details — draft`、`This edition is a development distribution`、`A verified operator identity, contact channel, and public policy address have not been configured`、`These details must be completed before public release`、`No contact address or public availability is implied by this page` 及大小写、标点、措辞不同的同义说明；也不将这些内容改成 `Preview`、`Unfinished` 等标签继续显示。

发现时按完整语义区块移除相应标题、段落、提示框和关联状态标记，不能只删 `draft` 一词后留下“资料未配置”的说明，不能用 CSS 隐藏、折叠、降低透明度或转移到另一公开页面/无障碍文案。若区块还包含必要的真实法律事实，仅保留经核实的成品表述；修复相邻排版、目录锚点和空白区域，维持页面完整可读。真实身份、支持渠道或其他法定资料缺失只记录到项目 `.codex-work/`，不得编造姓名、邮箱、正式域名、上线状态或把缺失事实写成已核实。原四个 `All URL` 值、固定注册表与链接的大小写和原文不因清理而更改。

使用运行器自带检查器执行 `python3 <runner-skill-root>/scripts/validate_about_copy.py --site-dir <project-root>/aduit/site`。`runner-skill-root` 指当前执行的 `flutter-engine-runner` 的 `SKILL.md` 所在目录，不是 `ios-app-listing` 的目录；资料包直接使用时为包内 `flutter-engine-runner/`，安装后为已安装运行器根目录。该检查器只读四页，不会访问 URL 或修改文件；修正文案后重跑直至无命中。它不依赖远程包是否提供 `validate_site_publication_ready.py`。静态检查后仍须本地渲染四页并查看脚本生成内容及适用外观/视口，确认未通过样式、动态插入或实体编码漏出同义提示；不得只检查首页或把静态通过当作法律资料已核实。检查结果和必要缺口放内部记录，不能生成公开校验报告或状态提示。

AppListing/About 生成、改名和最终精修时，按第 10.1.1 节移除生成器自动加入的不必要图片/视频来源列表、供应商标识、下载链接及 Credits 入口；不将内部素材清单批量转成公开页面或 Review Remarks。Terms 中的内容来源与许可说明保持概括、真实，不能据此生成逐项图库清单。保留实际许可强制要求的声明、软件必要许可通知及真实隐私/外部服务披露，四页白名单与协议 URL 原文不变。

四个自有 HTML 页面同步第 6.5 节的背景规则：浅色外观使用 Logo 暖色渐变整体底色，不能回退纯白；正文采用稳定高对比表面，深色外观保持现有规则。包括最终替换的 Welcome 引导 HTML，继续遵守自包含、图片内嵌及体积限制。

#### About 最终配色与小体积 Logo

- **以选中成品重新着色**：读取最终 `assets/logo.png` 与 `.codex-work/brand-palette.md`，将有来源的主/辅/强调色及衍生值映射为四页各自内联 CSS 变量。实际修改背景渐变、品牌页头、重点卡片、主按钮/分页点、链接、选中/焦点态和边框，不只替换 Logo 图片或声明一个主色。检查模板所有样式块、内联值、媒体查询、伪元素及脚本，移除仍生效的无关默认色与覆盖；深色保持可读。首次生成后对四页复验；根目录 `welcome.html` 另按引导页专项生成和验收，不能覆盖 `aduit/site/index.html`；至少品牌背景与一个强调区有清晰可见的不同渐变，法律正文保持稳定高对比。每页留本地渲染截图与 CSS 实际值的对应证据，不联网探测协议 URL。
- **主图不降质，网页只用小副本**：`assets/logo.png` 保持正式 1024×1024 RGB PNG，取色与 AppIcon 继续用它；`aduit/site/img/logo.png` 改为由该源图派生、按网页最大实际显示尺寸约 2 倍像素生成的小图，通常 128–256 像素即可，不直接把完整大图塞进四页。以清晰度与配色合格为前提，比较适用的缩放、PNG 压缩、无损优化及调色板量化结果，选择实际字节最少且无明显失真/色带的一版；图片以字节体积和解码开销衡量，不虚构“最低码率”设置。小 Logo 目标 8–20 KiB、尽量不超过 24 KiB；记录实际尺寸/字节、源与派生哈希、压缩方式和显示对照，不能只改扩展名或直接沿用未优化的大 PNG。预算内无法满足时记录具体限制并采用已验证的最小可用副本，不让压缩失败阻断页面生成，也不宣称大小达标。
- **引导页内嵌同样优化**：根目录 `welcome.html` 若显示 Logo，将小副本的实际字节以匹配 MIME 的 Base64 内嵌，不引用 `assets/`、项目路径或远程图片；Base64 后的真实字节同样计入整个 HTML 严格小于 262,144 字节的预算。`aduit/site/` 的其他四页按生成器交付内容保留，并可引用唯一的 `img/logo.png`。不为不同尺寸增添站点白名单外图片，未显示 Logo 的页面无需人为再加一个。
- **图片不阻塞页面**：为 Logo 预留宽高/比例，使用适用的异步解码；首屏图正常加载，下方图片按需处理。正文、导航和 `Continue` 不等待 Logo 的 `load`、`decode()`、图片预加载队列或 `window.onload` 才出现/启用；业务必需准备条件仍按原规则处理。禁止同步大 Base64 转换、主线程逐像素压缩或无限图片重试，图片优化在构建前完成。失败时显示清楚的文本品牌/可恢复状态，继续显示内容与可操作按钮，不让整页白屏或永远显示加载层；缺图项仍不算图片验收通过。
- **实际检查加载边界**：本地测试四页正常、图片延迟、解码失败和断网状态；确认文字/导航/轮播可用、Continue 两种调用不受 Logo 影响，检查 WebView 首帧/内存与无未处理错误。压缩派生文件与主 Logo 的哈希通常不同，只验证可追溯派生关系、主题色和视觉身份一致，不要求两者字节相等。来源、压缩表与截图只放 `.codex-work/`，不改 URL、文件白名单或把候选图放入站点。

四页、引导卡片、Intro 和 Remarks 同步执行第 6.6 节的文案编辑：各页按真实用途写不同内容，删除套话和重复段落；必要的法律事实、固定操作名称和审核七项结构保持准确。不能为减轻“AI 风格”虚构故事、事实或把每页改写成同一段营销介绍。

**改名后立即创建空目录**：完成 `AppListing/` 到项目根目录 `aduit/` 的改名/整理后，立即新建 `aduit/imgs/`，再执行引导页替换、URL 回接和 Review Remarks。它是与 `site/`、`review/` 同级的独立空文件夹，交付时必须存在且内部为空（包含隐藏项）；不放图片、占位文件、`.gitkeep` 或 `.DS_Store`，也不替代原有 `site/img/`。重跑时若该目录已有内容，先可恢复地归档到 `.codex-work/` 再保持为空；后续清理与白名单验收必须保留此目录。

#### Intro 与 Remarks 的科普标签统一

最终 `aduit/intro.md` 和 `aduit/review/remarks.md` 中，类别、分类、标签或产品定位标签若为“教育”“教育类”“Education”“Educational”或“教育 (Education)”等同义形式，统一改为“科普”；两份交付文档保持英语，因此实际写入 `Popular Science`。例如 Intro 的 `## Category` 正文写 `Popular Science`，Remarks 的基本信息写 `Category: Popular Science`，正文中重复出现的同一定位标签也须一致，不保留中英混合旧标签。其他已确认的类别原样保留，不把所有项目强制归为科普，也不因此虚构科学主题、课程、资质或功能。

生成器原始输出先按其现有契约校验；改名整理为 `aduit/` 后、生成引导页或 Remarks 前，执行本标签规范化，最终交付时重新核对两份实际文件。已有文档同样处理，先将原文件备份到 `.codex-work/`，仅修改作为分类/定位标签使用的相应值，不对全文做无差别替换。应用名称、真实服务名称、普通功能叙述、四个原始 URL（包括包含 Education 的域名、路径或参数）及其他事实保持不变。本规则只调整两份文档的展示用标签，不修改远程技能源码、生成器分类枚举或 App Store Connect 实际提交类别；不把 `Popular Science` 当作官方分类枚举传入接口。生成阶段与定制整理后的校验分别记录，后续重新生成仍须应用该规则，不因原始契约要求教育标签而恢复旧文案。

#### intro.md 的详尽项目描述（仅保留四个完整 URL，地址原文不变）

最终 `aduit/intro.md` 的 `## Description` 必须是针对当前实际 App 撰写的完整英文产品介绍，使未参与开发的人仅阅读该段就能理解应用面向谁、解决什么问题、各项主要功能怎样使用、操作会得到什么结果，以及内容如何保存和再次使用。不能只交付一句概述、三五条功能名称、生成器默认短文或“界面精美、简单易用”等泛泛营销话术。除本节科普标签规范化及下述四个 URL 整理步骤明确移除的重复 URL 栏目外，保留其他标题、顺序和事实字段；产品介绍扩写集中在现有 `## Description` 区域内，使用自然英文纯文本，按选定文案结构组织段落或项目符号，不加入 HTML、额外 Markdown 标题、内部技术说明或另一份介绍文件。

**先核对事实，再组织长文**：读取最终第一方源码、已注册页面和实际可达入口、内容/示例数据、设置及权限配置，并结合已有运行证据核对。已确认方案用于查漏，最终实现决定可描述的能力；未实现的规划不进入介绍。每个主要模块至少写清“处理什么内容 → 用户可以做什么 → 得到什么结果/为什么有用”，使用 App 实际英文页面和按钮名称，不逐项罗列代码目录或组件。需要数量时使用可核实的真实数量；不编造活跃用户、内容规模、效果、专业资质、设备测试、在线服务或性能数据。

按以下叙事顺序覆盖适用内容；这些是 Description 内的写作要点，不是在 Intro 中新增顶级栏目：

1. **具体定位与核心用途**：前 255 字符内说明实际应用名、主题、目标用户和主要用途；后续解释用户在什么场景遇到什么问题，以及本 App 如何帮助完成任务。开头清楚直接，不用空泛口号占据篇幅。
2. **完整主模块与内容结构**：覆盖每个已实现的主要目的地/核心模块及重要二级功能，说明实际分类、内容单位、关键字段或步骤，以及它们如何串联成主题任务；搜索、筛选、对比、计算、播放等仅描述实际存在的能力。不能只展开首页而漏掉其他主模块，也不能把相同功能换词重复介绍。
3. **典型使用过程与真实结果**：结合项目已有的至少三个不同用户结果的任务，以具体、自然的操作叙述说明从进入模块、选择/输入内容、执行动作，到查看结果、保存及回访的过程；相近步骤可以合并，但读者应知道从哪里开始、做什么、最后获得什么。示例必须可按当前功能完成，不虚构用户经历或反馈。
4. **摄像机、相册与麦克风（仅实际存在时）**：只解释已选能力在主题中的用途、真实入口、操作、结果及再次打开；未选能力不写成卖点或补建。三项全无时不写媒体段落。权限根据实际 API 描述；系统选择器不等同于整库授权，拒绝后可用路径按真实行为说明，不暗示所有硬件均已验证。
5. **成果管理与连续使用价值**：说明实际可保存的主题成果、用户可以怎样继续、编辑或删除，以及再次使用时能解决什么问题。清楚区分随包示例和用户自己创建的记录；没有编辑、导出、同步、收藏或分享就不写这些能力，不把私有媒体描述为公开内容。
6. **进入与清除流程**：用简洁但准确的文字说明每次启动在 Welcome 点击 `Continue` 进入，且无需账号、邮箱或登录；Settings 中 `Clear Data` 经二次确认后清除哪些 App 自有内容，真实成功后显示 Initialization 并以 `Entry` 返回主流程。不能把初始化页写成每次启动的欢迎页，不能写已取消的 Exit/登出功能。
7. **体验与可用性**：描述实际提供的 `System`、`Light`、`Dark`、有用的主题视觉/结果表达和可用性支持，说明它们怎样帮助阅读或操作，不堆砌“高级、丰富、极致”等形容词。离线使用、VoiceOver、大字号和减少动态等只按实际支持范围撰写；不能从几张截图推导全功能已验证。
8. **数据、权限与服务边界**：用普通用户能理解的英语准确说明实际存在的记录及媒体（如有）的处理和保存、真实需要的权限请求时机、删除范围、哪些操作需要网络，以及真实存在的账号/计费/服务限制。未使用的能力不写成卖点，不把“没有账号/不上传媒体”扩张成未经证实的“任何数据都不会离开手机”。必要事实披露保留，不暴露自有 package、模块、实现细节或多余素材来源清单。
9. **可信的独特价值与回访理由**：结合当前项目的标志性动作、内容组织规则和可回访成果，具体解释它给目标用户带来什么便利；结尾回扣真实使用场景，不使用无依据的“唯一、最好、领先”或虚构竞品比较。

**篇幅与生成方式**：Description 沿用 AppListing/商店字段的最多 4,000 字符限制，空格和换行计入；该上限不代表整份 `intro.md` 或 Review Remarks 的共同预算。已确认事实充足且选定文案结构允许时，以约 3,500–3,900 个英文字符作为充分展开的参考目标；优先保证功能覆盖、自然可读与事实准确，不靠重复或空话凑字数。生成前按当前生成器规定的选择流程确定文案样式，`description_style_label` 必须与其实际选定结果一致，正文遵守该样式的句数、段落或项目符号结构；不得擅自覆盖选择结果或强制使用 `longform`。`description` 由当前智能体依据已核实功能自行撰写后传给生成器，不能把自动短文当作已完成详细写作。不为篇幅编造能力、机械截断正文或改变其他字段。若可用样式或事实范围限制展开，只在内部记录实际覆盖与缺口，不新增询问、不停止后续材料生成。

**生成后强制复核，URL 完整保护**：在 AppListing 改名为 `aduit/` 后、使用该介绍生成引导卡片或 Review Remarks 之前，重新打开实际 `aduit/intro.md`，逐项核对上述内容是否真实落盘。先在 `.codex-work/` 保存修改前副本，并单独记录生成器 `All URL` 中四个完整原始地址。介绍有遗漏或过于简略时，仅精修 `## Description` 标题之后、下一个既有 `##` 标题之前的正文；然后执行下述 URL 整理及本节科普标签规范化。描述、URL 整理与标签规范化分别核验，不重新运行生成器覆盖已精修内容，不修改远程技能源码，不因文案编辑重写 App URL 注册表。证据与备份只放 `.codex-work/`，不向 `aduit/` 增加文件，不新增用户确认关卡。

**最终 Intro 仅保留四个完整 URL**：网址统一集中到既有 `## All URL` 块，按生成器原标签和原顺序仅保留首页、隐私政策、用户协议、Support 四项，每项一个完整原始地址。移除单独的 `## Support URL` 与 `## Terms of Service URL` 重复栏目及其内容，去除介绍其他位置的重复链接、多余网址、示例网址和无关外部链接，不留下空 URL 标题或另一个网址清单。只清理多余出现位置，不因暂不可访问、占位域名、格式看起来异常或请求失败而删除这四项中的任何一项；不以“无效 URL”为由重写地址、不访问真实目标。四个保留值的协议、域名、大小写、路径、文件名、参数及顺序、百分号编码、片段和斜杠全部原样保留，不补全、不替换、不截短。

**分别核验生成阶段与最终交付**：生成器原始输出先按其可用契约校验；最终 `aduit/intro.md` 在详细描述、四 URL 整理与科普标签规范化后，检查全文完整 URL 的出现次数恰好为 4、都位于 `All URL` 且各出现一次，标签齐全、顺序未变，四值逐字符等于修改前保存的原始值。除 `Description` 正文、两个重复 URL 栏目和其他多余网址的删除、本节科普标签规范化外，其余事实字段与原文保持不变；已满足四 URL 与科普标签规则的文件再次只精修描述时，Description 外应为零差异。远程生成器若要求六处 URL 或两个独立 URL 栏目，那是其原始输出契约；最终交付以本节四 URL 要求为准，记录定制整理和分阶段校验结果，不回填重复栏目，也不将修改后的文件谎报为通过旧格式校验。缺少原始地址时保留实际缺口与已有文件、继续独立任务，不猜测或拼接新地址。Description 仍单独验收英文、纯文本、字符数、功能覆盖与事实一致性，不能把详细介绍压缩成审核备注。

#### 生成 URL 的原文保留与大小写保护

- 生成完成后，先在 `.codex-work/` 保存生成器介绍文件中四个 `All URL` 原始值，作为改名、复制和接入的比对基准；然后将它们原封不动保留在 `aduit/intro.md` 并复制到 App 固定 URL 注册表。暂不可访问、占位域名、格式异常或加载失败都不是改写理由，不探测真实地址，不等待正式域名，继续完成后续任务。
- 完整 URL 严格区分大小写并逐字符保留：协议、域名、路径、目录名、文件名、扩展名、查询参数的名称/值/顺序、片段、斜杠及百分号编码的原始写法均不得改变。不得使用 `toLowerCase()`、`toUpperCase()`、slug 化、自动格式化或 URI 解析后重新序列化来重写值；不得根据页面显示标题、Dart 标识或本地目录重新拼接地址。源码、JSON 或 HTML 必需的转义可以使用，但解码后交给 WebView 的字符串必须与原始值完全相同。
- 本地将 `AppListing/` 改为 `aduit/`、将 `Intro.md` 改为 `intro.md`，只涉及本地文件整理，绝不能对 `All URL` 做全局替换或大小写转换。协议 HTML 保持 `PrivacyPolicy.html`、`Terms&Conditions.html`、`Support.html` 的原始大小写与标点，不改成全小写文件名；页面内链接也按实际文件名保持大小写。
- 验收链为“生成器原始值 → `aduit/intro.md` → App 固定注册表 → Initialization/Settings 点击时交给 WebView 的实际字符串”。使用区分大小写的精确相等比较，不允许先转小写再比对；发现任一处变化，修复该复制/传递环节并复验，不反过来修改原始值以使错误通过。按第 11.3 节用无网络 stub/fake 核验，证据仅放 `.codex-work/`，不增加 `aduit/` 交付文件。
- 当前生成流程不替换域名。用户之后明确提供正式域名并要求替换时，只替换授权的域名部分；协议及其余路径、文件名、查询参数、片段和编码原样保留，不随新域名重新生成 URL。仅修复大小写不能证明服务器配置或可达性已经通过。

例如，原始路径为 `/BrandA/PrivacyPolicy.html` 时，不得改为 `/branda/privacypolicy.html`；`Terms&Conditions.html` 不得改为 `terms&conditions.html`。此例只说明大小写规则，不是当前项目的网址。


**错误隔离与继续执行**：不要用一条 `&&` 命令链把素材检查、Listing 生成、目录整理与 Remarks 串成全有或全无。分别运行并读取生成器 JSON、退出码与实际文件；`local_generation_complete` 仅表示介绍和页面已经生成，`media_review_errors`、`failures` 与正式发布就绪状态分别记录。退出码非零时先有限修复可修复的本地问题，保留已有产物；仅 Logo 缺失、照片许可、图片运行验证或外部网络失败不能跳过后续改名与 Remarks。正常交付仍必须满足原白名单；完全没有可解码品牌图时，允许先保留空的 `site/img/` 并移除缺图引用，记录 `logo.png` 缺失和目录契约未通过，继续生成 `aduit/intro.md`、四页正文与 `aduit/review/remarks.md`，不创建假图片或宣称白名单通过。开发期图片可以使用已有有效 AppIcon，或显式记录来源的 `.codex-work/development-brand.png`；不能仅凭它被命名为 `assets/logo.png` 就认定正式 Logo 通过。

本节在全部 App 实现、UI/资源精修、适用验证与第 11.9 节质量复核之后执行；质量复核必须实际执行并记录结果，但单项照片、许可、Logo 或运行环境外部失败可以保持 `Blocked`/`Not verified`，不把它们改写为通过，也不阻断本地材料生成；随后还须完成第 12.2 节 Review Remarks。仅对本节涉及的页面、随包同步与文件变更补充必要核验，不另开产品设计或审批。开发期仍提前把四个固定 HTML 页面（About Home、Privacy Policy、Terms & Conditions、Support）及其中合并的法律章节直接放到 `aduit/site/`，应用介绍放到 `aduit/intro.md`，供离线 WebView 使用；即使实际事实尚有缺口，也只在内部记录里标明，不把页面降格为带草稿水印、待填字段或未完成说明的预览稿。这些准备不等于提前执行最终 AppListing 生成、改名或目录清理。最终阶段仅在 AppListing 已改名为 `aduit/` 后以引导页替换生成的 About Home；不得提前替换、另建文件或因此推迟 URL 回接与 Review Remarks。

固定收尾路径：先尝试验证安装器同步的完整远程 `ios-app-listing` checkout（Git 来源、`feature/1.2.1-A1` 分支和当前 revision）；远程不可用或不完整时，自动切换到 `/Applications/config/ios-app-listing`，两者均不可用时启用随包生成契约。使用当前可用来源的技能、脚本、引用和资源，以 `--no-deploy-about --no-sync-project-listing-urls` 本地生成最终 AppListing、`description` 与对应 About 页面 → 核对并修正 About 配色 → 将生成的 `AppListing/` 改名/整理为 `aduit/` → 立即新建空的 `aduit/imgs/` → 按第 12.1 节清理与核验 `site/` → **将当前引导页写入工程根目录 `welcome.html`，只替换并接入根目录引导页，完成引导页验收** → 将 `aduit/intro.md` 的四个 `All URL` 原样保存到固定 URL 注册表，协议通用文案只显示在清除成功后的 Initialization 页底部，Welcome 与引导页不含协议通用文案；Settings 只接入 Privacy Policy/Terms of Use/Support 三个 WebView 入口，再做定向回归（不探测或修复 URL）→ 按第 12.2 节生成 `aduit/review/remarks.md` → 核验完整目录白名单 → 将全部其他产物移入 `.codex-work/` 并从 `aduit/` 清除 → 确认 `AppListing/` 已不存在 → 最终报告。远程、本机后备或契约来源的失败证据分别记录到 `.codex-work/`；任何来源不可用时仍继续完成独立的本地材料、目录整理、引导页与 Remarks 步骤，相关验证准确标为 `Blocked`/`Not verified`，不得读取资料包内旧副本或手写等价页面冒充技能产物。此流程不要求、查询、推测或替换域名；不调用域名查询或 About 部署接口，不创建、轮询部署任务，不做 DNS 或公开访问探测。

引导页验收时核对文案结构、内容布局和协议文案缺席；通过后才进行原始 URL 的注册及两个目标的绑定。

协议通用文案仅初始化页显示：欢迎页和引导页都不显示该文案；只在确认 Clear Data 并且清理成功后显示的 Initialization 页底部呈现。

**运行时文件边界**：`aduit/site/` 四个生成 HTML 必须原样保留；工程根目录 `welcome.html` 是唯一运行与交付引导文件。将引导页同步到工程根目录 `welcome.html` 后，Welcome 只读取根级文件或根级 asset key `welcome.html`。不得在 `lib/`、`pubspec.yaml`、本地依赖、`.dart_tool`、iOS 工程、Pods、构建目录或 App bundle 中写入或保留任何 `aduit/` 路径、目录或资源副本；最终扫描须按路径字符串和目录项双重检查。

**目录白名单验收**：最终 `aduit/` 的直接子项必须恰好是小写 `intro.md`、`imgs/`、`site/` 和 `review/`；`site/` 的直接子项必须恰好是生成器保留的 `index.html`、`PrivacyPolicy.html`、`Terms&Conditions.html`、`Support.html` 和 `img/`，`img/` 中只保留 `logo.png`；`review/` 中只保留 `remarks.md`；`imgs/` 必须为真实空目录，内部含隐藏项在内的子项数量为 0。大小写、标点和目录层级按此核对，检查包括隐藏项，不允许 `.DS_Store`、其他文件、目录或符号链接混入。`site/` 的四页保持最新生成内容；根目录 `welcome.html` 是独立生成并接入的唯一 Welcome 引导页，不是 `site/index.html` 的副本或替换；免责及版权说明合并为现有法律页中的章节。AppListing 转移后先核对 `site/`，引导页替换和 Review Remarks 写入后再核对完整白名单；文件齐全且额外项为 0 才可标记交付目录验收完成。

页面所需 CSS 和确有用途的 JavaScript 内联到站点四个 HTML 文件及根目录 `welcome.html` 中，字体采用系统字体；About 页面如需图片仅引用 `img/logo.png`，但 `welcome.html` 引导页须遵循下方的 Base64 图片内嵌要求。改写后的引导页不得依赖任何外置图片文件。在移出额外文件前先消除页面对外置 CSS、JS、字体、其他图片或旧路径的依赖，并复验章节锚点、相对链接和离线显示。不能只移动依赖文件而留下失效引用。站点四页与根目录 `welcome.html` 的职责和路径必须分别核对。已有 `aduit/html/`、报告、截图、备份及其他白名单外内容先移到项目根目录 `.codex-work/` 的独立归档位置并核对，不覆盖已有备份；不得将这些内容复制进 `site/` 或 `img/`。

1. **按来源优先级生成当前项目的 AppListing 与 About 页面**：优先完整读取安装器同步的 `Workflow resource root/ios-app-listing/SKILL.md` 及其要求的 references、scripts、assets 和 validators，并核对 Git `origin`、`feature/1.2.1-A1` 分支与当前 revision；远程 checkout 缺失、不完整或同步失败时自动读取 `/Applications/config/ios-app-listing`，本机后备也不可用时按随包生成契约继续。对当前可用来源按技能检查实际 App、分类、选定描述样式、生成与验证；不使用资料包内旧副本、旧安装或无关项目目录。`description` 必须由当前智能体根据已实现的主题、功能和最终 UI 文案撰写，再通过当前来源实际支持的 `--authoring-json` 输入；不把脚本的默认文案当作已自行撰写，不虚构账号、社区、上传或 AI 功能。固定使用 `--no-deploy-about` 与 `--no-sync-project-listing-urls`，生成并验证本地产物；不调用域名查询、About 部署接口或线上访问工具。生成前确认 `assets/logo.png` 或 AppIcon 候选是真实可解码图片；如果正式 Logo 服务只返回生成网页或正式 Logo 超时，不能把网页保存为图片，先将已有有效 iPhone 品牌图归一化为 `assets/logo.png`，或创建仅供本地产物的 `unverified` 开发期品牌源并在 `.codex-work/` 记录，Listing/About 继续生成但不得称为正式品牌通过。若无可解码品牌图，保留失败证据并按来源输出/校验结果处理；不得伪造正式品牌通过。远程、本机与契约来源均不可完整验证时，只标记相应校验为 `Blocked`/`Not verified`，仍继续生成可完成的本地材料、整理 `aduit/`、引导页和 Review Remarks。
2. **保持真实文件契约、成品状态和协议边界**：技能输出文件为 `AppListing/Intro.md`、`AppListing/site/index.html`、`AppListing/site/img/logo.png`、`AppListing/site/PrivacyPolicy.html`、`AppListing/site/Terms&Conditions.html`、`AppListing/site/Support.html`，按实际大小写与标点核对；用户所说的 `intro.md` 对应这份介绍文件，最终目标统一为小写 `aduit/intro.md`。`aduit/site/` 最终严格保留生成器的 `index.html`、`PrivacyPolicy.html`、`Terms&Conditions.html`、`Support.html` 和 `img/logo.png`；不得在 `site/` 下新增 Disclaimer、Content & Copyright Notice 或其他协议文件，若法律内容需要披露，应合并到这四个页面并保持可达链接。四页必须是完整、自然、彼此独立的成品文案；正文、标题、描述元数据、替代文本和无障碍标签不得出现 `Draft` 等页面状态标签、`WIP`、`TBD`、`TODO`、`Placeholder`、`Pending confirmation`、方括号填空项或作者/开发状态说明。真实产品功能名称以项目事实为据，不得用作页面状态说明。description、网页正文与最终截图执行第 6.6、11.4 节的英语及显示文案检查，不沿用技能模板里的技术术语、中文、框架名称或 `local`/`device`；固定文件名、机器字段和内部报告不作为页面正文展示。公开文案和法律陈述据实，联系地址不能靠推测；没有经确认的支持邮箱时不推断或生成 `support@<slug>.com`，省略对应联系区并在内部摘要标记公开法律审阅缺口。用自然英文准确描述 `Clear Data` 与隐私事实，不因关键词命中删掉必要披露。遇到校验冲突须记录对应规则与实际依据并针对性核验，不伪报所有技能校验通过，不为过词库而虚构功能或更改数据行为。
3. **About 配色与 Logo 必须一致**：站点的 `img/logo.png` 必须来自当前项目验收后的 `assets/logo.png`，核对文件来源与内容，不用技能自行选中的旧 AppIcon 或旧品牌图覆盖它。以第 2.5 节真实色块和主题/渐变映射作为依据，实际查看 About 的主题色、主按钮、链接、渐变和背景；品牌区域必须呈现协调的渐变与鲜明色彩，不沿用生成器默认的无关配色。不一致时直接替换 About 主题色及共享 CSS 令牌，再核验浅/深色表现、文字/控件对比度与全部站点页面。配色一致不要求逐像素同色，阅读表面可保留中性色。缺少正式 Logo 时按第 2.5 节在内部记录发布阻断，并继续可完成的本地整理；About 页面不加开发状态水印，不能以临时图标冒充正式配色验收。
4. **不设置域名或公开部署关卡**：生成的 URL/元数据保持技能产物原样；不得要求用户提供域名，不调用域名查询接口，不推测、替换、拼接或验证任何域名/公开主机。固定使用本地生成参数，不调用 About 部署接口、不创建或轮询部署任务、不做 DNS 或公开访问探测。记录 `AppListing generation: succeeded/failed` 与 `Delivery: Local only`；无公开 URL、域名或线上页面不阻断本地页面生成、改名和白名单核验，也不把生成的 URL 说成已上线或可访问地址。
5. **将生成目录改名为 `aduit`，明确替换旧介绍并保留审核目录**：把技能生成的 `AppListing/` 目录按可恢复方式改名/整理为项目根目录的 `aduit/`；若 `aduit/` 已存在，先把旧目录完整备份到 `.codex-work/`，并将其中既有 `review/` 目录安全暂存，避免随旧版替换而丢失，再整理新生成内容；不把新介绍追加到旧内容后。改名完成后立即按本节创建空的 `aduit/imgs/`，后续清理不得移除该目录。将 `Intro.md` 改名为小写 `aduit/intro.md`，保留 `site/` 中四个生成 HTML 页面与 `img/logo.png`，将当前引导页写入工程根目录 `welcome.html`，清理其余生成文件。将暂存的 `review/` 恢复到新 `aduit/`；若没有既有目录，则在第 12.2 节创建。既有 `remarks.md` 在替换前另存可恢复副本，其他 review 文件移至 `.codex-work/`。`aduit/` 最终只能有 `intro.md`、空的 `imgs/`、`site/` 与 `review/`；`site/` 只能有四个 HTML 页面与 `img/logo.png`，`review/` 只能有 `remarks.md`。任何 CSS、JS、字体、截图、日志、报告、备份或其他生成文件必须移入 `.codex-work/`，不能保留在 `aduit/`。CSS/JS 应内联或由页面生成流程处理，不能因此增加白名单外文件。以文件清单、必要哈希、可读性和相对引用验证无遗漏，不能只转移首页而漏掉 Logo、Support 或协议。
6. **核验改名后的 `aduit/site/` 并清理多余内容**：以改名后的 `aduit/site/` 作为后续正文维护源，按第 7.6 节核验四个固定 HTML 页面及其合并法律章节、稳定文档注册、相对引用和离线显示，不让改名产生失效链接或两份不同版本。逐项核验 `aduit/intro.md`、四个 HTML 文件和 `img/logo.png` 的存在、内容、Logo 配色与离线显示；不执行线上访问检查。将改名前生成的临时输出和开发记录移入 `.codex-work/`，不得创建或保留 `aduit/html/`。改名/核验失败时保留可恢复备份并修复，未解决时如实说明；清理失败不谎报成功、不删除唯一副本。

**改名后的品牌复验**：按第 10.4 节将当前正式 Logo 按本节压缩成网页小体积派生图放到 `aduit/site/img/logo.png`，记录源/派生哈希和视觉同一性，实际查看本地四页的 Logo/品牌封面与渐变，修正旧图片引用；同时确认 App 的桌面图标、原生启动品牌图和 Welcome/Initialization 页面未被生成器或后续构建改回旧图。站点不新增独立封面图片文件，保持原白名单。

**页面成品文案检查**：最终生成或修改四个 HTML 页面后，必须按本节运行随运行器提供的 `validate_about_copy.py` 并查看四页实际渲染。所选 `ios-app-listing` 来源另有 `scripts/validate_site_publication_ready.py` 时，再运行其支持的 `--site-dir <project-root>/aduit/site` 检查；缺失时记录该工具不可用，不等待、不伪称执行成功，继续随包检查与页面复核。修复正文、标题、描述元数据或无障碍标签中的草稿/占位内容，并确认页面不是空壳。若缺少真实联系或其他法定事实，只在内部摘要标记公开法律审阅未完成；继续本地生成和接入，不在页面中显示待补字段，也不谎称法律材料已完成。

**AppListing 改名后：根目录引导页生成、接入与验收**：仅在最终 `AppListing/` 已按白名单改名/整理为 `aduit/` 后执行，并且必须在 URL 回接和 Review Remarks 之前完成。保留 `aduit/site/index.html` 及站点其他三个 HTML 的最新生成内容，不修改、不覆盖、不移动站点文件；保留 `aduit/site/index.html` 作为四个站点页面之一，并将当前引导页写入工程根目录 `welcome.html`，完全替换根目录文件为 Welcome 引导页。不得在 `aduit/` 再创建 `index.html`，不得在 `site/` 新增引导页副本。依据当前项目的源码、配置、实际页面与 `aduit/intro.md` 生成 3–5 张真实介绍卡片；全部可见文字使用英语，准确介绍项目实际用途和功能，不固定主题、不虚构能力，CSS 主题色、渐变与整体视觉风格须匹配当前 App 及 Logo 色板。页面必须是小于 256 KiB（262,144 字节）的单一自包含 HTML 文件：全部 HTML、CSS、JavaScript 在该文件中，使用系统字体，不加载外部脚本、样式、字体或其他运行时资源；装饰优先用 CSS 绘制，若采用 SVG 图片素材也须编码为 Base64 data URI，现有 Terms/Privacy 链接属于用户主动导航而非资源依赖。每张需在引导页显示的图片（包括 Logo 与卡片配图）均须编码为 Base64 data URI，直接内嵌在同一个工程根目录 `welcome.html` 中；浏览器/WebView 渲染时从 data URI 解码并显示。`site/img/logo.png` 仍按交付白名单保留，但引导页显示 Logo 时使用其内嵌数据，不从该相对路径加载。不得让根目录 `welcome.html` 引用 Flutter assets、工程内相对图片路径、`file://` 路径或远程图片 URL，也不得通过 CSS `url()`、`srcset` 等方式绕开内嵌要求。可为页面生成压缩或缩放后的图片副本以满足体积限制，但不能覆盖原素材；包含所有 Base64 图片内容后，完整 UTF-8 HTML 文件仍须严格小于 262,144 字节，不得放宽上限。验收时逐个解码 Base64，确认图像格式、尺寸与可读性，并在无网络 WebView 中确认每张图片实际显示。

页面需设置 `viewport-fit=cover`，用 `env(safe-area-inset-top)` 与 `env(safe-area-inset-bottom)` 处理刘海/Dynamic Island 和底部安全区。一次只展示一张卡片并自动轮播，提供可点击且有可访问名称的分页圆点；支持手机与桌面，适配指定尺寸并尽量一屏展示，不得有内容重叠、控件被遮挡或文案/按钮被裁切。尊重 `prefers-reduced-motion`：减少动态时关闭自动轮播及非必要运动，分页点仍可手动切换。引导页不含协议通用文案；Welcome 不显示协议通用文案或 Terms/Privacy 页脚链接；通用文案只在 Clear Data 确认成功后出现的 Initialization 页底部显示，两个目标分别可点击。引导页验收须确认协议文案缺席、安全区和内容布局正常，不得挤压或遮挡 `Continue`。协议原始 URL 的注册及 Initialization 中两个目标的绑定在通过引导页专项验收后的 URL 回接阶段完成。

根目录引导页及站点四个 HTML 页中所有展示图片按第 6.3 节使用统一圆角；包括 Base64 内嵌 Logo、卡片配图与其他图片，图片及容器同步设置 `border-radius`，容器使用 `overflow: hidden` 实际裁剪。可以适当加入与 App 统一的主题色细边框，轮播和响应式布局中不得露出尖角、溢出或遮挡主体。样式继续内联，不引入外部资源或新增文件；圆角不通过修改原始 Logo 的 Alpha 实现。引导页在四个指定视口验收实际裁剪效果，其余协议页沿用既定不探测真实 URL 的验证边界。

将工程根目录唯一的 `welcome.html` 作为 Flutter 欢迎/引导阶段实际显示的本地随包 WebView 页面；工程根目录 `welcome.html` 是唯一运行与交付引导文件，`aduit/site/index.html` 仍是生成器保留的 About Home 页面。`lib/`、依赖树和 App bundle 只能引用/包含根级 `welcome.html`，不得出现任何 `aduit/` 路径或目录。页面使用的图片已内嵌为 Base64 data URI，因此中转或随包加载时不依赖项目内部图片资源，也不发起图片网络请求。提供 WebView 的原生 `AppBridge.postMessage` 消息通道：收到唯一消息 `continue` 时调用现有进入 App 流程；Web 页面 Continue 按钮必须调用以下函数，不增删分支或改写其行为：

```javascript
function continueToApp() {
  if (window.AppBridge && typeof window.AppBridge.postMessage === 'function') {
    window.AppBridge.postMessage('continue');
    return;
  }
  window.location.href = 'go://continue';
}
```

当 Bridge 不可用时，原生 WebView 导航代理必须截获 `go://continue` 并调用相同的现有进入流程，不向外部浏览器放行，不绕过初始化、权限提示或 App 自身状态。引导页中的 `Continue` 是该欢迎阶段唯一的继续控件，不重复显示旧入口按钮。

验收实际随包页面而非独立样稿：核对 UTF-8 文件字节数 `< 262144`、页面不存在外部资源请求、全部卡片文案与当前功能一致、仅一份 HTML 被 App 加载；在 `390×667`、`390×844`、`1024×768`、`1440×900` 分别检查安全区、完整显示、无重叠/裁切与滚动情况。实际验证自动轮播、每个分页圆点点击、系统减少动态效果、Bridge 存在时只发送一次 `continue` 且不触发回退、Bridge 缺失时精确导航到 `go://continue` 并由原生代理接续。使用不发起网络请求的 Bridge/WebView stub 核验；截图与结果写入项目 `.codex-work/`，不能写入 `aduit/`。在这些检查完成前不得开始 Review Remarks；检查失败则先修复并复验，客观受阻项据实记为 `Blocked`/`Not verified`，不得只检查 About HTML 生成器原页或宣称通过。

**About 完成后、Review Remarks 前的 Initialization 文案与协议入口回接**：在 About/AppListing 本地生成、配色核对并整理为 `aduit/` 后、生成 `remarks.md` 前执行。先读取 `aduit/intro.md` 的 `All URL` 区域，逐字复制其中四个 URL 到 App 的固定 URL 注册表，按文档名称对应绑定。将值作为原始字符串保存和传递，不以 URI 预解析/有效性检查作为复制、保存或导航前置条件。此时将以下两行协议文案接入 Clear Data 确认清理成功后出现的 Initialization 页底部，显式在 `our` 后换行，无句末句号；每次启动进入的 Welcome、Welcome HTML 引导页和原生启动页均不得显示这段文案：

```text
By continuing, you agree to our
Terms of Use and Privacy Policy
```

两行居中放在 Initialization 页底部安全区内，不截断文本；第二行的 `Terms of Use` 与 `Privacy Policy` 分别可点击，使用 All URL 中对应的原始值，`and` 为普通文本。不能只改 About HTML、字符串文件或规划说明而不更新 App 实际显示。不增加勾选或额外确认，不保存个人协议同意记录，也不将按钮等同于媒体授权；Terms 正文应与这项实际提示一致。Settings 同一页面只提供三个链接：Privacy Policy、Terms of Use、Support；工程根目录 `welcome.html` 作为唯一 Welcome 引导页；站点 `index.html` 仅作为 About Home 页面交付，不写入 Settings 且不含协议页脚。三个 Settings 入口使用 All URL 中对应的原始值，第四个 About Home URL 仍保存在固定注册表但不提供 Settings 入口。无论 URL 格式是否正常、目标是否可达，均直接复制，不校验、规范化、补全、替换或删去；WebView 加载失败时显示可读错误、返回与有限重试，不能阻断 Welcome、Settings、清除数据或其他 App 功能，也不回退到开发期本地预览页面。回归时按第 7.2 节核验 Initialization 的完整原文、显式换行、底部安全区和两个独立链接，并确认 Welcome、HTML 引导页和原生启动页均无该文案；用不发起网络请求的 WebView stub/fake 核验注册值、实际入口 URL、Settings 不含引导页、失败/返回状态和主流程，不访问或探测真实目标；完成后继续 Review Remarks，不重开总体 UI 审批。

7. **完成 AppListing 与协议入口阶段**：报告实际使用的 `ios-app-listing` 来源（远程分支、本机后备或契约来源）、可取得的分支与 revision、当前智能体撰写的 description、About 配色核验和修正结果、`AppListing/` 生成与改名/整理为 `aduit/` 的结果、站点白名单核验及额外文件移出位置，以及四个 URL 的原样接入和定向回归结果。远程、本机或生成器失败时报告对应 `Blocked`/`Not verified` 证据，但继续完成独立的本地材料、引导页、目录清理和第 12.2 节 Review Remarks；不得使用资料包内旧副本或手写页面冒充技能产物。备份放在 `.codex-work/` 并说明可恢复位置。完成所有可执行步骤后再做完整白名单核验，不在此阶段提前宣布最终交付。不询问用户意见、继续许可或交付确认。

### 12.2 App Review Remarks

在第 12.1 节完成后，为当前 Flutter App 生成审核备注，并写入 `aduit/review/remarks.md`。若目录不存在则创建；若文件已存在，先将旧版保存到 `.codex-work/` 中的可恢复位置再替换。此文件是 `aduit/` 的唯一审核备注产物，不新增其他审核材料到该目录。备注全程使用英语，字符总数不超过 4,000；使用七个编号 Markdown 标题，各章正文分点描述，不使用 `**` 粗体标记，不输出分析、推理、免责声明或中文。

**分点写作与内容边界**：基本信息每项单独一行；七个章节内按事实使用简洁的 `- ` 项目符号，每点只说明一个事实、操作或结果，设置流程使用按操作顺序排列的编号列表。实际设备、地区差异和独特价值只有一条时保留单个条目，不为凑数量扩写，不把整章合成冗长段落。`remarks.md` 全文不得出现 `WebView`、`web view`、`WKWebView`、`WebKit` 或网页容器、嵌入式网页等实现描述，覆盖基本信息、七章、括注及依赖说明；不叙述协议页面的呈现方式、URL 回接、桥接、内部路由或本地页面实现。已有备注中的相关文字同样移除。真实外部服务仍按名称、用途和实际数据处理如实说明；内部显示容器不作为外部服务列举，不把实际使用写成未使用，也不新增服务或省略必要隐私事实。实现与网址可达性检查只记内部记录，审核备注以可执行的用户操作和实际产品能力为主。

**全文设备范围仅限 iPhone**：`remarks.md` 的基本信息、七个章节、正文、括注及测试/截图说明只保留有依据的 iPhone 机型、对应 iOS 版本和实际测试范围。读取混合设备记录时先筛选 iPhone，其他设备的名称、系统版本、测试记录、兼容性说明及排除示例均不写入最终备注。修改既有备注时同样清除这些内容，混合句中只保留能独立核实的 iPhone 事实；不得把其他设备的结果改名为 iPhone 记录，也不得为补足数量编造测试。iPhone 真机与 iPhone Simulator 仍须准确区分。完成后通读全文核对设备范围，而非仅检查第 2 项；备份与清理证据只放 `.codex-work/`。

**类别标签与 Intro 一致**：按第 12.1 节的科普标签规则读取最终介绍文件；原教育类标签统一写为 `Popular Science`，基本信息使用 `Category: Popular Science`，各章出现的同一定位标签保持一致。不得从生成器原始文件回填 `Education` 或中文“教育”，也不改写其他类别、真实功能或服务名称。

先读取当前实际存在的介绍文件：AppListing 尚未规范化时为 `AppListing/Intro.md`；完成第 12.1 节转移/小写规范化后，以白名单中的 `aduit/intro.md` 为准。若输入材料写作 `aduit/Intro.md`，先核对实际大小写，不得因大小写不符漏读或另造重复文件。提取应用名称、用途、类别、功能、用户生成内容、账号、计费、权限和其他提审信息；必要时查看源码、配置、测试记录和现有审核材料核实事实。还要在内部逐字核对 App 固定协议 URL 配置与 `All URL` 四项映射，但不发起网络请求；映射和可达性状态只记录到 `.codex-work/`，不写入审核备注，也不据此宣称在线服务可用。不得把开发期占位文案当成最终事实。输出以 `# App Review Remarks` 开始，随后用普通英文标签列出 `App name`、`Purpose`、`Category`、`User-generated content`、`Account`、`Billing`、`Permissions` 和 `Other submission details`；未知值统一按缺失规则标注。之后按以下七项顺序使用清晰的 Markdown 标题：`## 1. Actual Device`、`## 2. Test Devices and Operating Systems`、`## 3. App Purpose, Intended Audience, and Problem Solved`、`## 4. Setup Steps`、`## 5. External Services`、`## 6. Regional Differences`、`## 7. Unique Value`。

1. Actual Device：写入用户已提供的实际运行设备记录 `iPhone 17 Pro Max, iOS 26.5`，不得自行添加或替换机型、系统版本、视频、账号或测试结果。此项按用户明确提供的记录填写，不得把模拟器结果称为真机结果。
2. Test Devices and Operating Systems：从有明确已完成自测记录且符合本项目 iPhone-only 范围的 iPhone 中随机抽取 2–5 台，不重复；候选不足时只报告确有记录的设备，不编造机型凑数。当前提供的合格样本为 `iPhone 15 Pro, iOS 18.6` 与 `iPhone 13, iOS 17.7.1`，故本项目应从这两台中抽样（若取 2 台则均列出），不增加其他设备记录。当前记录说明合格 iPhone 已完成启动、主要功能与权限提示自测且未发现阻塞问题；只复述记录明确覆盖的测试类别。不要照搬通用模板中的注册/登录或计费测试声明：当前产品无账号/登录功能，写 `No such feature` 且不得声称测试过此流程；计费/内购须先核对实际实现与测试记录，确无此功能才写 `No such feature`，存在时仅报告有记录的实际测试，未知时写 `Not provided; pending confirmation.`。
3. App Purpose, Intended Audience, and Problem Solved：只依据 `aduit/intro.md` 和当前实现说明产品用途、主要用户及解决的实际问题，不夸大。
4. Setup Steps：按审核人员可执行的顺序写安装/启动、点击最终引导页的 `Continue` 进入主要功能（仅改名前开发预览可用 `Enter`）、仅为实际存在且需要授权的功能列出真实入口、触发系统授权的操作和拒绝后的可用路径；系统照片选择器按实际行为说明，不添加整库请求；无受保护能力时明确无需这些权限，不编造媒体操作，随后说明`Settings` 中 `Clear Data` 的入口与二次确认及成功后显示 Initialization 页。注册/登录、验证码、邀请码或测试账号仅在实际存在时说明路径；不存在时写 `No such feature`。计费或内购步骤仅在实际存在时提供，并按审核人员可执行顺序说明；无需特殊设置时明确写 `No additional setup is required.`
5. External Services：逐项列出 App 实际使用的外部服务、平台、API、分析工具、支付服务、云服务及第三方 SDK，并说明各自用途；另以独立标签列出 `Advertising`、`AI services`、`Third-party SDKs`。每项均明确给出状态：有证据确认使用时写服务与用途，确认未使用时写 `Not used.`，未知或未提供信息时写 `Not provided; pending confirmation.`；不能把未知写成未使用。不列举协议链接、页面容器或访问状态；这些配置及核验结果只留内部记录，不据此声称存在已上线服务。只列真实外部依赖，不暴露自有 package、内部模块、目录或实现细节；仅供本地生成的 URL/占位地址不算线上服务。不得查询、要求或推断域名。
6. Regional Differences：核对功能、内容、价格、权限、可用性及审核流程的地区差异。确认无差异时必须使用精确英文句子 `All regions are the same.`；确认存在差异时逐项说明具体地区与内容；事实不足时写 `Not provided; pending confirmation.`，不能默认所有地区相同或猜测。最终备注全程英语，因此不得将该固定英文句子替换为中文。
7. Unique Value：用一句具体、可信且与当前功能一致的话概括与同类产品的差异和用户价值，避免空泛营销语。

基本信息与七项内容须全部包含。只使用源码、配置、实际测试记录或用户明确提供的已确认事实；不能编造设备、系统版本、测试、视频、账号、服务、SDK、地区支持或功能。缺失信息统一写 `Not provided; pending confirmation.`；已确认不存在的能力写 `No such feature` 或 `Not used.`。不适用的账号、注册、登录、订阅、内购和受限功能应明确说明没有对应能力及可执行路径；未知的计费状态不得擅自标为不存在。不要把 iPhone 模拟器测试写成真机测试。完成后检查全文仅为英语、字符数不超过 4,000、基本信息及七项顺序/标题准确、无 `**`、不出现 H5、B-side 或内部 package/模块信息，并与 App、实际存在且大小写正确的介绍文件及审核事实一致；不等待用户审批或补充意见。

### 12.3 App Store 隐私披露、EULA 与提交材料

1. 根据实际数据流填写 App Store Connect 隐私披露，覆盖 App 本身、第三方 SDK 与 App 功能内 WebView。纯设备端处理的照片与录音不因访问系统权限就自动属于 Apple 定义的“收集”；若其他数据离开设备，按 Apple 当前定义分别判断用途、保留、关联身份与追踪，不直接套用 `Data Not Collected`。
2. App 内必须提供隐私政策入口；最终 Entry/Settings 目标按 `aduit/intro.md` `All URL` 原样配置，不执行公开部署或可达性验证。目标地址可达性须记为未验证，不通过回归测试发送网络请求，也不自行修复地址。若正式提交仍需要公开可访问的隐私政策 URL，单独记录为未验证发布前置条件；公开链接、真实开发者身份或联系渠道缺失时保留本地产物并记录缺口，不编造信息、不要求用户提供域名，也不因此停止其他本地实现。
3. 明确采用 Apple 标准 EULA，或在确需自定义 EULA 时依据 Apple 当前最低条款完整准备并正确配置；App 内 `Terms of Use` 不自动等同于 App Store 的自定义 EULA，不能宣称四份 HTML 已覆盖所有提交协议。
4. 审核说明必须写明无需登录，并给出从最终引导页点击 `Continue` 到达主要功能的步骤；仅对实际选用的摄像机/相册/麦克风列具体入口与用途，按所需授权说明拒绝后的可用路径；三项全无时不编造入口或权限测试。另列清除本地数据的入口/二次确认/成功后显示 Initialization 的结果。截图、描述、年龄分级与二进制一致，不展示未实现能力或用户私有素材。
5. 检查最终构建的权限声明、隐私清单、SDK 要求、公开政策、协议版本、支持链接与审核说明。已知错误须修复，证据不足须明确标记；正式提交流程遵守用户已有授权与实际平台能力，不因宣称“协议完整”跳过 Apple 当前验证。

官方核对来源：开发与正式发布时重新查看适用版本并记录核对日期，不能假定本文永远覆盖后续政策变动。

- [Apple 用户隐私与数据使用](https://developer.apple.com/app-store/user-privacy-and-data-use/)
- [App Review Guidelines：2.5.14、5.1.1 与 5.1.2](https://developer.apple.com/app-store/review/guidelines/)
- [系统相册选择器与最小权限](https://developer.apple.com/documentation/photokit/selecting-photos-and-videos-in-ios)
- [App Store 隐私披露](https://developer.apple.com/app-store/app-privacy-details/)
- [隐私清单](https://developer.apple.com/documentation/bundleresources/privacy-manifest-files)
- [第三方 SDK 要求](https://developer.apple.com/support/third-party-SDK-requirements/)
- [自定义 EULA 最低条款](https://www.apple.com/legal/internet-services/itunes/dev/minterms/)

### 12.4 4.3/5.6 发布材料与身份复核

发布材料必须和当前二进制一起审计，不能把生成器输出当成事实证明。对 `App Store Connect` 元数据、截图、`aduit/intro.md`、四个站点页面、Support 和 `aduit/review/remarks.md` 执行以下检查，并将结果写入 `.codex-work/app-review-risk.md`：

- 只有一个产品身份：Bundle ID、显示名称、类别、应用图标、描述、支持信息和审核备注互相一致，不创建同一产品的地区/品牌/主题副本，也不把共享模板当成独立产品。
- 描述产品的差异来自真实目标问题、领域内容、任务路径、交互规则和用户可回访结果。只更换 Logo、颜色、字体、素材、文案或卡片外观的版本不能提交；无法证明实质差异时标记 `4.3 risk: Failed`。
- 公开材料只写已确认的开发者身份、支持渠道、服务、权限、设备测试、地区和计费事实；不编造测试账号、购买结果、用户规模、合作关系、可用地区或公开部署状态。缺失项留在内部记录，不在 About 或 Remarks 中补写推测。
- 不加入自定义评分/评论弹窗、五星引导、评价奖励、搜索词堆叠、虚假推荐、引荐或安装量操纵。需要评价时只允许 Apple 系统评价 API，且必须有真实产品需求和测试证据。
- 质量缺陷、无效链接、占位资源、错误权限、白屏、崩溃、数据损坏和未完成核心任务必须先修复；材料完成不等于发布就绪。把专项结果与 `Verified`、`Blocked`、`Not verified` 分开记录。

4.3 或 5.6 的关键项失败时，仍可继续生成本地 `aduit/` 和其他不依赖项，但最终报告必须写 `Release readiness: Blocked`，说明具体阻断和下一步；不得以“已生成材料”或“流程未中断”替代审核合规结论。
