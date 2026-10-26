## 12. App Store、法律与 About 材料

思维导图整体确认并开始实现后，所有公开材料从实际实现生成，并且 App 内公开文案保持英语：

**发布范围固定为 iOS iPhone。** AppListing、About、Support、协议、商店文案、预览和截图均只面向 iPhone；不出现其他设备版本、兼容性声明、商店分发选项或下载入口。最终核对构建产物与商店配置时，只有 iPhone 可用；若后台无法验证这一点，明确记为未验证，不将其描述为已限制完成。

- `Privacy Policy`：完整说明摄像机、相册选择/读取与麦克风的具体用途、授权时机、拒绝/撤销后的行为，照片和录音的本地处理、保存位置、保留、删除、临时文件、备份边界与安全措施；按第 8.5 节准确说明 `Clear Data` 二次确认后清除 App 自有媒体、记录、偏好和缓存，成功后进入 Initialization，失败可重试，系统相册原件、App 外导出文件、现存备份和系统权限不由此删除或重置。说明实际的第三方 SDK、WebView 请求、诊断/网络元数据、接收方和 ATT/追踪结论。App 无需账号、不要求邮箱输入或身份认证数据、不上传用户媒体；若真实支持渠道接收用户主动发送的信息，按第 0.3 节准确披露，不将无账号扩大为未经核验的“所有数据绝不离开设备”。包含真实开发者身份、联系渠道、生效日期、政策变更及适用的隐私权利说明，不声称保存个人协议同意记录。
- `Terms of Use`：完整说明功能范围、内容来源、许可、可用性、用户责任和禁止滥用，以及拍摄/录音应尊重他人权利、本地媒体保存与删除、用户需自行备份的重要内容、服务限制和联系方式；不得将这些条款变为隐蔽免责。准确描述每次启动进入 Welcome 并点击 `Continue` 即可进入主流程（仅改名前开发预览可显示 `Enter`），`Clear Data` 须二次确认、无法通过 App 撤销，清理成功后进入 Initialization；不加入不存在的退出、登录、会员、上传或社交功能，也不宣称按钮代表勾选协议、授予系统权限或同意 ATT。
- `Disclaimer` 章节：在 `Terms&Conditions.html` 或 `PrivacyPolicy.html` 中根据主题提供仅供参考的说明，以及适当的专业意见排除条款。
- `Content & Copyright Notice` 章节：在现有法律页中用简洁、真实的内容使用与权利说明及更正/删除联系渠道表达，不默认逐项列举图片/视频供应商、作者、来源链接或素材许可。按第 10.1.1 节仅加入实际许可要求的最小必要声明；没有公开署名义务的素材只留内部核验记录。区分随包内容和用户本地拍摄/导入/录音，不声称拥有用户媒体，不把私有媒体列入公开清单，也不作虚假的全部原创或自有版权声明。
- About Home 与 Support：使用清晰、友好的产品介绍和支持说明，通过同一 WebView 页面展示，不把 About Home 误写成 App 主首页。

开发期根据实际实现持续维护应用介绍、About、支持页和协议正文，四个 HTML 页面始终保持完整、自然、可独立阅读的成品文案，不显示 `Draft` 等页面状态标签、待补提示或作者备注。最终生成的 `site/index.html` 会在 AppListing 改名为 `aduit/` 后被当前 App 的自包含引导页替换；其余三个页面仍为 Privacy Policy、Terms & Conditions 与 Support。缺失的开发者、联系、司法辖区等事实不得猜测，也不得以填空语写入页面；仅在内部生成摘要中记录具体缺口，并标记公开法律审阅未完成。页面生成、接入与本地校验不因此卡住；这不等于宣称法律材料已可公开发布。全流程不依赖域名、公开部署或线上访问。App 功能、UI、资源和第 11.9 节质量复核完成后，依次使用安装器从远程指定分支同步的完整 `ios-app-listing` 目录生成 AppListing 与 About 页面、核对 Logo 配色并整理为 `aduit/`，按本节先替换并接入首页引导页，再更新 Entry/Settings 的 WebView URL，最后按第 12.2 节依据已核实事实生成英文 Review Remarks。质量复核的完成含义是已执行适用检查、修复可修复问题并记录外部失败；图库许可或正式 Logo 仍为 `Blocked` 时，不得把相应质量项写成通过，但不能阻断已独立的本地材料步骤。远程 `ios-app-listing` checkout 缺失、来源不符或同步失败时，只将 AppListing 阶段标为 `Blocked`，不得改用资料包副本或手写等价产物。均由智能体自主完成，不新增询问关卡；不要求或查询域名，不公开部署。

### 12.1 AppListing 与本地 About 页面生成、改名为 aduit 并清理

AppListing/About 生成、改名和最终精修时，按第 10.1.1 节移除生成器自动加入的不必要图片/视频来源列表、供应商标识、下载链接及 Credits 入口；不将内部素材清单批量转成公开页面或 Review Remarks。Terms 中的内容来源与许可说明保持概括、真实，不能据此生成逐项图库清单。保留实际许可强制要求的声明、软件必要许可通知及真实隐私/外部服务披露，四页白名单与协议 URL 原文不变。

四个自有 HTML 页面同步第 6.5 节的背景规则：浅色外观使用 Logo 暖色渐变整体底色，不能回退纯白；正文采用稳定高对比表面，深色外观保持现有规则。包括最终替换的 Welcome 引导 HTML，继续遵守自包含、图片内嵌及体积限制。

**改名后立即创建空目录**：完成 `AppListing/` 到项目根目录 `aduit/` 的改名/整理后，立即新建 `aduit/imgs/`，再执行引导页替换、URL 回接和 Review Remarks。它是与 `site/`、`review/` 同级的独立空文件夹，交付时必须存在且内部为空（包含隐藏项）；不放图片、占位文件、`.gitkeep` 或 `.DS_Store`，也不替代原有 `site/img/`。重跑时若该目录已有内容，先可恢复地归档到 `.codex-work/` 再保持为空；后续清理与白名单验收必须保留此目录。

#### 生成 URL 的原文保留与大小写保护

- 生成完成后，先在 `.codex-work/` 保存生成器介绍文件中四个 `All URL` 原始值，作为改名、复制和接入的比对基准；然后将它们原封不动保留在 `aduit/intro.md` 并复制到 App 固定 URL 注册表。暂不可访问、占位域名、格式异常或加载失败都不是改写理由，不探测真实地址，不等待正式域名，继续完成后续任务。
- 完整 URL 严格区分大小写并逐字符保留：协议、域名、路径、目录名、文件名、扩展名、查询参数的名称/值/顺序、片段、斜杠及百分号编码的原始写法均不得改变。不得使用 `toLowerCase()`、`toUpperCase()`、slug 化、自动格式化或 URI 解析后重新序列化来重写值；不得根据页面显示标题、Dart 标识或本地目录重新拼接地址。源码、JSON 或 HTML 必需的转义可以使用，但解码后交给 WebView 的字符串必须与原始值完全相同。
- 本地将 `AppListing/` 改为 `aduit/`、将 `Intro.md` 改为 `intro.md`，只涉及本地文件整理，绝不能对 `All URL` 做全局替换或大小写转换。协议 HTML 保持 `PrivacyPolicy.html`、`Terms&Conditions.html`、`Support.html` 的原始大小写与标点，不改成全小写文件名；页面内链接也按实际文件名保持大小写。
- 验收链为“生成器原始值 → `aduit/intro.md` → App 固定注册表 → Initialization/Settings 点击时交给 WebView 的实际字符串”。使用区分大小写的精确相等比较，不允许先转小写再比对；发现任一处变化，修复该复制/传递环节并复验，不反过来修改原始值以使错误通过。按第 11.3 节用无网络 stub/fake 核验，证据仅放 `.codex-work/`，不增加 `aduit/` 交付文件。
- 当前生成流程不替换域名。用户之后明确提供正式域名并要求替换时，只替换授权的域名部分；协议及其余路径、文件名、查询参数、片段和编码原样保留，不随新域名重新生成 URL。仅修复大小写不能证明服务器配置或可达性已经通过。

例如，原始路径为 `/BrandA/PrivacyPolicy.html` 时，不得改为 `/branda/privacypolicy.html`；`Terms&Conditions.html` 不得改为 `terms&conditions.html`。此例只说明大小写规则，不是当前项目的网址。


**错误隔离与继续执行**：不要用一条 `&&` 命令链把素材检查、Listing 生成、目录整理与 Remarks 串成全有或全无。分别运行并读取生成器 JSON、退出码与实际文件；`local_generation_complete` 仅表示介绍和页面已经生成，`media_review_errors`、`failures` 与正式发布就绪状态分别记录。退出码非零时先有限修复可修复的本地问题，保留已有产物；仅 Logo 缺失、照片许可、图片运行验证或外部网络失败不能跳过后续改名与 Remarks。正常交付仍必须满足原白名单；完全没有可解码品牌图时，允许先保留空的 `site/img/` 并移除缺图引用，记录 `logo.png` 缺失和目录契约未通过，继续生成 `aduit/intro.md`、四页正文与 `aduit/review/remarks.md`，不创建假图片或宣称白名单通过。开发期图片可以使用已有有效 AppIcon，或显式记录来源的 `.codex-work/development-brand.png`；不能仅凭它被命名为 `assets/logo.png` 就认定正式 Logo 通过。

本节在全部 App 实现、UI/资源精修、适用验证与第 11.9 节质量复核之后执行；质量复核必须实际执行并记录结果，但单项照片、许可、Logo 或运行环境外部失败可以保持 `Blocked`/`Not verified`，不把它们改写为通过，也不阻断本地材料生成；随后还须完成第 12.2 节 Review Remarks。仅对本节涉及的页面、随包同步与文件变更补充必要核验，不另开产品设计或审批。开发期仍提前把四个固定 HTML 页面（About Home、Privacy Policy、Terms & Conditions、Support）及其中合并的法律章节直接放到 `aduit/site/`，应用介绍放到 `aduit/intro.md`，供离线 WebView 使用；即使实际事实尚有缺口，也只在内部记录里标明，不把页面降格为带草稿水印、待填字段或未完成说明的预览稿。这些准备不等于提前执行最终 AppListing 生成、改名或目录清理。最终阶段仅在 AppListing 已改名为 `aduit/` 后以引导页替换生成的 About Home；不得提前替换、另建文件或因此推迟 URL 回接与 Review Remarks。

固定收尾路径：先验证安装器同步的完整远程 `ios-app-listing` checkout（Git 来源、`feature/1.2.1-A1` 分支和当前 revision），再只使用该目录的技能、脚本、引用和资源，以 `--no-deploy-about --no-sync-project-listing-urls` 本地生成最终 AppListing、`description` 与对应 About 页面 → 核对并修正 About 配色 → 将生成的 `AppListing/` 改名/整理为 `aduit/` → 立即新建空的 `aduit/imgs/` → 按第 12.1 节清理与核验 `site/` → **完整替换 `aduit/site/index.html` 并接入本地 Welcome 引导 WebView，完成引导页验收** → 将 `aduit/intro.md` 的四个 `All URL` 原样保存到固定 URL 注册表，协议通用文案只显示在清除成功后的 Initialization 页底部，Welcome 与引导页不含协议通用文案；Settings 只接入 Privacy Policy/Terms of Use/Support 三个 WebView 入口，再做定向回归（不探测或修复 URL）→ 按第 12.2 节生成 `aduit/review/remarks.md` → 核验完整目录白名单 → 将全部其他产物移入 `.codex-work/` 并从 `aduit/` 清除 → 确认 `AppListing/` 已不存在 → 最终报告。若远程 checkout 缺失、来源/分支/revision 不符或技能执行失败，保留证据并将 AppListing 阶段标为 `Blocked`，不得读取资料包中的 `ios-app-listing/` 副本，也不得手写等价页面。此流程不要求、查询、推测或替换域名；不调用域名查询或 About 部署接口，不创建、轮询部署任务，不做 DNS 或公开访问探测。

引导页验收时核对文案结构、内容布局和协议文案缺席；通过后才进行原始 URL 的注册及两个目标的绑定。

协议通用文案仅初始化页显示：欢迎页和引导页都不显示该文案；只在确认 Clear Data 并且清理成功后显示的 Initialization 页底部呈现。

**目录白名单验收**：最终 `aduit/` 的直接子项必须恰好是小写 `intro.md`、`imgs/`、`site/` 和 `review/`；`site/` 的直接子项必须恰好是 `index.html`、`PrivacyPolicy.html`、`Terms&Conditions.html`、`Support.html` 和 `img/`，`img/` 中只保留 `logo.png`；`review/` 中只保留 `remarks.md`；`imgs/` 必须为真实空目录，内部含隐藏项在内的子项数量为 0。大小写、标点和目录层级按此核对，检查包括隐藏项，不允许 `.DS_Store`、其他文件、目录或符号链接混入。最终四页分别为替换生成 About Home 后的引导页、Privacy Policy、Terms of Use 与 Support；免责及版权说明合并为现有法律页中的章节。AppListing 转移后先核对 `site/`，引导页替换和 Review Remarks 写入后再核对完整白名单；文件齐全且额外项为 0 才可标记交付目录验收完成。

页面所需 CSS 和确有用途的 JavaScript 内联到这四个 HTML 文件中，字体采用系统字体；About 页面如需图片仅引用 `img/logo.png`，但最终引导页须遵循下方的 Base64 图片内嵌要求。改写后的引导页不得依赖任何外置图片文件。在移出额外文件前先消除页面对外置 CSS、JS、字体、其他图片或旧路径的依赖，并复验章节锚点、相对链接和离线显示。不能只移动依赖文件而留下失效引用。已有 `aduit/html/`、报告、截图、备份及其他白名单外内容先移到项目根目录 `.codex-work/` 的独立归档位置并核对，不覆盖已有备份；不得将这些内容复制进 `site/` 或 `img/`。

1. **只使用远程 `ios-app-listing` 技能生成当前项目的 AppListing 与 About 页面**：完整读取安装器同步的 `Workflow resource root/ios-app-listing/SKILL.md` 及该目录中要求的全部 references、scripts、assets 和 validators，先核对其 Git `origin`、`feature/1.2.1-A1` 分支与当前 revision，再按技能检查实际 App、分类、选定描述样式、生成与验证。资料包不提供可执行的 AppListing 副本；不得使用旧安装或其他路径作为运行时来源。`description` 必须由当前智能体根据已实现的主题、功能和最终 UI 文案撰写，再通过远程技能实际支持的 `--authoring-json` 输入；不把脚本的默认文案当作已自行撰写，不虚构账号、社区、上传或 AI 功能。固定使用 `--no-deploy-about` 与 `--no-sync-project-listing-urls`，生成并验证本地产物；不调用域名查询、About 部署接口或线上访问工具。生成前确认 `assets/logo.png` 或 AppIcon 候选是真实可解码图片；如果正式 Logo 服务只返回生成网页或正式 Logo 超时，不能把网页保存为图片，先将已有有效 iPhone 品牌图归一化为 `assets/logo.png`，或创建仅供本地产物的 `unverified` 开发期品牌源并在 `.codex-work/` 记录，Listing/About 继续生成但不得称为正式品牌通过。若无可解码品牌图，保留远程技能的真实失败证据并按该技能的输出/校验结果处理，不得用手写或等价本地页面替代远程技能。远程技能缺失、来源/分支/revision 不符或同步失败时，将 AppListing 阶段标为 `Blocked`，提示重新运行安装器同步后再恢复，不读取其他本地副本、不执行自制生成器。
2. **保持真实文件契约、成品状态和协议边界**：技能输出文件为 `AppListing/Intro.md`、`AppListing/site/index.html`、`AppListing/site/img/logo.png`、`AppListing/site/PrivacyPolicy.html`、`AppListing/site/Terms&Conditions.html`、`AppListing/site/Support.html`，按实际大小写与标点核对；用户所说的 `intro.md` 对应这份介绍文件，最终目标统一为小写 `aduit/intro.md`。`aduit/site/` 最终严格只允许 `index.html`、`PrivacyPolicy.html`、`Terms&Conditions.html`、`Support.html` 和 `img/logo.png`；不得在 `site/` 下新增 Disclaimer、Content & Copyright Notice 或其他协议文件，若法律内容需要披露，应合并到这四个页面并保持可达链接。四页必须是完整、自然、彼此独立的成品文案；正文、标题、描述元数据、替代文本和无障碍标签不得出现 `Draft` 等页面状态标签、`WIP`、`TBD`、`TODO`、`Placeholder`、`Pending confirmation`、方括号填空项或作者/开发状态说明。真实产品功能名称以项目事实为据，不得用作页面状态说明。description、网页正文与最终截图执行第 6.6、11.4 节的英语及显示文案检查，不沿用技能模板里的技术术语、中文、框架名称或 `local`/`device`；固定文件名、机器字段和内部报告不作为页面正文展示。公开文案和法律陈述据实，联系地址不能靠推测；没有经确认的支持邮箱时不推断或生成 `support@<slug>.com`，省略对应联系区并在内部摘要标记公开法律审阅缺口。用自然英文准确描述 `Clear Data` 与隐私事实，不因关键词命中删掉必要披露。遇到校验冲突须记录对应规则与实际依据并针对性核验，不伪报所有技能校验通过，不为过词库而虚构功能或更改数据行为。
3. **About 配色与 Logo 必须一致**：站点的 `img/logo.png` 必须来自当前项目验收后的 `assets/logo.png`，核对文件来源与内容，不用技能自行选中的旧 AppIcon 或旧品牌图覆盖它。以第 2.5 节真实色块和主题/渐变映射作为依据，实际查看 About 的主题色、主按钮、链接、渐变和背景；品牌区域必须呈现协调的渐变与鲜明色彩，不沿用生成器默认的无关配色。不一致时直接替换 About 主题色及共享 CSS 令牌，再核验浅/深色表现、文字/控件对比度与全部站点页面。配色一致不要求逐像素同色，阅读表面可保留中性色。缺少正式 Logo 时按第 2.5 节在内部记录发布阻断，并继续可完成的本地整理；About 页面不加开发状态水印，不能以临时图标冒充正式配色验收。
4. **不设置域名或公开部署关卡**：生成的 URL/元数据保持技能产物原样；不得要求用户提供域名，不调用域名查询接口，不推测、替换、拼接或验证任何域名/公开主机。固定使用本地生成参数，不调用 About 部署接口、不创建或轮询部署任务、不做 DNS 或公开访问探测。记录 `AppListing generation: succeeded/failed` 与 `Delivery: Local only`；无公开 URL、域名或线上页面不阻断本地页面生成、改名和白名单核验，也不把生成的 URL 说成已上线或可访问地址。
5. **将生成目录改名为 `aduit`，明确替换旧介绍并保留审核目录**：把技能生成的 `AppListing/` 目录按可恢复方式改名/整理为项目根目录的 `aduit/`；若 `aduit/` 已存在，先把旧目录完整备份到 `.codex-work/`，并将其中既有 `review/` 目录安全暂存，避免随旧版替换而丢失，再整理新生成内容；不把新介绍追加到旧内容后。改名完成后立即按本节创建空的 `aduit/imgs/`，后续清理不得移除该目录。将 `Intro.md` 改名为小写 `aduit/intro.md`，保留四个 HTML 页面与 `img/logo.png`，清理其余生成文件。将暂存的 `review/` 恢复到新 `aduit/`；若没有既有目录，则在第 12.2 节创建。既有 `remarks.md` 在替换前另存可恢复副本，其他 review 文件移至 `.codex-work/`。`aduit/` 最终只能有 `intro.md`、空的 `imgs/`、`site/` 与 `review/`；`site/` 只能有四个 HTML 页面与 `img/logo.png`，`review/` 只能有 `remarks.md`。任何 CSS、JS、字体、截图、日志、报告、备份或其他生成文件必须移入 `.codex-work/`，不能保留在 `aduit/`。CSS/JS 应内联或由页面生成流程处理，不能因此增加白名单外文件。以文件清单、必要哈希、可读性和相对引用验证无遗漏，不能只转移首页而漏掉 Logo、Support 或协议。
6. **核验改名后的 `aduit/site/` 并清理多余内容**：以改名后的 `aduit/site/` 作为后续正文维护源，按第 7.6 节核验四个固定 HTML 页面及其合并法律章节、稳定文档注册、相对引用和离线显示，不让改名产生失效链接或两份不同版本。逐项核验 `aduit/intro.md`、四个 HTML 文件和 `img/logo.png` 的存在、内容、Logo 配色与离线显示；不执行线上访问检查。将改名前生成的临时输出和开发记录移入 `.codex-work/`，不得创建或保留 `aduit/html/`。改名/核验失败时保留可恢复备份并修复，未解决时如实说明；清理失败不谎报成功、不删除唯一副本。

**改名后的品牌复验**：按第 10.4 节将当前正式 Logo 同步到 `aduit/site/img/logo.png` 并核对哈希，实际查看本地四页的 Logo/品牌封面与渐变，修正旧图片引用；同时确认 App 的桌面图标、原生启动品牌图和 Welcome/Initialization 页面未被生成器或后续构建改回旧图。站点不新增独立封面图片文件，保持原白名单。

**页面发布就绪检查**：最终生成或修改四个 HTML 页面后，运行 `python3 <skill-root>/scripts/validate_site_publication_ready.py --site-dir <project-root>/aduit/site`。修复正文、标题、描述元数据或无障碍标签中的草稿/占位内容，并确认页面不是空壳。若缺少真实联系或其他法定事实，只在内部摘要标记公开法律审阅未完成；继续本地生成和接入，不在页面中显示待补字段，也不谎称法律材料已完成。

**AppListing 改名后：首页引导页替换、接入与验收**：仅在最终 `AppListing/` 已按白名单改名/整理为 `aduit/` 后执行，并且必须在 URL 回接和 Review Remarks 之前完成。将用户提到的 `aduit/index.html` 精确落实为现有站点文件 `aduit/site/index.html`：完全替换其中生成器的 About Home 正文，不在 `aduit/` 根目录另建 `index.html`，不新增站点文件。依据当前项目的源码、配置、实际页面与 `aduit/intro.md` 生成 3–5 张真实介绍卡片；全部可见文字使用英语，准确介绍项目实际用途和功能，不固定主题、不虚构能力，CSS 主题色、渐变与整体视觉风格须匹配当前 App 及 Logo 色板。页面必须是小于 256 KiB（262,144 字节）的单一自包含 HTML 文件：全部 HTML、CSS、JavaScript 在该文件中，使用系统字体，不加载外部脚本、样式、字体或其他运行时资源；装饰优先用 CSS 绘制，若采用 SVG 图片素材也须编码为 Base64 data URI，现有 Terms/Privacy 链接属于用户主动导航而非资源依赖。每张需在引导页显示的图片（包括 Logo 与卡片配图）均须编码为 Base64 data URI，直接内嵌在同一个 `aduit/site/index.html` 中；浏览器/WebView 渲染时从 data URI 解码并显示。`site/img/logo.png` 仍按交付白名单保留，但引导页显示 Logo 时使用其内嵌数据，不从该相对路径加载。不得让 `index.html` 引用 Flutter assets、工程内相对图片路径、`file://` 路径或远程图片 URL，也不得通过 CSS `url()`、`srcset` 等方式绕开内嵌要求。可为页面生成压缩或缩放后的图片副本以满足体积限制，但不能覆盖原素材；包含所有 Base64 图片内容后，完整 UTF-8 HTML 文件仍须严格小于 262,144 字节，不得放宽上限。验收时逐个解码 Base64，确认图像格式、尺寸与可读性，并在无网络 WebView 中确认每张图片实际显示。

页面需设置 `viewport-fit=cover`，用 `env(safe-area-inset-top)` 与 `env(safe-area-inset-bottom)` 处理刘海/Dynamic Island 和底部安全区。一次只展示一张卡片并自动轮播，提供可点击且有可访问名称的分页圆点；支持手机与桌面，适配指定尺寸并尽量一屏展示，不得有内容重叠、控件被遮挡或文案/按钮被裁切。尊重 `prefers-reduced-motion`：减少动态时关闭自动轮播及非必要运动，分页点仍可手动切换。引导页不含协议通用文案；Welcome 不显示协议通用文案或 Terms/Privacy 页脚链接；通用文案只在 Clear Data 确认成功后出现的 Initialization 页底部显示，两个目标分别可点击。引导页验收须确认协议文案缺席、安全区和内容布局正常，不得挤压或遮挡 `Continue`。协议原始 URL 的注册及 Initialization 中两个目标的绑定在通过引导页专项验收后的 URL 回接阶段完成。

引导页及其余三个 HTML 页中所有展示图片按第 6.3 节使用统一圆角；包括 Base64 内嵌 Logo、卡片配图与其他图片，图片及容器同步设置 `border-radius`，容器使用 `overflow: hidden` 实际裁剪。可以适当加入与 App 统一的主题色细边框，轮播和响应式布局中不得露出尖角、溢出或遮挡主体。样式继续内联，不引入外部资源或新增文件；圆角不通过修改原始 Logo 的 Alpha 实现。引导页在四个指定视口验收实际裁剪效果，其余协议页沿用既定不探测真实 URL 的验证边界。

将该同一 `aduit/site/index.html` 作为 Flutter 欢迎/引导阶段实际显示的本地随包 WebView 页面，不维护第二份 HTML。页面使用的图片已内嵌为 Base64 data URI，因此中转或随包加载时不依赖项目内部图片资源，也不发起图片网络请求。提供 WebView 的原生 `AppBridge.postMessage` 消息通道：收到唯一消息 `continue` 时调用现有进入 App 流程；Web 页面 Continue 按钮必须调用以下函数，不增删分支或改写其行为：

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

两行居中放在 Initialization 页底部安全区内，不截断文本；第二行的 `Terms of Use` 与 `Privacy Policy` 分别可点击，使用 All URL 中对应的原始值，`and` 为普通文本。不能只改 About HTML、字符串文件或规划说明而不更新 App 实际显示。不增加勾选或额外确认，不保存个人协议同意记录，也不将按钮等同于媒体授权或 ATT 同意；Terms 正文应与这项实际提示一致。Settings 同一页面只提供三个链接：Privacy Policy、Terms of Use、Support；Welcome 引导页作为站点 `index.html` 交付，但不写入 Settings 且不含协议页脚。三个 Settings 入口使用 All URL 中对应的原始值，第四个 About Home URL 仍保存在固定注册表但不提供 Settings 入口。无论 URL 格式是否正常、目标是否可达，均直接复制，不校验、规范化、补全、替换或删去；WebView 加载失败时显示可读错误、返回与有限重试，不能阻断 Welcome、Settings、清除数据或其他 App 功能，也不回退到开发期本地预览页面。回归时按第 7.2 节核验 Initialization 的完整原文、显式换行、底部安全区和两个独立链接，并确认 Welcome、HTML 引导页和原生启动页均无该文案；用不发起网络请求的 WebView stub/fake 核验注册值、实际入口 URL、Settings 不含引导页、失败/返回状态和主流程，不访问或探测真实目标；完成后继续 Review Remarks，不重开总体 UI 审批。

7. **完成 AppListing 与协议入口阶段**：报告远程 `ios-app-listing` checkout 的来源、分支与 revision、当前智能体撰写的 description、About 配色核验和修正结果、`AppListing/` 生成与改名/整理为 `aduit/` 的结果、站点白名单核验及额外文件移出位置，以及四个 URL 的原样接入和定向回归结果。若远程技能缺失或执行失败，报告 `AppListing: Blocked` 及证据，不写“真实替代流程”，不使用资料包副本或手写页面。备份放在 `.codex-work/` 并说明可恢复位置。远程阶段成功后，随后必须继续第 12.2 节生成 Review Remarks，再做完整白名单核验；不在此阶段提前宣布最终交付。不询问用户意见、继续许可或交付确认。

### 12.2 App Review Remarks

在第 12.1 节完成后，为当前 Flutter App 生成审核备注，并写入 `aduit/review/remarks.md`。若目录不存在则创建；若文件已存在，先将旧版保存到 `.codex-work/` 中的可恢复位置再替换。此文件是 `aduit/` 的唯一审核备注产物，不新增其他审核材料到该目录。备注全程使用英语，字符总数不超过 4,000；使用 Markdown 标题组织内容，不使用 `**` 粗体标记，不输出分析、推理、免责声明或中文。

先读取当前实际存在的介绍文件：AppListing 尚未规范化时为 `AppListing/Intro.md`；完成第 12.1 节转移/小写规范化后，以白名单中的 `aduit/intro.md` 为准。若输入材料写作 `aduit/Intro.md`，先核对实际大小写，不得因大小写不符漏读或另造重复文件。提取应用名称、用途、类别、功能、用户生成内容、账号、计费、权限和其他提审信息；必要时查看源码、配置、测试记录和现有审核材料核实事实。还要逐字核对 App 固定协议 URL 配置与 `All URL` 四项映射，但不发起网络请求；审核备注可说明这些配置的协议页地址尚未验证可达性，不得将其描述为在线服务或可用页面。不得把开发期占位文案当成最终事实。输出以 `# App Review Remarks` 开始，随后用普通英文标签列出 `App name`、`Purpose`、`Category`、`User-generated content`、`Account`、`Billing`、`Permissions` 和 `Other submission details`；未知值统一按缺失规则标注。之后按以下七项顺序使用清晰的 Markdown 标题：`## 1. Actual Device`、`## 2. Test Devices and Operating Systems`、`## 3. App Purpose, Intended Audience, and Problem Solved`、`## 4. Setup Steps`、`## 5. External Services`、`## 6. Regional Differences`、`## 7. Unique Value`。

1. Actual Device：写入用户已提供的实际运行设备记录 `iPhone 17 Pro Max, iOS 26.5`，不得自行添加或替换机型、系统版本、视频、账号或测试结果。此项按用户明确提供的记录填写，不得把模拟器结果称为真机结果。
2. Test Devices and Operating Systems：从有明确已完成自测记录且符合本项目 iPhone-only 范围的 iPhone 中随机抽取 2–5 台，不重复；候选不足时只报告确有记录的设备，不编造机型凑数。当前提供的合格样本为 `iPhone 15 Pro, iOS 18.6` 与 `iPhone 13, iOS 17.7.1`，故本项目应从这两台中抽样（若取 2 台则均列出）；同一请求列出的 iPad（第 10 代）因项目严格限定 iPhone 而不得列入。当前记录说明合格 iPhone 已完成启动、主要功能与权限提示自测且未发现阻塞问题；只复述记录明确覆盖的测试类别。不要照搬通用模板中的注册/登录或计费测试声明：当前产品无账号/登录功能，写 `No such feature` 且不得声称测试过此流程；计费/内购须先核对实际实现与测试记录，确无此功能才写 `No such feature`，存在时仅报告有记录的实际测试，未知时写 `Not provided; pending confirmation.`。
3. App Purpose, Intended Audience, and Problem Solved：只依据 `aduit/intro.md` 和当前实现说明产品用途、主要用户及解决的实际问题，不夸大。
4. Setup Steps：按审核人员可执行的顺序写安装/启动、点击最终引导页的 `Continue` 进入主要功能（仅改名前开发预览可用 `Enter`）、分别打开摄像机/相册/麦克风的真实入口并触发权限提示、权限拒绝后的可用路径、`Settings` 中 `Clear Data` 的入口与二次确认及成功后显示 Initialization 页；写明 ATT 是否出现及其实际触发条件，无追踪时依据事实说明不显示 ATT 提示。注册/登录、验证码、邀请码或测试账号仅在实际存在时说明路径；不存在时写 `No such feature`。计费或内购步骤仅在实际存在时提供，并按审核人员可执行顺序说明；无需特殊设置时明确写 `No additional setup is required.`
5. External Services：逐项列出 App 实际使用的外部服务、平台、API、分析工具、支付服务、云服务及第三方 SDK，并说明各自用途；另以独立标签列出 `Advertising`、`AI services`、`Third-party SDKs`。每项均明确给出状态：有证据确认使用时写服务与用途，确认未使用时写 `Not used.`，未知或未提供信息时写 `Not provided; pending confirmation.`；不能把未知写成未使用。说明 App 实际配置的协议页链接及用途，并指出可达性未经验证，不得据此声称相关网站/服务已上线。只列真实外部依赖，不暴露自有 package、内部模块、目录或实现细节；仅供本地生成的 URL/占位地址不算线上服务。不得查询、要求或推断域名。
6. Regional Differences：核对功能、内容、价格、权限、可用性及审核流程的地区差异。确认无差异时必须使用精确英文句子 `All regions are the same.`；确认存在差异时逐项说明具体地区与内容；事实不足时写 `Not provided; pending confirmation.`，不能默认所有地区相同或猜测。最终备注全程英语，因此不得将该固定英文句子替换为中文。
7. Unique Value：用一句具体、可信且与当前功能一致的话概括与同类产品的差异和用户价值，避免空泛营销语。

基本信息与七项内容须全部包含。只使用源码、配置、实际测试记录或用户明确提供的已确认事实；不能编造设备、系统版本、测试、视频、账号、服务、SDK、地区支持或功能。缺失信息统一写 `Not provided; pending confirmation.`；已确认不存在的能力写 `No such feature` 或 `Not used.`。不适用的账号、注册、登录、订阅、内购和受限功能应明确说明没有对应能力及可执行路径；未知的计费状态不得擅自标为不存在。不要把 iPhone 模拟器测试写成真机测试。完成后检查全文仅为英语、字符数不超过 4,000、基本信息及七项顺序/标题准确、无 `**`、不出现 H5、B-side 或内部 package/模块信息，并与 App、实际存在且大小写正确的介绍文件及审核事实一致；不等待用户审批或补充意见。

### 12.3 App Store 隐私披露、EULA 与提交材料

1. 根据实际数据流填写 App Store Connect 隐私披露，覆盖 App 本身、第三方 SDK 与 App 功能内 WebView。纯设备端处理的照片与录音不因访问系统权限就自动属于 Apple 定义的“收集”；若其他数据离开设备，按 Apple 当前定义分别判断用途、保留、关联身份与追踪，不直接套用 `Data Not Collected`。
2. App 内必须提供隐私政策入口；最终 Entry/Settings 目标按 `aduit/intro.md` `All URL` 原样配置，不执行公开部署或可达性验证。目标地址可达性须记为未验证，不通过回归测试发送网络请求，也不自行修复地址。若正式提交仍需要公开可访问的隐私政策 URL，单独记录为未验证发布前置条件；公开链接、真实开发者身份或联系渠道缺失时保留本地产物并记录缺口，不编造信息、不要求用户提供域名，也不因此停止其他本地实现。
3. 明确采用 Apple 标准 EULA，或在确需自定义 EULA 时依据 Apple 当前最低条款完整准备并正确配置；App 内 `Terms of Use` 不自动等同于 App Store 的自定义 EULA，不能宣称四份 HTML 已覆盖所有提交协议。
4. 审核说明必须写明无需登录，并给出从最终引导页点击 `Continue` 到达主要功能的步骤；另列摄像机/相册/麦克风的具体入口与用途、权限拒绝后的可用路径、清除本地数据的入口/二次确认/成功后显示 Initialization 的结果，以及 ATT 适用性和触发条件。无追踪时明确无需 ATT 弹窗。截图、描述、年龄分级与二进制一致，不展示未实现能力或用户私有素材。
5. 检查最终构建的权限声明、隐私清单、SDK 要求、公开政策、协议版本、支持链接与审核说明。已知错误须修复，证据不足须明确标记；正式提交流程遵守用户已有授权与实际平台能力，不因宣称“协议完整”跳过 Apple 当前验证。

官方核对来源：开发与正式发布时重新查看适用版本并记录核对日期，不能假定本文永远覆盖后续政策变动。

- [Apple 用户隐私与数据使用／ATT](https://developer.apple.com/app-store/user-privacy-and-data-use/)
- [App Review Guidelines：2.5.14、5.1.1 与 5.1.2](https://developer.apple.com/app-store/review/guidelines/)
- [系统相册选择器与最小权限](https://developer.apple.com/documentation/photokit/selecting-photos-and-videos-in-ios)
- [App Store 隐私披露](https://developer.apple.com/app-store/app-privacy-details/)
- [隐私清单](https://developer.apple.com/documentation/bundleresources/privacy-manifest-files)
- [第三方 SDK 要求](https://developer.apple.com/support/third-party-SDK-requirements/)
- [自定义 EULA 最低条款](https://www.apple.com/legal/internet-services/itunes/dev/minterms/)
