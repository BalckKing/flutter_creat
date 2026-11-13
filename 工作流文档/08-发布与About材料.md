## 12. App Store、法律与 About 材料

思维导图整体确认并开始实现后，所有公开材料从实际实现生成，并且 App 内公开文案保持英语：

**发布范围固定为 iOS iPhone。** AppListing、About、Support、协议、商店文案、预览和截图均只面向 iPhone；不出现其他设备版本、兼容性声明、商店分发选项或下载入口。最终核对构建产物与商店配置时，只有 iPhone 可用；若后台无法验证这一点，明确记为未验证，不将其描述为已限制完成。

- `Privacy Policy`：只说明实际功能的数据处理；若选用摄像机、相册选择/读取或麦克风，再说明对应具体用途、按实际 API 的授权时机及拒绝/撤销后的行为，并描述实际照片/录音的处理、保存、保留、删除、临时文件、备份边界与安全措施。三项均无时不添加相关使用或授权声明；按第 7.7 节选定模式披露真实行为：clear 才按第 8.5 节说明 `Clear Data` 二次确认及实际清除范围；无用户数据的 exit 则说明 `Exit App` 确认后结束当前使用、保留偏好和随包内容，不能宣称删除媒体或记录。两者成功后进入 Initialization，失败可重试；系统相册原件、App 外导出文件、现存备份和系统权限均不由此删除或重置。说明实际的第三方 SDK、WebView 请求、诊断/网络元数据、接收方和 实际数据处理情况。App 无需账号、不要求邮箱输入或身份认证数据、不上传用户媒体；若真实支持渠道接收用户主动发送的信息，按第 0.3 节准确披露，不将无账号扩大为未经核验的“所有数据绝不离开设备”。包含真实开发者身份、联系渠道、生效日期、政策变更及适用的隐私权利说明，不声称保存个人协议同意记录。
- `Terms of Use`：完整说明功能范围、内容来源、许可、可用性、用户责任和禁止滥用，以及实际涉及的用户内容权利、保存与删除、重要内容备份、服务限制和联系方式；仅实际提供拍摄/录音时加入对应权利与使用条款；不得将这些条款变为隐蔽免责。准确描述每次启动进入 Welcome 并点击 `Continue` 即可进入主流程（仅改名前开发预览可显示 `Enter`），按第 7.7 节采用实际 Clear Data / Exit App 及二次确认，成功后进入 Initialization；仅 clear 说明真实删除范围与不可撤销后果，exit 说明结束当前流程且保留偏好。不加入不存在的登录、会员、上传或社交功能，也不宣称按钮代表勾选协议、授予系统权限。
- `Disclaimer` 章节：在 `Terms&Conditions.html` 或 `PrivacyPolicy.html` 中根据主题提供仅供参考的说明，以及适当的专业意见排除条款。
- `Content & Copyright Notice` 章节：在现有法律页中用简洁、真实的内容使用与权利说明及更正/删除联系渠道表达，不默认逐项列举图片/视频供应商、作者、来源链接或素材许可。按第 10.1.1 节仅加入实际许可要求的最小必要声明；没有公开署名义务的素材只留内部核验记录。若存在用户本地拍摄/导入/录音，则与随包内容区分；不声称拥有用户媒体，不把私有媒体列入公开清单，也不作虚假的全部原创或自有版权声明。
- 生成器站点首页与 Support：保留当前 `ios-app-listing` 输出的首页形态和内容职责，不强制改写成 About Home 或 App 主首页；首页仅交付、不接入 App，Support 仍通过既有协议 WebView 入口展示。

aduit 生成完成后，App 内 WebView 显示四个协议页面，不跳转到外部 App。

开发期根据实际实现维护应用介绍、About、支持页和协议正文，四个站点 HTML 保持完整英文成品文案，不含草稿/待补说明。 `aduit` 生成完成后，App 内 WebView 显示四个协议页面，不跳转到外部 App。保留四页职责与路径，四个固定文件名 `index.html`、`PrivacyPolicy.html`、`Terms&Conditions.html`、`Support.html`，四个文件名不得改动、不改大小写；协议链接统一使用可直接搜索替换的完整 HTTP 模板 `http://【项目名称】/index.html`、`http://【项目名称】/PrivacyPolicy.html`、`http://【项目名称】/Terms&Conditions.html`、`http://【项目名称】/Support.html`。质量复核后依远程指定分支 → `/Users/admin/Desktop/config/ios-app-listing` → 随包生成契约的顺序完成 AppListing/About，改名整理为 `aduit/`，立即建立空 `imgs/`，再按本节最终实现并接入 `lib/welcome.dart`，保留仅供独立交付的 `aduit/welcome.html`；随后在 App 内用 WebView 回接四个协议页面，禁止跳转外部 App，再生成 Review Remarks。正式 Logo、照片许可、外部来源或运行验证失败只记录对应 `Blocked`/`Not verified`，不得伪报通过，也不阻断独立本地材料；不询问域名、不公开部署、不探测真实 URL。缺失的身份/联系/法律事实只记 `.work/`，不猜测或写成公开待补文案；本地生成完成不等于法律审阅或发布就绪。

### 12.1 AppListing 与本地 About 页面生成、改名为 aduit 并清理

#### 生成器首页保留，不替换（硬门槛）

`AppListing/site/index.html` 生成完成后，随目录整理原位保留为 `aduit/site/index.html`。不得用另写的欢迎引导页、About Home、开发期预览页或其他模板替换、覆盖或重建它，也不能将它移走/改名后在原路径放另一份首页、跳转页或占位文件。生成器首页即使本身含卡片、轮播或 Continue，也保留其原有结构与行为，不因其外观像欢迎页而替换。该规定覆盖远程技能、本机后备与契约后备的生成路径，以及重跑、迁移、清理和最终精修阶段。

实际 App 欢迎页仍独立实现为 `lib/welcome.dart`；独立交付文件仍单独保留/生成于 `aduit/welcome.html`，不被 App 使用。 App 运行时只使用 `lib/welcome.dart`，不加载 `aduit/welcome.html`；保留 `aduit/welcome.html` 作为独立交付文件，不删除。Dart 运行 Welcome 与 HTML 交付文件的生成、修改或旧文件迁移只操作各自路径，不移动站点首页、不向 `site/index.html` 写入欢迎内容，也不把四个 `All URL` 中的首页地址改成 welcome/enter。`site/` 的其余三个 HTML、`img/` 和目录白名单照常保留。

既有 Logo 配色、小图优化、草稿区块清理、事实与必要法律文案修正仍可在原生成页面中定点完成；只能修改对应样式、图片引用或实际问题区块，保留其余正文、DOM 骨架、原脚本/交互与链接，不借此整页重写或转换成另一种页面。生成后先在 `.work/` 保存原首页副本与 SHA-256；定点修正后记录具体差异、理由和最终哈希。制作 Dart 运行 Welcome 与 HTML 交付文件、URL 回接及交付清理前后精确比较站点首页，除已记录的定点修正外必须字节一致。发现被误覆盖时，从本项目匹配本次生成版本的副本恢复并重新核验；没有可恢复副本时记录缺口并修复生成环节，不能以另写首页冒充原生成产物。

#### 最终页面不得包含草稿或开发分发说明

每次生成或重新生成后、改名为 `aduit/` 后、独立欢迎页制作后以及最终交付前，检查四个 HTML 页面。正文、标题、页眉/页脚、横幅、描述元数据、图片替代文本、无障碍标签和脚本实际渲染的内容都不得出现草稿、开发版本、待配置资料或发布前待完善提示。特别禁止 `Publication details — draft`、`This edition is a development distribution`、`A verified operator identity, contact channel, and public policy address have not been configured`、`These details must be completed before public release`、`No contact address or public availability is implied by this page` 及大小写、标点、措辞不同的同义说明；也不将这些内容改成 `Preview`、`Unfinished` 等标签继续显示。

发现时按完整语义区块移除相应标题、段落、提示框和关联状态标记，不能只删 `draft` 一词后留下“资料未配置”的说明，不能用 CSS 隐藏、折叠、降低透明度或转移到另一公开页面/无障碍文案。若区块还包含必要的真实法律事实，仅保留经核实的成品表述；修复相邻排版、目录锚点和空白区域，维持页面完整可读。真实身份、支持渠道或其他法定资料缺失只记录到项目 `.work/`，不得编造姓名、邮箱、正式域名、上线状态或把缺失事实写成已核实。原四个固定 HTTP 模板地址、固定注册表与链接的大小写和原文不因清理而更改。

使用运行器自带检查器执行 `python3 <runner-skill-root>/scripts/validate_about_copy.py --site-dir <project-root>/aduit/site`。`runner-skill-root` 指当前执行的 `flutter-engine-runner` 的 `SKILL.md` 所在目录，不是 `ios-app-listing` 的目录；资料包直接使用时为包内 `flutter-engine-runner/`，安装后为已安装运行器根目录。该检查器只读四页，不会访问 URL 或修改文件；修正文案后重跑直至无命中。它不依赖远程包是否提供 `validate_site_publication_ready.py`。静态检查后仍须本地渲染四页并查看脚本生成内容及适用外观/视口，确认未通过样式、动态插入或实体编码漏出同义提示；不得只检查首页或把静态通过当作法律资料已核实。检查结果和必要缺口放内部记录，不能生成公开校验报告或状态提示。

AppListing/About 生成、改名和最终精修时，按第 10.1.1 节移除生成器自动加入的不必要图片/视频来源列表、供应商标识、下载链接及 Credits 入口；不将内部素材清单批量转成公开页面或 Review Remarks。Terms 中的内容来源与许可说明保持概括、真实，不能据此生成逐项图库清单。保留实际许可强制要求的声明、软件必要许可通知及真实隐私/外部服务披露，四页白名单与协议 URL 原文不变。

四个自有 HTML 页面统一采用明亮色调，使用通透背景、可读正文和清晰强调色，Logo 取色仅作可选参考，渐变按主题选用。移除颜色/明暗切换控件及其偏好脚本，设置 `color-scheme: light`，清理自动变暗的媒体查询与 CSS 覆盖。系统外观变化后仍保持明亮，不改动四个固定 HTTP 模板。独立 `aduit/welcome.html` 同样执行明亮规则，继续遵守自包含、图片内嵌及体积限制。

#### About 最终配色与小体积 Logo

- **按项目选定视觉校正配色**：读取正式 `assets/logo.png` 与实际项目主题令牌，若已有 `.work/brand-palette.md` 则核对所选色值与用途；Logo 取色仅作可选参考，主题颜色保持明亮。定点修改四页各自内联 CSS 变量及需要调整的品牌页头、背景、卡片、按钮/分页点、链接、选中/焦点态和边框，检查所有样式块、内联值、媒体查询、伪元素及脚本，修正实际覆盖冲突并核验明亮可读性。渐变仅按创意选用，不要求品牌背景或强调区必须渐变。首次生成后对四页复验并保存本地渲染截图与 CSS 实际值对应证据；`aduit/welcome.html` 另按引导页专项生成和验收，不能覆盖 `aduit/site/index.html`，不联网探测协议 URL。
- **主图不降质，网页只用小副本**：`assets/logo.png` 保持正式 1024×1024 RGB PNG，取色与 AppIcon 继续用它；`aduit/site/img/logo.png` 改为由该源图派生、按网页最大实际显示尺寸约 2 倍像素生成的小图，通常 128–256 像素即可，不直接把完整大图塞进四页。以清晰度与配色合格为前提，比较适用的缩放、PNG 压缩、无损优化及调色板量化结果，选择实际字节最少且无明显失真/色带的一版；图片以字节体积和解码开销衡量，不虚构“最低码率”设置。小 Logo 目标 8–20 KiB、尽量不超过 24 KiB；记录实际尺寸/字节、源与派生哈希、压缩方式和显示对照，不能只改扩展名或直接沿用未优化的大 PNG。预算内无法满足时记录具体限制并采用已验证的最小可用副本，不让压缩失败阻断页面生成，也不宣称大小达标。
- **引导页内嵌同样优化**：`aduit/welcome.html` 若显示 Logo，将小副本的实际字节以匹配 MIME 的 Base64 内嵌，不引用 `assets/`、项目路径或远程图片；Base64 后的真实字节同样计入整个 HTML 严格小于 262,144 字节的预算。`aduit/site/` 的其他四页按生成器交付内容保留，并可引用唯一的 `img/logo.png`。不为不同尺寸增添站点白名单外图片，未显示 Logo 的页面无需人为再加一个。
- **图片不阻塞页面**：为 Logo 预留宽高/比例，使用适用的异步解码；首屏图正常加载，下方图片按需处理。正文、导航和 `Continue` 不等待 Logo 的 `load`、`decode()`、图片预加载队列或 `window.onload` 才出现/启用；业务必需准备条件仍按原规则处理。禁止同步大 Base64 转换、主线程逐像素压缩或无限图片重试，图片优化在构建前完成。失败时显示清楚的文本品牌/可恢复状态，继续显示内容与可操作按钮，不让整页白屏或永远显示加载层；缺图项仍不算图片验收通过。
- **实际检查加载边界**：本地测试四页正常、图片延迟、解码失败和断网状态；确认文字/导航/轮播可用、Continue 两种调用不受 Logo 影响，检查 WebView 首帧/内存与无未处理错误。压缩派生文件与主 Logo 的哈希通常不同，只验证可追溯派生关系、主题色和视觉身份一致，不要求两者字节相等。来源、压缩表与截图只放 `.work/`，不改 URL、文件白名单或把候选图放入站点。

四页、引导卡片、Intro 和 Remarks 同步执行第 6.6 节的文案编辑：各页按真实用途写不同内容，删除套话和重复段落；必要的法律事实、固定操作名称和审核七项结构保持准确。不能为减轻“AI 风格”虚构故事、事实或把每页改写成同一段营销介绍。

**改名后立即创建截图目录**：完成 `AppListing/` 到项目根目录 `aduit/` 的改名/整理后，立即新建 `aduit/imgs/`，再执行独立欢迎页制作、URL 回接和 Review Remarks。它与 `site/`、`review/` 同级，创建时为空，工程完成后的第 21 步按第 12.5 节放入恰好五张有意义的项目截图，每张为原始竖屏 1206×2622 PNG；不放占位文件、`.gitkeep`、`.DS_Store` 或额外产物，也不替代原有 `site/img/`。重跑时先可恢复归档旧截图，只交付当前最终构建的五张；后续清理与白名单验收必须保留此目录及合格截图。

#### Intro 与 Remarks 的科普标签统一

最终 `aduit/intro.md` 和 `aduit/review/remarks.md` 中，类别、分类、标签或产品定位标签若为“教育”“教育类”“Education”“Educational”或“教育 (Education)”等同义形式，统一改为“科普”；两份交付文档保持英语，因此实际写入 `Popular Science`。例如 Intro 的 `## Category` 正文写 `Popular Science`，Remarks 的基本信息写 `Category: Popular Science`，正文中重复出现的同一定位标签也须一致，不保留中英混合旧标签。其他已确认的类别原样保留，不把所有项目强制归为科普，也不因此虚构科学主题、课程、资质或功能。

生成器原始输出先按其现有契约校验；改名整理为 `aduit/` 后、生成引导页或 Remarks 前，执行本标签规范化，最终交付时重新核对两份实际文件。已有文档同样处理，先将原文件备份到 `.work/`，仅修改作为分类/定位标签使用的相应值，不对全文做无差别替换。应用名称、真实服务名称、普通功能叙述、四个固定 HTTP 模板（包括包含 Education 的域名、路径或参数）及其他事实保持不变。本规则只调整两份文档的展示用标签，不修改远程技能源码、生成器分类枚举或 App Store Connect 实际提交类别；不把 `Popular Science` 当作官方分类枚举传入接口。生成阶段与定制整理后的校验分别记录，后续重新生成仍须应用该规则，不因原始契约要求教育标签而恢复旧文案。

#### intro.md 的详尽项目描述（仅保留四个固定 HTTP 模板 URL，地址原文不变）

最终 `aduit/intro.md` 的 `## Description` 必须是针对当前实际 App 撰写的完整英文产品介绍，使未参与开发的人仅阅读该段就能理解应用面向谁、解决什么问题、各项主要功能怎样使用、操作会得到什么结果，以及内容如何保存和再次使用。不能只交付一句概述、三五条功能名称、生成器默认短文或“界面精美、简单易用”等泛泛营销话术。除本节科普标签规范化及下述四个 URL 整理步骤明确移除的重复 URL 栏目外，保留其他标题、顺序和事实字段；产品介绍扩写集中在现有 `## Description` 区域内，使用自然英文纯文本，按选定文案结构组织段落或项目符号，不加入 HTML、额外 Markdown 标题、内部技术说明或另一份介绍文件。

**先核对事实，再组织长文**：读取最终第一方源码、已注册页面和实际可达入口、内容/示例数据、设置及权限配置，并结合已有运行证据核对。已确认方案用于查漏，最终实现决定可描述的能力；未实现的规划不进入介绍。每个主要模块至少写清“处理什么内容 → 用户可以做什么 → 得到什么结果/为什么有用”，使用 App 实际英文页面和按钮名称，不逐项罗列代码目录或组件。需要数量时使用可核实的真实数量；不编造活跃用户、内容规模、效果、专业资质、设备测试、在线服务或性能数据。

按以下叙事顺序覆盖适用内容；这些是 Description 内的写作要点，不是在 Intro 中新增顶级栏目：

1. **具体定位与核心用途**：前 255 字符内说明实际应用名、主题、目标用户和主要用途；后续解释用户在什么场景遇到什么问题，以及本 App 如何帮助完成任务。开头清楚直接，不用空泛口号占据篇幅。
2. **完整主模块与内容结构**：覆盖每个已实现的主要目的地/核心模块及重要二级功能，说明实际分类、内容单位、关键字段或步骤，以及它们如何串联成主题任务；搜索、筛选、对比、计算、播放等仅描述实际存在的能力。不能只展开首页而漏掉其他主模块，也不能把相同功能换词重复介绍。
3. **典型使用过程与真实结果**：结合项目已有的至少 8 个不同用户结果的端到端任务，以具体、自然的操作叙述说明从进入模块、选择/输入内容、执行动作，到查看结果、保存及回访的过程；相近步骤可以合并，但读者应知道从哪里开始、做什么、最后获得什么。示例必须可按当前功能完成，不虚构用户经历或反馈。
4. **摄像机、相册与麦克风（仅实际存在时）**：只解释已选能力在主题中的用途、真实入口、操作、结果及再次打开；未选能力不写成卖点或补建。三项全无时不写媒体段落。权限根据实际 API 描述；系统选择器不等同于整库授权，拒绝后可用路径按真实行为说明，不暗示所有硬件均已验证。
5. **成果管理与连续使用价值**：说明实际可保存的主题成果、用户可以怎样继续、编辑或删除，以及再次使用时能解决什么问题。清楚区分随包示例和用户自己创建的记录；没有编辑、导出、同步、收藏或分享就不写这些能力，不把私有媒体描述为公开内容。
6. **进入与结束流程**：准确说明每次启动在 Welcome 点击 `Continue` 进入，无需账号、邮箱或登录；Settings 的结束操作按第 7.7 节和当前构建写 `Clear Data` 或 `Exit App`，说明同一个二次确认及实际行为。clear 才描述真实删除范围与默认重建，exit 描述结束当前使用、保留偏好和随包内容，不虚构数据删除或不可撤销后果。两者成功后显示 Initialization，以 `Entry` 返回主流程；不能把初始化页写成正常启动入口，也不把 Exit App 写成账号登出或系统强制终止。
7. **体验与可用性**：描述统一明亮外观、有用的主题视觉/结果表达和实际可用性支持，不宣传调色或明暗切换能力，说明它们怎样帮助阅读或操作，不堆砌“高级、丰富、极致”等形容词。离线使用、VoiceOver、大字号和减少动态等只按实际支持范围撰写；不能从几张截图推导全功能已验证。
8. **数据、权限与服务边界**：用普通用户能理解的英语准确说明实际存在的记录及媒体（如有）的处理和保存、真实需要的权限请求时机、删除范围、哪些操作需要网络，以及真实存在的账号/计费/服务限制。未使用的能力不写成卖点，不把“没有账号/不上传媒体”扩张成未经证实的“任何数据都不会离开手机”。必要事实披露保留，不暴露自有 package、模块、实现细节或多余素材来源清单。
9. **可信的独特价值与回访理由**：结合当前项目的标志性动作、内容组织规则和可回访成果，具体解释它给目标用户带来什么便利；结尾回扣真实使用场景，不使用无依据的“唯一、最好、领先”或虚构竞品比较。

**篇幅与生成方式**：Description 沿用 AppListing/商店字段的最多 4,000 字符限制，空格和换行计入；该上限不代表整份 `intro.md` 或 Review Remarks 的共同预算。已确认事实充足且选定文案结构允许时，以约 3,500–3,900 个英文字符作为充分展开的参考目标；优先保证功能覆盖、自然可读与事实准确，不靠重复或空话凑字数。生成前按当前生成器规定的选择流程确定文案样式，`description_style_label` 必须与其实际选定结果一致，正文遵守该样式的句数、段落或项目符号结构；不得擅自覆盖选择结果或强制使用 `longform`。`description` 由当前智能体依据已核实功能自行撰写后传给生成器，不能把自动短文当作已完成详细写作。不为篇幅编造能力、机械截断正文或改变其他字段。若可用样式或事实范围限制展开，只在内部记录实际覆盖与缺口，不新增询问、不停止后续材料生成。

**生成后强制复核，URL 完整保护**：在 AppListing 改名为 `aduit/` 后、使用该介绍生成引导卡片或 Review Remarks 之前，重新打开实际 `aduit/intro.md`，逐项核对上述内容是否真实落盘。先在 `.work/` 保存修改前副本，并单独记录生成器 `All URL` 中四个固定 HTTP 模板地址。介绍有遗漏或过于简略时，仅精修 `## Description` 标题之后、下一个既有 `##` 标题之前的正文；然后执行下述 URL 整理及本节科普标签规范化。描述、URL 整理与标签规范化分别核验，不重新运行生成器覆盖已精修内容，不修改远程技能源码，不因文案编辑重写 App URL 注册表。证据与备份只放 `.work/`，不向 `aduit/` 增加文件，不新增用户确认关卡。

**最终 Intro 仅保留四个固定 HTTP 模板 URL**：网址统一集中到既有 `## All URL` 块，按生成器原标签和原顺序仅保留首页、隐私政策、用户协议、Support 四项，每项一个完整模板地址。移除单独的 `## Support URL` 与 `## Terms of Service URL` 重复栏目及其内容，去除介绍其他位置的重复链接、多余网址、示例网址和无关外部链接，不留下空 URL 标题或另一个网址清单。只清理多余出现位置，不因暂不可访问、占位域名、格式看起来异常或请求失败而删除这四项中的任何一项；不以“无效 URL”为由重写地址、不访问真实目标。四个保留值的协议、域名、大小写、路径、文件名、参数及顺序、百分号编码、片段和斜杠全部原样保留，不补全、不替换、不截短。

**分别核验生成阶段与最终交付**：生成器输出先按其可用契约校验；最终 `aduit/intro.md` 在详细描述、固定 HTTP 模板整理与科普标签规范化后，检查完整模板 URL 的出现次数恰好为 4、都位于 `All URL` 且各出现一次，标签齐全、顺序未变。四个模板只替换 `【项目名称】`，四个 HTML 文件名、大小写和路径结构保持不变。除 `Description` 正文、重复 URL 栏目和多余网址的删除、本节科普标签规范化外，其余事实字段与原文保持不变；模板回接后再次只精修描述时，Description 外应为零差异。远程生成器若要求额外 URL 栏目，那是其原始输出契约；最终交付以本节四个固定模板要求为准，记录定制整理和分阶段校验结果，不回填重复栏目。缺少模板地址时保留实际缺口与已有文件、继续独立任务，不猜测或拼接新地址。Description 仍单独验收英文、纯文本、字符数、功能覆盖与事实一致性，不能把详细介绍压缩成审核备注。

#### 固定 HTTP 模板与大小写保护

- 生成完成后，在 `.work/` 保存四个固定 HTTP 模板地址作为核对记录；将 `http://【项目名称】/index.html`、`http://【项目名称】/PrivacyPolicy.html`、`http://【项目名称】/Terms&Conditions.html`、`http://【项目名称】/Support.html` 写入 `aduit/intro.md` 的 `All URL` 与 App 固定 URL 注册表。
- 后续统一替换时只替换 `【项目名称】`。四个文件名、大小写、扩展名和路径结构保持不变；未替换域名、格式异常或加载失败时保留模板并显示 App 内错误、返回和有限重试，不打开外部 App 或系统浏览器，也不探测真实地址。
- 使用无网络 WebView stub/fake 核对 `aduit/intro.md`、固定注册表、Initialization 两个链接和 Settings 三个入口的映射；源码、JSON 或 HTML 的转义在交给 WebView 前必须还原为同一固定模板地址。

示例中的路径大小写仅用于说明文件名契约：`PrivacyPolicy.html`、`Terms&Conditions.html` 和 `Support.html` 必须保持原样；示例域名不代表当前项目地址。

**错误隔离与继续执行**：不要用一条 `&&` 命令链把素材检查、Listing 生成、目录整理与 Remarks 串成全有或全无。分别运行并读取生成器 JSON、退出码与实际文件；`local_generation_complete` 仅表示介绍和页面已经生成，`media_review_errors`、`failures` 与正式发布就绪状态分别记录。退出码非零时先有限修复可修复的本地问题，保留已有产物；仅 Logo 缺失、照片许可、图片运行验证或外部网络失败不能跳过后续改名与 Remarks。正常交付仍必须满足原白名单；完全没有可解码品牌图时，允许先保留空的 `site/img/` 并移除缺图引用，记录 `logo.png` 缺失和目录契约未通过，继续生成 `aduit/intro.md`、四页正文与 `aduit/review/remarks.md`，不创建假图片或宣称白名单通过。开发期图片可以使用已有有效 AppIcon，或放入实际项目资源目录的 `assets/dev_brand.png`；来源和 `unverified` 状态记录在 `.work/`，实际 App/生成器输入与站点派生图不得引用工作目录，执行第 9.2.1 节。不能仅凭它被命名为 `assets/logo.png` 就认定正式 Logo 通过。

本节在 App 实现、UI/资源精修及第 11.9 节质量复核后执行；执行适用检查、修复可修复项并记录外部失败，不将失败改写为通过。开发期四个站点页面仅在开发浏览器预览，不将其接入 App 依赖，也不提前执行最终 AppListing。最终改名为 `aduit/` 后更新并接入 `lib/welcome.dart`，保留自包含 `aduit/welcome.html` 但不加载/打包；继续 URL 回接与 Review Remarks，不等域名或部署。

固定收尾路径：完整远程 `feature/1.2.1-A1` checkout（核对 origin/分支/revision）→ 失败切换 `/Users/admin/Desktop/config/ios-app-listing` → 仍失败使用随包生成契约 → 本地生成 AppListing、详尽 description 与 About（支持时使用 `--no-deploy-about --no-sync-project-listing-urls`）→ 核对 Logo 配色 → 改名/整理为 `aduit/` → 立即建立空 `aduit/imgs/` → 核验四页 `site/` → **实现并接入 `lib/welcome.dart`，保留独立 `aduit/welcome.html` 且不使用，分别验收** → 写入四个固定 HTTP 模板 → 仅 Initialization 底部 Terms/Privacy，Settings 三个协议 WebView 入口并无网络回归 → `aduit/review/remarks.md` → 当前阶段目录白名单/运行边界验收（五张截图在第 21 步补齐并最终复核）→ 额外产物与证据归档 `.work/` → 确认 `AppListing/` 不存在 → 最终图片/依赖检查 → 最终 iOS 权限校验及修复复验 → 按第 12.5 节交付五张 1206×2622 项目截图到 `aduit/imgs/` → 全部验收通过后第 22 步关联用户仓库并创建/切换 `feat/1.0.0`（不暂存、提交或推送）→ 最终报告。不因外部失败等待用户或取消后续材料，不冒充技能验证；不查询/推测/替换域名，不部署、不探测公开地址。

引导页检查必须先执行并记录结果，再进入 URL 回接和 Review Remarks；可修复缺陷先修复复验，外部条件受阻则记录证据并继续生成后续材料，不将验收通过作为后续材料生成的无限等待条件。检查失败仍是硬门槛未通过，不得宣称发布就绪。

协议通用文案仅初始化页显示：欢迎页和引导页都不显示该文案；只在确认所选 Clear Data / Exit App 并且实际成功后显示的 Initialization 页底部呈现。

**运行时文件边界**：`lib/welcome.dart` 是实际 Welcome 页面，路由 `/welcome` 使用 Flutter Widget，不使用 HTML/WebView。`aduit/welcome.html` 仅为独立交付文件，不被 App 使用，不登记为 asset，不进入依赖或 App bundle；站点四页职责与 URL 不变。`lib/`、`pubspec.yaml`、本地依赖、`.dart_tool`、iOS 工程、Pods、构建目录和 App bundle 中不得保留 `aduit/` 路径、目录或欢迎 HTML 副本，按路径字符串、目录项和实际打包清单检查。

**目录白名单验收**：最终 `aduit/` 直接子项恰好为 `intro.md`、`welcome.html`、`imgs/`、`site/` 和 `review/`；独立 `welcome.html` 不供 App 使用。`site/` 直接子项恰好为 `index.html`、`PrivacyPolicy.html`、`Terms&Conditions.html`、`Support.html` 和 `img/`，`img/` 只含 `logo.png`；`review/` 只含 `remarks.md`；`imgs/` 最终恰好含第 12.5 节五张原始竖屏 1206×2622 PNG，无子目录、链接或隐藏项；第 21 步截图前允许创建时为空，但此时不能宣称最终白名单已全部通过。检查实际大小写、层级、隐藏项和符号链接，不允许 `.DS_Store` 或其他额外产物。四站点页不被欢迎页替换；免责声明/版权合并到原法律页。最终同时核验 `lib/welcome.dart` 实际接入和 HTML 未打包，根目录无旧 welcome/enter HTML。

CSS/JavaScript 内联到四个站点 HTML 与独立 `aduit/welcome.html`，字体使用系统字体。站点图片仅用 `img/logo.png`，独立欢迎 HTML 图片用 Base64 data URI，遵守其严格体积预算；实际 Dart Welcome 使用已登记的本地 assets。清理额外文件前消除旧外置依赖，复验锚点、相对链接与离线显示。`aduit/html/`、过程截图、日志、备份及其他白名单外项先可恢复归档 `.work/`，不移入 `site/` 或 `img/`；第 12.5 节五张最终项目截图必须保留在 `aduit/imgs/`。

1. **按来源优先级生成当前项目的 AppListing 与 About 页面**：优先完整读取安装器同步的 `Workflow resource root/ios-app-listing/SKILL.md` 及其要求的 references、scripts、assets 和 validators，并核对 Git `origin`、`feature/1.2.1-A1` 分支与当前 revision；远程 checkout 缺失、不完整或同步失败时自动读取 `/Users/admin/Desktop/config/ios-app-listing`，本机后备也不可用时按随包生成契约继续。对当前可用来源按技能检查实际 App、分类、选定描述样式、生成与验证；不使用资料包内旧副本、旧安装或无关项目目录。`description` 必须由当前智能体根据已实现的主题、功能和最终 UI 文案撰写，再通过当前来源实际支持的 `--authoring-json` 输入；不把脚本的默认文案当作已自行撰写，不虚构账号、社区、上传或 AI 功能。固定使用 `--no-deploy-about` 与 `--no-sync-project-listing-urls`，生成并验证本地产物；不调用域名查询、About 部署接口或线上访问工具。生成前确认 `assets/logo.png` 或 AppIcon 候选是真实可解码图片；如果正式 Logo 服务只返回生成网页或正式 Logo 超时，不能把网页保存为图片，先将已有有效 iPhone 品牌图归一化为 `assets/logo.png`，或将仅供本地产物的 `unverified` 开发期品牌图独立保存在 `assets/dev_brand.png` 并仅在 `.work/` 记录来源与状态，Listing/About 继续生成但不得称为正式品牌通过。若无可解码品牌图，保留失败证据并按来源输出/校验结果处理；不得伪造正式品牌通过。远程、本机与契约来源均不可完整验证时，只标记相应校验为 `Blocked`/`Not verified`，仍继续生成可完成的本地材料、整理 `aduit/`、引导页和 Review Remarks。
2. **保持真实文件契约、成品状态和协议边界**：技能输出文件为 `AppListing/Intro.md`、`AppListing/site/index.html`、`AppListing/site/img/logo.png`、`AppListing/site/PrivacyPolicy.html`、`AppListing/site/Terms&Conditions.html`、`AppListing/site/Support.html`，按实际大小写与标点核对；用户所说的 `intro.md` 对应这份介绍文件，最终目标统一为小写 `aduit/intro.md`。`aduit/site/` 最终严格保留生成器的 `index.html`、`PrivacyPolicy.html`、`Terms&Conditions.html`、`Support.html` 和 `img/logo.png`；不得在 `site/` 下新增 Disclaimer、Content & Copyright Notice 或其他协议文件，若法律内容需要披露，应合并到这四个页面并保持可达链接。四页必须是完整、自然、彼此独立的成品文案；正文、标题、描述元数据、替代文本和无障碍标签不得出现 `Draft` 等页面状态标签、`WIP`、`TBD`、`TODO`、`Placeholder`、`Pending confirmation`、方括号填空项或作者/开发状态说明。真实产品功能名称以项目事实为据，不得用作页面状态说明。description、网页正文与最终截图执行第 6.6、11.4 节的英语及显示文案检查，不沿用技能模板里的技术术语、中文、框架名称或 `local`/`device`；固定文件名、机器字段和内部报告不作为页面正文展示。公开文案和法律陈述据实，联系地址不能靠推测；没有经确认的支持邮箱时不推断或生成 `support@<slug>.com`，省略对应联系区并在内部摘要标记公开法律审阅缺口。用自然英文准确描述所选 `Clear Data` / `Exit App` 的实际行为与隐私事实，不因关键词命中删掉必要披露。遇到校验冲突须记录对应规则与实际依据并针对性核验，不伪报所有技能校验通过，不为过词库而虚构功能或更改数据行为。
3. **About Logo 与项目主题核验**：站点的 `img/logo.png` 必须来自当前项目验收后的 `assets/logo.png`，核对来源与内容，不用技能自行选中的旧 AppIcon 或旧品牌图覆盖。About 色彩统一明亮，不要求取自 Logo；检查实际主题色、主按钮、链接、背景和选用的渐变，修正与所选方案不符的默认值及共享 CSS 覆盖，再核验明亮表现、文字/控件对比度与全部站点页面。白底、明亮冷暖色和可选渐变均可采用，整体灰暗或压黑须修正。缺少正式 Logo 时按第 2.5 节在内部记录发布阻断，并继续可完成的本地整理；About 页面不加开发状态水印，不能以临时图标冒充正式 Logo 验收。
4. **不设置域名或公开部署关卡**：生成的 URL/元数据保持技能产物原样；不得要求用户提供域名，不调用域名查询接口，不推测、替换、拼接或验证任何域名/公开主机。固定使用本地生成参数，不调用 About 部署接口、不创建或轮询部署任务、不做 DNS 或公开访问探测。记录 `AppListing generation: succeeded/failed` 与 `Delivery: Local only`；无公开 URL、域名或线上页面不阻断本地页面生成、改名和白名单核验，也不把生成的 URL 说成已上线或可访问地址。
5. **将生成目录改名为 `aduit`，明确替换旧介绍并保留审核目录**：把技能生成的 `AppListing/` 目录按可恢复方式改名/整理为项目根目录的 `aduit/`；若 `aduit/` 已存在，先把旧目录完整备份到 `.work/`，并将其中既有 `review/` 目录安全暂存，避免随旧版替换而丢失，再整理新生成内容；不把新介绍追加到旧内容后。改名完成后立即按本节创建空的 `aduit/imgs/`，后续清理不得移除该目录。将 `Intro.md` 改名为小写 `aduit/intro.md`，保留 `site/` 中四个生成 HTML 页面与 `img/logo.png`，将独立引导页保留为 `aduit/welcome.html`（不使用，不能通过移动或改名 `site/index.html` 取得），并接入 `lib/welcome.dart`，清理其余生成文件。将暂存的 `review/` 恢复到新 `aduit/`；若没有既有目录，则在第 12.2 节创建。既有 `remarks.md` 在替换前另存可恢复副本，其他 review 文件移至 `.work/`。`aduit/` 最终只能有 `intro.md`、`welcome.html`、`imgs/`（最终五张截图）、`site/` 与 `review/`；`site/` 只能有四个 HTML 页面与 `img/logo.png`，`review/` 只能有 `remarks.md`。除第 12.5 节五张最终截图保留于 `aduit/imgs/` 外，CSS、JS、字体、过程截图、日志、报告、备份或其他额外生成文件必须移入 `.work/`，不能保留在 `aduit/`。CSS/JS 应内联或由页面生成流程处理，不能因此增加白名单外文件。以文件清单、必要哈希、可读性和相对引用验证无遗漏，不能只转移首页而漏掉 Logo、Support 或协议。
6. **核验改名后的 `aduit/site/` 并清理多余内容**：以改名后的 `aduit/site/` 作为后续正文维护源，按第 7.6 节核验四个固定 HTML 页面及其合并法律章节、稳定文档注册、相对引用和离线显示，不让改名产生失效链接或两份不同版本。逐项核验 `aduit/intro.md`、四个 HTML 文件和 `img/logo.png` 的存在、内容、Logo 配色与离线显示；不执行线上访问检查。将改名前生成的临时输出和开发记录移入 `.work/`，不得创建或保留 `aduit/html/`。改名/核验失败时保留可恢复备份并修复，未解决时如实说明；清理失败不谎报成功、不删除唯一副本。

**改名后的品牌复验**：按第 10.4 节将当前正式 Logo 按本节压缩成网页小体积派生图放到 `aduit/site/img/logo.png`，记录源/派生哈希和视觉同一性，实际查看本地四页的 Logo/品牌封面与选定配色，修正旧图片引用；同时确认 App 的桌面图标、原生启动品牌图和 Welcome/Initialization 页面未被生成器或后续构建改回旧图。站点不新增独立封面图片文件，保持原白名单。

**页面成品文案检查**：最终生成或修改四个 HTML 页面后，必须按本节运行随运行器提供的 `validate_about_copy.py` 并查看四页实际渲染。所选 `ios-app-listing` 来源另有 `scripts/validate_site_publication_ready.py` 时，再运行其支持的 `--site-dir <project-root>/aduit/site` 检查；缺失时记录该工具不可用，不等待、不伪称执行成功，继续随包检查与页面复核。修复正文、标题、描述元数据或无障碍标签中的草稿/占位内容，并确认页面不是空壳。若缺少真实联系或其他法定事实，只在内部摘要标记公开法律审阅未完成；继续本地生成和接入，不在页面中显示待补字段，也不谎称法律材料已完成。

**AppListing 改名后：Dart 欢迎页与独立 HTML 交付**：在最终 `AppListing/` 已改名/整理为 `aduit/` 后、URL 回接和 Review Remarks 之前，依据最终源码、配置、实际页面与 `aduit/intro.md` 同步完成以下两份产物。原位保留 `aduit/site/index.html` 的生成器内容与结构及其余三个站点 HTML 的职责与路径；本操作不替换、覆盖或移动四页，必要的品牌配色、Logo 优化及成品文案修正仍按本节执行，四个固定 HTTP 协议模板和四个文件名保持不变。

1. **App 实际使用 `lib/welcome.dart`**：定义并导出 Flutter `WelcomePage`，将 `/welcome` 路由实际指向它。按第 6.13、7.1 节自由设计本项目独有、复杂且贴题的精致欢迎构图，不固定卡片形状、区域顺序或按钮位置，保持必要内容与行为：3–5 个真实介绍章节/卡片、自动轮播、可点击且有可访问名称的分页圆点、英文文案、按创意选定的明亮色彩与可选渐变、主题背景、圆角图片、图标、Emoji 和适用图片/GIF，以及 `Continue`、真实准备步骤/百分比/进度、错误态 `Try again` 与所选 `Clear Data` / `Exit App`。不能只放一个按钮、删除视觉效果或把 HTML 字符串包进 Dart。使用 Flutter Widget，可选择 `PageView` / `PageController` 或等价章节呈现与可释放的控制器/计时器；不能把组件选择当作固定整页骨架；复杂子组件按原页面分类拆分，欢迎入口固定在 `lib/welcome.dart`，其余页面不集中到该文件。图片/背景/GIF 使用已登记并随包的项目 `assets/`，通过 `Image.asset` 等加载，不从 `aduit/`、HTML、网络或超大 Base64 字符串读取。此 Dart 文件不适用 HTML 的 256 KiB、内联 CSS/JS 或 Base64 限制；正常资源解码、命名、圆角、许可和最终图片验收继续执行。
2. **原行为改为 Dart 调用**：`Continue` 直接调用现有 Welcome-to-main 的 Dart callback/路由逻辑，防重复点击/重复导航，不通过 WebView、JavaScript、AppBridge 或 URL scheme。保留原准备条件与进入目标，准备就绪且原生承接层淡出后才允许继续；不增加 `Enter` 或协议页脚。每次启动仍进入 Welcome；只有所选 `Clear Data` / `Exit App` 二次确认且真实成功后才进入独立 Initialization（`/entry`、`Entry`），协议通用文案仅初始化页显示。协议页继续由 App 内 WebView 显示；改名为 `aduit/` 后才接入这四个 HTTP 模板，不跳转到外部 App。
3. **保留 `aduit/welcome.html`，但不使用**：将原自包含 HTML 欢迎引导页保留/生成在 `aduit/` 顶层，仅供独立查看、交付和后续使用，不作为 App 页面、资源、回退页或启动就绪来源。内容和骨架对应本次实际 Dart Welcome 的已选独有方案，不恢复固定居中卡片模板；原 HTML 契约继续适用：全部 HTML/CSS/JavaScript 内联、系统字体、3–5 个介绍章节（不限定矩形卡片容器）、自动轮播/分页点、全英文、所有图片 Base64 data URI 内嵌、完整 UTF-8 文件严格小于 262,144 字节、无外部资源请求，`viewport-fit=cover` 与 `env(safe-area-inset-top)` / `env(safe-area-inset-bottom)`、圆角裁剪、`prefers-reduced-motion`。Logo 使用优化小副本的内嵌字节，不引用工程资产或站点相对图片。保留下面的原 Continue 函数，两个交付表示中只有 HTML 使用此函数，App 的 Dart Welcome 仍直接导航；生成器站点首页已有的同类函数照常保留，不因本说明删改。App 不为它注册消息桥、URL scheme、导航拦截或加载入口，也不把它打包；生成器站点首页同样不接入 App 或打包。

```javascript
function continueToApp() {
  if (window.AppBridge && typeof window.AppBridge.postMessage === 'function') {
    window.AppBridge.postMessage('continue');
    return;
  }
  window.location.href = 'go://continue';
}
```

欢迎页禁止整页或内部纵向滚动，实际 Dart 与独立 HTML 均按第 7.1 节不可滚动硬门槛验收；仅允许卡片横向切换，不能用裁切或过小字体掩盖溢出。

运行 Welcome 只由 `lib/welcome.dart` 承担；保留的 `aduit/welcome.html` 作为独立交付文件，与 Dart 设计保持内容/视觉一致。两份表示共同按第 7.1、10.5.1 节先选精细主视觉，再围绕素材自由构图，逐章节安排不同的图文关系与视觉节奏；不使用整页同骨架换图换字，也不以简单线条、轮廓或色块拼接作为主图，覆盖 AI、原创、SVG、Canvas/CustomPainter 与其位图导出。材质、光影、叠层和过渡围绕主题自主设计，静态及减少动态时仍须完整精致。独立 HTML 允许对同一合格原图另导出小尺寸 JPEG/WebP/PNG 并压缩，记录派生关系；完整 UTF-8 文件严格小于 262,144 字节（256KB），包含 Base64 编码膨胀、data URI 前缀、HTML/CSS/JavaScript 和 Logo。嵌入最终图片后重新读取精确字节数，并在四指定视口离线复核全部章节与每张解码图的细节、边缘和色带；不以原始图片体积合计代替总文件验收，不以外链或简图降质凑预算。Dart 的本地 assets 继续独立按实际展示质量验收，不受 HTML 文件体积约束。

4. **安全区、动态和无缝启动**：Dart 欢迎页使用 `SafeArea` / `MediaQuery` 与响应式约束处理刘海、Dynamic Island 和底部安全区。尊重系统减少动态：停止自动轮播与非必要位移/呼吸/粒子运动，分页点可手动使用，保持原定静态色彩和按下反馈；随前后台、路由离开及 dispose 暂停/释放动画与计时器，恢复不重复创建。按第 10.4.3 节仅由实际 Flutter 欢迎首屏布局、必要准备、首屏必需图片解码/绘制及可用 Continue callback 发出操作级就绪信号；就绪后原生同款承接层必须保持 250 毫秒再淡出，失败在同页显示恢复状态。不能等待独立 HTML、DOM 或网页消息；不能用单独 postFrameCallback 或固定延时冒充完整就绪。
Welcome Dart 与独立 HTML 不提供暂停按钮、暂停/恢复控件或 paused 状态，也不注册 Welcome 专属暂停/恢复回调。前后台、路由离开和 dispose 的动画/计时器停用只属于生命周期资源管理；其他页面的 GIF、视频、录音和游戏控制按实际功能保留。
5. **旧工程迁移与边界**：先将原欢迎 HTML、配置和专用桥代码可恢复地备份到 `.work/`；需要保留的 HTML 最终只放 `aduit/welcome.html`。删除根目录旧 `welcome.html` / `enter.html`、`aduit/enter.html` 等过时副本，清除欢迎页专用 WebView/HTML 包装、桥接监听、scheme/导航拦截与旧路由，移除 pubspec 资源项及 native copy/build phase 对旧 HTML 的引用。保留协议页面仍实际需要的 WebView 依赖与安全配置。`lib/`、`pubspec.yaml`、依赖树、iOS 工程、构建产物和 App bundle 不得引用或包含 `aduit/`、`welcome.html` 或 `enter.html`；不得通过别名、通配目录、符号链接或复制到其他路径绕过。源文件 `lib/welcome.dart` 通过 Dart import/路由编译，不登记为 Flutter asset。
6. **分别验收运行页面和独立文件**：App 运行时只验收 Dart 页；独立 HTML 仅在 `390×667`、`390×844`、`1024×768`、`1440×900` 检查安全区、可读性、无重叠/裁切/遮挡，大尺寸只是布局约束测试，不扩大 iPhone-only 产品范围。Dart 页用 widget/导航测试和当前 iPhone 构建验证轮播、每个圆点、滑动、减少动态、离线资源、准备/失败/重试/所选结束操作，以及 Continue 直接进入原有主流程且重复点击只导航一次；用连续运行画面与单调时钟证据验证就绪后 250 毫秒保持再淡出。独立 HTML 核验字节数、每张 Base64 图片解码/可读性、断网显示、轮播和分页点；在独立浏览器用隔离 stub 验证原 Continue 函数两分支，不连接 App，不访问真实协议地址。确认 HTML 不进 App bundle，App 运行时唯一 Welcome 是 Dart 页。截图和日志只放 `.work/`；引导页检查必须先执行并记录结果，再进入 URL 回接和 Review Remarks。可修复缺陷先修复复验，外部验证受阻据实记录 `Blocked`/`Not verified` 并继续后续材料，不宣称发布就绪。

**About 完成后、Review Remarks 前的 Initialization 文案与协议入口回接**：在 About/AppListing 本地生成、配色核对并整理为 `aduit/` 后、生成 `remarks.md` 前执行。将四个固定协议链接写入 App 的固定 URL 注册表，统一使用 `http://【项目名称】/index.html`、`http://【项目名称】/PrivacyPolicy.html`、`http://【项目名称】/Terms&Conditions.html`、`http://【项目名称】/Support.html`，保留完整 HTTP 写法，方便后续按项目名称统一搜索替换。四个文件名保持原样和大小写，不改名。此时将以下两行协议文案接入 所选 Clear Data / Exit App 确认并实际成功后出现的 Initialization 页底部，显式在 `our` 后换行，无句末句号；每次启动进入的 Welcome、Welcome HTML 引导页和原生启动页均不得显示这段文案：

```text
By continuing, you agree to our
Terms of Use and Privacy Policy
```

两行居中放在 Initialization 页底部安全区内，不截断文本；第二行的 `Terms of Use` 与 `Privacy Policy` 分别可点击，使用对应的固定 HTTP 模板，`and` 为普通文本。不能只改 About HTML、字符串文件或规划说明而不更新 App 实际显示。不增加勾选或额外确认，不保存个人协议同意记录，也不将按钮等同于媒体授权；Terms 正文应与这项实际提示一致。Settings 同一页面只提供三个链接：Privacy Policy、Terms of Use、Support；`lib/welcome.dart` 作为唯一运行 Welcome 页，`aduit/welcome.html` 不接入 App；站点 `index.html` 按本节硬门槛保留生成器原有内容与结构，仅交付、不写入 Settings；不能为改成 About Home 或套用独立 welcome.html 的要求而重写首页。Settings 仍只提供 Privacy Policy、Terms of Use、Support 三个入口，首页 `index.html` 的链接保存在固定注册表但不提供 Settings 入口。四个协议页面均在 App 内 WebView 打开，禁止调用外部 App；未替换域名或目标不可达时保留原模板，显示可读错误、返回与有限重试，不回退到开发期本地预览页面。回归时按第 7.2 节核验 Initialization 的完整原文、显式换行、底部安全区和两个独立链接，并确认 Welcome、HTML 引导页和原生启动页均无该文案；用不发起网络请求的 WebView stub/fake 核验注册值、实际入口 URL、Settings 不含引导页、失败/返回状态和主流程，不访问或探测真实目标；完成后继续 Review Remarks，不重开总体 UI 审批。

7. **完成 AppListing 与协议入口阶段**：报告实际使用的 `ios-app-listing` 来源（远程分支、本机后备或契约来源）、可取得的分支与 revision、当前智能体撰写的 description、About 配色核验和修正结果、`AppListing/` 生成与改名/整理为 `aduit/` 的结果、站点白名单核验及额外文件移出位置，以及四个固定 HTTP 模板的接入和定向回归结果。远程、本机或生成器失败时报告对应 `Blocked`/`Not verified` 证据，但继续完成独立的本地材料、引导页、目录清理和第 12.2 节 Review Remarks；不得使用资料包内旧副本或手写页面冒充技能产物。备份放在 `.work/` 并说明可恢复位置。完成所有可执行步骤后再做完整白名单核验，不在此阶段提前宣布最终交付。不询问用户意见、继续许可或交付确认。

### 12.2 App Review Remarks

在第 12.1 节完成后，为当前 Flutter App 生成审核备注，并写入 `aduit/review/remarks.md`。若目录不存在则创建；若文件已存在，先将旧版保存到 `.work/` 中的可恢复位置再替换。此文件是 `aduit/` 的唯一审核备注产物，不新增其他审核材料到该目录。备注全程使用英语，字符总数不超过 4,000；使用七个编号 Markdown 标题，各章正文分点描述，不使用 `**` 粗体标记，不输出分析、推理、免责声明或中文。

**分点写作与内容边界**：基本信息每项单独一行；七个章节内按事实使用简洁的 `- ` 项目符号，每点只说明一个事实、操作或结果，设置流程使用按操作顺序排列的编号列表。实际设备、地区差异和独特价值只有一条时保留单个条目，不为凑数量扩写，不把整章合成冗长段落。`remarks.md` 全文不得出现 `WebView`、`web view`、`WKWebView`、`WebKit` 或网页容器、嵌入式网页等实现描述，覆盖基本信息、七章、括注及依赖说明；不叙述协议页面的呈现方式、URL 回接、桥接、内部路由或本地页面实现。已有备注中的相关文字同样移除。真实外部服务仍按名称、用途和实际数据处理如实说明；内部显示容器不作为外部服务列举，不把实际使用写成未使用，也不新增服务或省略必要隐私事实。实现与网址可达性检查只记内部记录，审核备注以可执行的用户操作和实际产品能力为主。

**全文设备范围仅限 iPhone**：`remarks.md` 的基本信息、七个章节、正文、括注及测试/截图说明只保留有依据的 iPhone 机型、对应 iOS 版本和实际测试范围。读取混合设备记录时先筛选 iPhone，其他设备的名称、系统版本、测试记录、兼容性说明及排除示例均不写入最终备注。修改既有备注时同样清除这些内容，混合句中只保留能独立核实的 iPhone 事实；不得把其他设备的结果改名为 iPhone 记录，也不得为补足数量编造测试。iPhone 真机与 iPhone Simulator 仍须准确区分。完成后通读全文核对设备范围，而非仅检查第 2 项；备份与清理证据只放 `.work/`。

**类别标签与 Intro 一致**：按第 12.1 节的科普标签规则读取最终介绍文件；原教育类标签统一写为 `Popular Science`，基本信息使用 `Category: Popular Science`，各章出现的同一定位标签保持一致。不得从生成器原始文件回填 `Education` 或中文“教育”，也不改写其他类别、真实功能或服务名称。

先读取当前实际存在的介绍文件：AppListing 尚未规范化时为 `AppListing/Intro.md`；完成第 12.1 节转移/小写规范化后，以白名单中的 `aduit/intro.md` 为准。若输入材料写作 `aduit/Intro.md`，先核对实际大小写，不得因大小写不符漏读或另造重复文件。提取应用名称、用途、类别、功能、用户生成内容、账号、计费、权限和其他提审信息；必要时查看源码、配置、测试记录和现有审核材料核实事实。还要在内部逐字核对 App 固定协议 URL 配置与 `All URL` 四项映射，但不发起网络请求；映射和可达性状态只记录到 `.work/`，不写入审核备注，也不据此宣称在线服务可用。不得把开发期占位文案当成最终事实。输出以 `# App Review Remarks` 开始，随后仅列出有确认依据的普通英文标签 `App name`、`Purpose`、`Category`、`User-generated content`、`Account`、`Billing`、`Permissions` 和 `Other submission details`；缺失或未确认字段直接删除，不写占位语。之后按以下七项顺序使用清晰的 Markdown 标题：`## 1. Actual Device`、`## 2. Test Devices and Operating Systems`、`## 3. App Purpose, Intended Audience, and Problem Solved`、`## 4. Setup Steps`、`## 5. External Services`、`## 6. Regional Differences`、`## 7. Unique Value`。

1. Actual Device：按“原生竖屏截图尺寸为 1206 × 2622 像素的机型中，选择当前性能最高的 iPhone”确定配置。本次规格核验日期为 2026-10-30：[Apple 官方 iPhone 18 Pro 技术规格](https://www.apple.com/iphone-18-pro/specs/)确认 iPhone 18 Pro 搭载 A20 Pro、屏幕原生像素为 2622-by-1206，出厂系统为 iOS 27；Pro Max 的原生像素为 2868-by-1320，不符合指定尺寸。因此覆盖旧的 Pro Max / iOS 26.5 固定值，第 1 章正文必须按顺序逐字写入以下两条：

   ```markdown
   - iPhone 18 Pro, iOS 27
   - Screenshot size: 1206 x 2622 pixels (portrait).
   ```

   第 1 章不能为空，不增加其他机型、系统版本或测试通过声明。该配置与第 2 项的两台测试设备分别填写，不互相替代；型号与尺寸要求本身不构成当前 App 已经完成真机测试的证据，不得把模拟器结果称为真机结果。截图要求是原始竖屏 PNG 的实际像素宽 1206、高 2622，不能用裁切、缩放、补边或更改文件名把 Pro Max 等其他机型伪装成符合要求。对实际生成的截图读取像素尺寸，并把原始文件、机型/运行环境与尺寸检查证据记到现有 `.work/quality.md`；没有运行或截图证据时不声明已实测，缺口留内部并继续独立材料生成，不为满足备注新增多个模拟器。此处固定值是本次已核验的配置快照，不凭未来机型名称推测规格；后续若更新配置，必须先核实 Apple 官方的芯片、原生像素和可用系统，再同步本文、执行摘要及校验器。
2. Test Devices and Operating Systems：固定使用用户提供的两个测试设备配置，不再随机抽样，不增加、替换、合并或漏写，不把第 1 项实际设备挪到本项。该章正文不能为空；前两个非空正文行必须按以下顺序逐字写入，设备与系统版本分别准确对应，各出现一次：

   ```markdown
   - iPhone 15 Pro, iOS 18.6
   - iPhone 13, iOS 17.7.1
   ```

   两条配置是用户指定信息，必须保留；它们本身不代表当前 App 已完成测试，不能当作每个新项目已经完成的测试。只有当前 App 的实际测试记录或用户明确确认的测试结果，才可在这两行之后另用项目符号说明对应测试范围与结果；不再次列举机型/系统，不新增其他设备。缺少结果依据时仅保留这两行配置，验证缺口只记 `.work/`，不留空、不输出待补占位语、不宣称测试已完成或无阻塞问题。其他设备的运行记录只记内部，不替换该固定名单；不要照搬不存在的注册/登录或计费测试声明。
3. App Purpose, Intended Audience, and Problem Solved：只依据 `aduit/intro.md` 和当前实现说明产品用途、主要用户及解决的实际问题，不夸大。
4. Setup Steps：按审核人员可执行的顺序写安装/启动、点击最终引导页的 `Continue` 进入主要功能（仅改名前开发预览可用 `Enter`）、仅为实际存在且需要授权的功能列出真实入口、触发系统授权的操作和拒绝后的可用路径；系统照片选择器按实际行为说明，不添加整库请求；无受保护能力时明确无需这些权限，不编造媒体操作，随后按第 7.7 节说明 Settings 中实际采用的 `Clear Data` 或 `Exit App`、对应二次确认及成功后显示 Initialization/Entry 的结果；无用户数据不写删除步骤/范围，有实际删除则准确列明。注册/登录、验证码、邀请码或测试账号仅在实际存在时说明路径；不存在时写 `No such feature`。计费或内购步骤仅在实际存在时提供，并按审核人员可执行顺序说明；无需特殊设置时明确写 `No additional setup is required.`
5. External Services：逐项列出有证据确认实际使用的外部服务、平台、API、分析工具、支付服务、云服务及第三方 SDK，并说明各自用途；另以独立标签列出 `Advertising`、`AI services`、`Third-party SDKs`。确认未使用时写 `Not used.`，确认没有该能力时写 `No such feature`；未知或未提供的项目从最终备注中删除，不写 pending 占位语。内部缺口只记录到 `.work/`。不列举协议链接、页面容器或访问状态；只列真实外部依赖，不暴露自有 package、内部模块或目录；不得查询、要求或推断域名。
6. Regional Differences：本流程的功能、内容、价格、权限和可用性应保持地区一致；该章唯一条目固定写 `- All regions are the same.`，不改写或添加待确认语。若实现存在已确认差异，先修正实现和材料一致性，再使用固定句；不得把真实差异隐瞒成无差异，证据缺口只记内部。
7. Unique Value：用一句具体、可信且与当前功能一致的话概括与同类产品的差异和用户价值，避免空泛营销语。

七个章节标题须全部保留，基本信息仅写已确认字段；每章按事实使用项目符号，设置流程使用有序列表。只使用源码、配置、实际测试记录或用户明确提供的已确认事实；不能编造设备、系统版本、测试、视频、账号、服务、SDK、地区支持或功能。未知测试结果和其他未确认、待提供、待补充或无法核实的字段、句子均从最终 `remarks.md` 删除，不写 `Not provided; pending confirmation.` 或同义占位语；已确认不存在的能力才写 `No such feature` 或 `Not used.`。第 1 项固定为 `iPhone 18 Pro, iOS 27`，另起项目符号逐字写 `Screenshot size: 1206 x 2622 pixels (portrait).`；第 2 项固定为用户指定的 `iPhone 15 Pro, iOS 18.6`、`iPhone 13, iOS 17.7.1` 两条配置；两章不同且均不能为空，不因缺少测试结果而删除已指定配置，不以固定名单推导测试已经完成。第 6 项固定为 `All regions are the same.`。不要把 iPhone 模拟器测试写成真机测试。完成后运行 `python3 <flutter-engine-runner-root>/scripts/validate_review_remarks.py --remarks-file <project-root>/aduit/review/remarks.md`，校验器必须拒绝空设备章、漏项、顺序/机型/版本不符、重复或额外测试设备，再检查全文仅为英语、字符数不超过 4,000、基本信息及七项顺序/标题准确、无 `**`、不出现 H5、B-side、WebView、内部 package/模块信息，并与 App、实际存在且大小写正确的介绍文件及审核事实一致；不等待用户审批或补充意见。

### 12.3 App Store 隐私披露、EULA 与提交材料

1. 根据实际数据流填写 App Store Connect 隐私披露，覆盖 App 本身、第三方 SDK 与 App 功能内 WebView。纯设备端处理的照片与录音不因访问系统权限就自动属于 Apple 定义的“收集”；若其他数据离开设备，按 Apple 当前定义分别判断用途、保留、关联身份与追踪，不直接套用 `Data Not Collected`。
2. App 内必须提供隐私政策入口；最终 Entry/Settings 目标按 `aduit/intro.md` `All URL` 原样配置，不执行公开部署或可达性验证。目标地址可达性须记为未验证，不通过回归测试发送网络请求，也不自行修复地址。若正式提交仍需要公开可访问的隐私政策 URL，单独记录为未验证发布前置条件；公开链接、真实开发者身份或联系渠道缺失时保留本地产物并记录缺口，不编造信息、不要求用户提供域名，也不因此停止其他本地实现。
3. 明确采用 Apple 标准 EULA，或在确需自定义 EULA 时依据 Apple 当前最低条款完整准备并正确配置；App 内 `Terms of Use` 不自动等同于 App Store 的自定义 EULA，不能宣称四份 HTML 已覆盖所有提交协议。
4. 审核说明必须写明无需登录，并给出从最终引导页点击 `Continue` 到达主要功能的步骤；仅对实际选用的摄像机/相册/麦克风列具体入口与用途，按所需授权说明拒绝后的可用路径；三项全无时不编造入口或权限测试。另列所选清除或退出操作的真实入口/二次确认/成功后显示 Initialization 的结果，名称/范围须与实际构建一致。截图、描述、年龄分级与二进制一致，不展示未实现能力或用户私有素材。
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

发布材料必须和当前二进制一起审计，不能把生成器输出当成事实证明。对 `App Store Connect` 元数据、截图、`aduit/intro.md`、四个站点页面、Support 和 `aduit/review/remarks.md` 执行以下检查，并将结果写入 `.work/app-review-risk.md`：

- 只有一个产品身份：Bundle ID、显示名称、类别、应用图标、描述、支持信息和审核备注互相一致，不创建同一产品的地区/品牌/主题副本，也不把共享模板当成独立产品。
- 描述产品的差异来自真实目标问题、领域内容、任务路径、交互规则和用户可回访结果。只更换 Logo、颜色、字体、素材、文案或卡片外观的版本不能提交；无法证明实质差异时标记 `4.3 risk: Failed`。
- 公开材料只写已确认的开发者身份、支持渠道、服务、权限、设备测试、地区和计费事实；不编造测试账号、购买结果、用户规模、合作关系、可用地区或公开部署状态。缺失项留在内部记录，不在 About 或 Remarks 中补写推测。
- 不加入自定义评分/评论弹窗、五星引导、评价奖励、搜索词堆叠、虚假推荐、引荐或安装量操纵。需要评价时只允许 Apple 系统评价 API，且必须有真实产品需求和测试证据。
- 质量缺陷、无效链接、占位资源、错误权限、白屏、崩溃、数据损坏和未完成核心任务必须先修复；材料完成不等于发布就绪。把专项结果与 `Verified`、`Blocked`、`Not verified` 分开记录。

4.3 或 5.6 的关键项失败时，仍可继续生成本地 `aduit/` 和其他不依赖项，但最终报告必须写 `Release readiness: Blocked`，说明具体阻断和下一步；不得以“已生成材料”或“流程未中断”替代审核合规结论。

### 12.5 最终五张项目截图（硬门槛）

在工程实现、全部发布材料、最终图片/依赖检查和第 11.6 节权限校验及其修复复验完成后，执行第 13 节第 21 步；全部项目验收与五张截图通过后，再按第 13.1 节执行第 22 步 Git 交接，不提交代码，之后提交最终报告。自主选择并实际截取五张有产品意义的当前 App 画面，存入项目根目录 `aduit/imgs/`；不再询问选页或保存位置。该目录创建时为空，最终交付时必须恰好包含本节五张 PNG，此为最终目录契约。

- **选图**：围绕本项目真实核心任务选择五个内容与用途有实质区别的页面或操作结果，优先展示主要功能概览、不同核心模块、内容深度、主题专属交互及有价值的成果；具体组合随主题决定，不固定页面模板。不能用五张相似列表、同一页换配色/轻微滚动、启动/加载/空白页或连续动画帧凑数，也不为截图新增未选功能或虚构完成结果。使用实际随包内容或已有可用演示记录，避免私人敏感信息。
- **真实采集**：复用第 0.9.1、0.10 节的测试安装与已有 iPhone，串行进入五个目标画面，从最终交付构建真实截屏；使用可用 iPhone 截图工具，模拟器可用 `xcrun simctl io <明确的 iPhone UDID> screenshot <输出 PNG 路径>`。不新建测试 App、Bundle ID 或模拟器，不拍 HTML、设计稿、测试拼图、外壳样机图或其他项目替代。保留正常视觉效果，在有代表性的清晰状态截图，不关闭动画来掩饰未实现效果。
- **尺寸与画质**：每张必须是原始竖屏 PNG，实际像素宽 1206、高 2622。沿用第 12.2 节的指定 iPhone 截图配置并核对实际运行目标；设备/工具输出不符时修正采集目标或方法后重截，不裁切、缩放、拉伸或补边凑尺寸，不将其他设备截图改名冒充。逐张读取像素尺寸、完整解码并实际查看，确认本地图片正常显示、文字清晰、无占位图/黑白空屏/重叠裁切/无关系统弹窗或调试浮层；同哈希或语义近似重复均重新选图。
- **文件与记录**：按展示顺序使用 `01_<短页面或功能ID>.png` 至 `05_<短页面或功能ID>.png`，ID 使用本项目真实简短英文标识。截图先在 `.work/` 中完成采集与核验，再将合格的五张交付到 `aduit/imgs/`；既有内容先可恢复归档，清除多余文件、子目录、链接及隐藏项，不加入 `.gitkeep`、`.DS_Store`、日志或清单。该目录与 `aduit/site/img/logo.png` 分开，不被 App 引用或打包。将每张的文件路径、展示价值、页面/操作路径、构建/Bundle ID、实际 iPhone/iOS/UDID、真机或模拟器、采集时间、像素尺寸与哈希写入既有 `.work/quality.md`，最终报告提供五张文件链接。
- **复验与完成**：截图中发现可修复问题先修复、更新同一安装并复验；之后的代码、资源或配置变更若改变截图画面，重截受影响项并核对五张仍来自最终构建，相关图片/权限验收按原规则刷新。再次检查目录数量、尺寸、解码、内容差异与当前构建一致后才将此项标为 `Verified`。实际 iPhone/截图工具不可用时保留已完成产物，记录具体缺口并继续独立工作，不能生成假截图、复制同图凑五张或声称完整交付。
