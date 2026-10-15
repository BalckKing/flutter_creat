## 12. App Store、法律与 About 材料

思维导图整体确认并开始实现后，所有公开材料从实际实现生成，并且 App 内公开文案保持英语：

**发布范围固定为 iOS iPhone。** AppListing、About、Support、协议、商店文案、预览和截图均只面向 iPhone；不出现其他设备版本、兼容性声明、商店分发选项或下载入口。最终核对构建产物与商店配置时，只有 iPhone 可用；若后台无法验证这一点，明确记为未验证，不将其描述为已限制完成。

- `Privacy Policy`：完整说明摄像机、相册选择/读取与麦克风的具体用途、授权时机、拒绝/撤销后的行为，照片和录音的本地处理、保存位置、保留、删除、临时文件、备份边界与安全措施；按第 8.5 节准确说明 `Clear Data` 二次确认后清除 App 自有媒体、记录、偏好和缓存，成功后返回欢迎页，失败可重试，系统相册原件、App 外导出文件、现存备份和系统权限不由此删除或重置。说明实际的第三方 SDK、WebView 请求、诊断/网络元数据、接收方和 ATT/追踪结论。App 无需账号、不要求邮箱输入或身份认证数据、不上传用户媒体；若真实支持渠道接收用户主动发送的信息，按第 0.3 节准确披露，不将无账号扩大为未经核验的“所有数据绝不离开设备”。包含真实开发者身份、联系渠道、生效日期、政策变更及适用的隐私权利说明，不声称保存个人协议同意记录。
- `Terms of Use`：完整说明功能范围、内容来源、许可、可用性、用户责任和禁止滥用，以及拍摄/录音应尊重他人权利、本地媒体保存与删除、用户需自行备份的重要内容、服务限制和联系方式；不得将这些条款变为隐蔽免责。准确描述点击 `Enter` 即可进入，`Clear Data` 须二次确认、无法通过 App 撤销，清理成功后返回欢迎页；不加入不存在的退出、登录、会员、上传或社交功能，也不宣称 `Enter` 代表勾选协议、授予系统权限或同意 ATT。
- `Disclaimer` 章节：在 `Terms&Conditions.html` 或 `PrivacyPolicy.html` 中根据主题提供仅供参考的说明，以及适当的专业意见排除条款。
- `Content & Copyright Notice` 章节：在现有法律页中列出随包素材来源、许可、署名、条款 URL 以及更正/删除联系渠道；区分随包内容和用户本地拍摄/导入/录音，不声称拥有用户媒体，不把私有媒体列入公开清单。
- About Home 与 Support：使用清晰、友好的产品介绍和支持说明，通过同一 WebView 页面展示，不把 About Home 误写成 App 主首页。

开发期根据实际实现持续维护应用介绍、About、支持页和协议正文，四个 HTML 页面始终保持完整、自然、可独立阅读的成品文案，不显示 `Draft` 等页面状态标签、待补提示或作者备注。缺失的开发者、联系、司法辖区等事实不得猜测，也不得以填空语写入页面；仅在内部生成摘要中记录具体缺口，并标记公开法律审阅未完成。页面生成、接入与本地校验不因此卡住；这不等于宣称法律材料已可公开发布。全流程不依赖域名、公开部署或线上访问。App 功能、UI、资源和第 11.9 节质量复核完成后，依次执行第 12.1 节本地生成 AppListing 与 About 页面、核对 Logo 配色并整理为 `aduit/`，按第 12.1 节的改名后协议回接要求更新 Entry/Settings 的 WebView URL，最后按第 12.2 节依据已核实事实生成英文 Review Remarks。质量复核的完成含义是已执行适用检查、修复可修复问题并记录外部失败；图库许可或正式 Logo 仍为 `Blocked` 时，不得把相应质量项写成通过，但不能阻断这些本地材料步骤。均由智能体自主完成，不新增询问关卡；不要求或查询域名，不公开部署。

### 12.1 AppListing 与本地 About 页面生成、改名为 aduit 并清理

**错误隔离与继续执行**：不要用一条 `&&` 命令链把素材检查、Listing 生成、目录整理与 Remarks 串成全有或全无。分别运行并读取生成器 JSON、退出码与实际文件；`local_generation_complete` 仅表示介绍和页面已经生成，`media_review_errors`、`failures` 与正式发布就绪状态分别记录。退出码非零时先有限修复可修复的本地问题，保留已有产物；仅 Logo 缺失、照片许可、图片运行验证或外部网络失败不能跳过后续改名与 Remarks。正常交付仍必须满足原白名单；完全没有可解码品牌图时，允许先保留空的 `site/img/` 并移除缺图引用，记录 `logo.png` 缺失和目录契约未通过，继续生成 `aduit/intro.md`、四页正文与 `aduit/review/remarks.md`，不创建假图片或宣称白名单通过。开发期图片可以使用已有有效 AppIcon，或显式记录来源的 `.codex-work/development-brand.png`；不能仅凭它被命名为 `assets/logo.png` 就认定正式 Logo 通过。

本节在全部 App 实现、UI/资源精修、适用验证与第 11.9 节质量复核之后执行；质量复核必须实际执行并记录结果，但单项照片、许可、Logo 或运行环境外部失败可以保持 `Blocked`/`Not verified`，不把它们改写为通过，也不阻断本地材料生成；随后还须完成第 12.2 节 Review Remarks。仅对本节涉及的页面、随包同步与文件变更补充必要核验，不另开产品设计或审批。开发期仍提前把四个固定 HTML 页面（About Home、Privacy Policy、Terms & Conditions、Support）及其中合并的法律章节直接放到 `aduit/site/`，应用介绍放到 `aduit/intro.md`，供离线 WebView 使用；即使实际事实尚有缺口，也只在内部记录里标明，不把页面降格为带草稿水印、待填字段或未完成说明的预览稿。这些准备不等于提前执行最终 AppListing 生成、改名或目录清理。

固定收尾路径：使用指定技能以 `--no-deploy-about --no-sync-project-listing-urls` 本地生成最终 AppListing、`description` 与对应 About 页面 → 核对并修正 About 配色 → 将生成的 `AppListing/` 改名/整理为 `aduit/` → 按第 12.1 节清理与核验 `site/` → 将 `aduit/intro.md` 的四个 `All URL` 原样保存到固定 URL 注册表，Entry 接入 Terms/Privacy 两条文本链接、Settings 只接入 Privacy Policy/Terms of Use/Support 三个 WebView 入口，About Home 不加入 Settings，再做定向回归（不探测或修复 URL）→ 按第 12.2 节生成 `aduit/review/remarks.md` → 核验完整目录白名单 → 将全部其他产物移入 `.codex-work/` 并从 `aduit/` 清除 → 确认 `AppListing/` 已不存在 → 最终报告。此流程不要求、查询、推测或替换域名；不调用域名查询或 About 部署接口，不创建、轮询部署任务，不做 DNS 或公开访问探测。

**目录白名单验收**：最终 `aduit/` 的直接子项必须恰好是小写 `intro.md`、`site/` 和 `review/`；`site/` 的直接子项必须恰好是 `index.html`、`PrivacyPolicy.html`、`Terms&Conditions.html`、`Support.html` 和 `img/`，`img/` 中只保留 `logo.png`；`review/` 中只保留 `remarks.md`。大小写、标点和目录层级按此核对，检查包括隐藏项，不允许 `.DS_Store`、其他文件、目录或符号链接混入。四页分别对应 About Home、Privacy Policy、Terms of Use 和 Support；免责及版权说明合并为现有法律页中的章节。AppListing 转移后先核对 `site/`，Review Remarks 写入后再核对完整白名单；文件齐全且额外项为 0 才可标记交付目录验收完成。

页面所需 CSS 和确有用途的 JavaScript 内联到这四个 HTML 文件中，字体采用系统字体，图片仅引用 `img/logo.png`；在移出额外文件前先消除页面对外置 CSS、JS、字体、其他图片或旧路径的依赖，并复验章节锚点、相对链接和离线显示。不能只移动依赖文件而留下失效引用。已有 `aduit/html/`、报告、截图、备份及其他白名单外内容先移到项目根目录 `.codex-work/` 的独立归档位置并核对，不覆盖已有备份；不得将这些内容复制进 `site/` 或 `img/`。

1. **使用指定技能生成当前项目的 AppListing 与 About 页面**：完整读取 `Workflow resource root/ios-app-listing/SKILL.md` 及其中要求的 `references/output-contract.md`、`references/privacy-ai-rules.md`，按技能检查实际 App、分类、选定描述样式、生成与验证。`description` 必须由当前智能体根据已实现的主题、功能和最终 UI 文案撰写，再通过技能实际支持的 `--authoring-json` 输入；不把脚本的默认文案当作已自行撰写，不虚构账号、社区、上传或 AI 功能。固定使用 `--no-deploy-about` 与 `--no-sync-project-listing-urls`，生成并验证本地产物；不调用域名查询、About 部署接口或线上访问工具。生成前确认 `assets/logo.png` 或 AppIcon 候选是真实可解码图片；如果正式 Logo 服务只返回生成网页或正式 Logo 超时，不能把网页保存为图片，先将已有有效 iPhone 品牌图归一化为 `assets/logo.png`，或创建仅供本地产物的 `unverified` 开发期品牌源并在 `.codex-work/` 记录，Listing/About 继续生成但不得称为正式品牌通过。若仍无任何可解码图片，保留失败证据并使用等价本地页面流程完成 `aduit/`，不因素材阻断而结束。技能缺失时先查找已知可用位置；仍不可用则按本节生成同等本地产物、记录具体限制，并继续可执行的改名/转移步骤，不询问用户或声称使用了缺失技能。
2. **保持真实文件契约、成品状态和协议边界**：技能输出文件为 `AppListing/Intro.md`、`AppListing/site/index.html`、`AppListing/site/img/logo.png`、`AppListing/site/PrivacyPolicy.html`、`AppListing/site/Terms&Conditions.html`、`AppListing/site/Support.html`，按实际大小写与标点核对；用户所说的 `intro.md` 对应这份介绍文件，最终目标统一为小写 `aduit/intro.md`。`aduit/site/` 最终严格只允许 `index.html`、`PrivacyPolicy.html`、`Terms&Conditions.html`、`Support.html` 和 `img/logo.png`；不得在 `site/` 下新增 Disclaimer、Content & Copyright Notice 或其他协议文件，若法律内容需要披露，应合并到这四个页面并保持可达链接。四页必须是完整、自然、彼此独立的成品文案；正文、标题、描述元数据、替代文本和无障碍标签不得出现 `Draft` 等页面状态标签、`WIP`、`TBD`、`TODO`、`Placeholder`、`Pending confirmation`、方括号填空项或作者/开发状态说明。真实产品功能名称以项目事实为据，不得用作页面状态说明。description、网页正文与最终截图执行第 6.6、11.4 节的英语及显示文案检查，不沿用技能模板里的技术术语、中文、框架名称或 `local`/`device`；固定文件名、机器字段和内部报告不作为页面正文展示。公开文案和法律陈述据实，联系地址不能靠推测；没有经确认的支持邮箱时不推断或生成 `support@<slug>.com`，省略对应联系区并在内部摘要标记公开法律审阅缺口。用自然英文准确描述 `Clear Data` 与隐私事实，不因关键词命中删掉必要披露。遇到校验冲突须记录对应规则与实际依据并针对性核验，不伪报所有技能校验通过，不为过词库而虚构功能或更改数据行为。
3. **About 配色与 Logo 必须一致**：站点的 `img/logo.png` 必须来自当前项目验收后的 `assets/logo.png`，核对文件来源与内容，不用技能自行选中的旧 AppIcon 或旧品牌图覆盖它。以第 2.5 节真实色块和主题/渐变映射作为依据，实际查看 About 的主题色、主按钮、链接、渐变和背景；品牌区域必须呈现协调的渐变与鲜明色彩，不沿用生成器默认的无关配色。不一致时直接替换 About 主题色及共享 CSS 令牌，再核验浅/深色表现、文字/控件对比度与全部站点页面。配色一致不要求逐像素同色，阅读表面可保留中性色。缺少正式 Logo 时按第 2.5 节在内部记录发布阻断，并继续可完成的本地整理；About 页面不加开发状态水印，不能以临时图标冒充正式配色验收。
4. **不设置域名或公开部署关卡**：生成的 URL/元数据保持技能产物原样；不得要求用户提供域名，不调用域名查询接口，不推测、替换、拼接或验证任何域名/公开主机。固定使用本地生成参数，不调用 About 部署接口、不创建或轮询部署任务、不做 DNS 或公开访问探测。记录 `AppListing generation: succeeded/failed` 与 `Delivery: Local only`；无公开 URL、域名或线上页面不阻断本地页面生成、改名和白名单核验，也不把生成的 URL 说成已上线或可访问地址。
5. **将生成目录改名为 `aduit`，明确替换旧介绍并保留审核目录**：把技能生成的 `AppListing/` 目录按可恢复方式改名/整理为项目根目录的 `aduit/`；若 `aduit/` 已存在，先把旧目录完整备份到 `.codex-work/`，并将其中既有 `review/` 目录安全暂存，避免随旧版替换而丢失，再整理新生成内容；不把新介绍追加到旧内容后。将 `Intro.md` 改名为小写 `aduit/intro.md`，保留四个 HTML 页面与 `img/logo.png`，清理其余生成文件。将暂存的 `review/` 恢复到新 `aduit/`；若没有既有目录，则在第 12.2 节创建。既有 `remarks.md` 在替换前另存可恢复副本，其他 review 文件移至 `.codex-work/`。`aduit/` 最终只能有 `intro.md`、`site/` 与 `review/`；`site/` 只能有四个 HTML 页面与 `img/logo.png`，`review/` 只能有 `remarks.md`。任何 CSS、JS、字体、截图、日志、报告、备份或其他生成文件必须移入 `.codex-work/`，不能保留在 `aduit/`。CSS/JS 应内联或由页面生成流程处理，不能因此增加白名单外文件。以文件清单、必要哈希、可读性和相对引用验证无遗漏，不能只转移首页而漏掉 Logo、Support 或协议。
6. **核验改名后的 `aduit/site/` 并清理多余内容**：以改名后的 `aduit/site/` 作为后续正文维护源，按第 7.6 节核验四个固定 HTML 页面及其合并法律章节、稳定文档注册、相对引用和离线显示，不让改名产生失效链接或两份不同版本。逐项核验 `aduit/intro.md`、四个 HTML 文件和 `img/logo.png` 的存在、内容、Logo 配色与离线显示；不执行线上访问检查。将改名前生成的临时输出和开发记录移入 `.codex-work/`，不得创建或保留 `aduit/html/`。改名/核验失败时保留可恢复备份并修复，未解决时如实说明；清理失败不谎报成功、不删除唯一副本。

**改名后的品牌复验**：按第 10.4 节将当前正式 Logo 同步到 `aduit/site/img/logo.png` 并核对哈希，实际查看本地四页的 Logo/品牌封面与渐变，修正旧图片引用；同时确认 App 的桌面图标、启动品牌图和 Loading/Entry 封面未被生成器或后续构建改回旧图。站点不新增独立封面图片文件，保持原白名单。

**页面发布就绪检查**：最终生成或修改四个 HTML 页面后，运行 `python3 <skill-root>/scripts/validate_site_publication_ready.py --site-dir <project-root>/aduit/site`。修复正文、标题、描述元数据或无障碍标签中的草稿/占位内容，并确认页面不是空壳。若缺少真实联系或其他法定事实，只在内部摘要标记公开法律审阅未完成；继续本地生成和接入，不在页面中显示待补字段，也不谎称法律材料已完成。
**About 完成后、Review Remarks 前的欢迎页文案与协议入口回接**：在 About/AppListing 本地生成、配色核对并整理为 `aduit/` 后、生成 `remarks.md` 前执行。先读取 `aduit/intro.md` 的 `All URL` 区域，逐字复制其中四个 URL 到 App 的固定 URL 注册表，按文档名称对应绑定。将值作为原始字符串保存和传递，不以 URI 预解析/有效性检查作为复制、保存或导航前置条件。此时实际替换 App 的 Entry 欢迎页底部协议文案，严格分为以下两行，显式在 `our` 后换行，无句末句号：

```text
By continuing, you agree to our
Terms of Use and Privacy Policy
```

两行居中放在底部安全区内，不遮挡 `Enter`，不截断文本；第二行的 `Terms of Use` 与 `Privacy Policy` 分别可点击，使用 All URL 中对应的原始值，`and` 为普通文本。不能只改 About HTML、字符串文件或规划说明而不更新 App 实际显示。不增加勾选或额外确认，不保存个人协议同意记录，也不将继续使用等同于媒体授权或 ATT 同意；Terms 正文应与这项实际提示一致。Settings 同一页面只提供三个链接：Privacy Policy、Terms of Use、Support；About Home 保留为 `index.html` 交付页面，但不写入 Settings。三个 Settings 入口使用 All URL 中对应的原始值，第四个 About Home URL 仍保存在固定注册表但不提供 Settings 入口。无论 URL 格式是否正常、目标是否可达，均直接复制，不校验、规范化、补全、替换或删去；WebView 加载失败时显示可读错误、返回与有限重试，不能阻断 `Enter`、Settings、清除数据或其他 App 功能，也不回退到开发期本地预览页面。回归时按第 7.2 节核验完整原文、显式换行、底部安全区和两个独立链接，并用不发起网络请求的 WebView stub/fake 核验注册值、实际入口 URL、Settings 不含 About Home、失败/返回状态和主流程，不访问或探测真实目标；完成后继续 Review Remarks，不重开总体 UI 审批。

7. **完成 AppListing 与协议入口阶段**：报告使用的技能或真实替代流程、当前智能体撰写的 description、About 配色核验和修正结果、`AppListing/` 生成与改名/整理为 `aduit/` 的结果、站点白名单核验及额外文件移出位置，以及四个 URL 的原样接入和定向回归结果。备份放在 `.codex-work/` 并说明可恢复位置。随后必须继续第 12.2 节生成 Review Remarks，再做完整白名单核验；不在此阶段提前宣布最终交付。不询问用户意见、继续许可或交付确认。

### 12.2 App Review Remarks

在第 12.1 节完成后，为当前 Flutter App 生成审核备注，并写入 `aduit/review/remarks.md`。若目录不存在则创建；若文件已存在，先将旧版保存到 `.codex-work/` 中的可恢复位置再替换。此文件是 `aduit/` 的唯一审核备注产物，不新增其他审核材料到该目录。备注全程使用英语，字符总数不超过 4,000；使用 Markdown 标题组织内容，不使用 `**` 粗体标记，不输出分析、推理、免责声明或中文。

先读取规范路径 `aduit/intro.md`（AppListing 生成的 `Intro.md` 已在第 12.1 节规范化为小写文件名），提取应用名称、用途、类别、功能、用户生成内容、账号、计费、权限和其他提审信息；必要时查看源码、配置、测试记录和现有审核材料核实事实。还要逐字核对 App 固定协议 URL 配置与 `All URL` 四项映射，但不发起网络请求；审核备注可说明这些配置的协议页地址尚未验证可达性，不得将其描述为在线服务或可用页面。不得把开发期占位文案当成最终事实。输出以 `# App Review Remarks` 开始，随后用普通英文标签列出 `App name`、`Purpose`、`Category`、`User-generated content`、`Account`、`Billing`、`Permissions` 和 `Other submission details`；未知值统一按缺失规则标注。之后按以下七项顺序使用清晰的 Markdown 标题（例如 `## 1. Real Device`）：

1. Real Device：写入用户已提供的真实设备记录 `iPhone 17 Pro Max, iOS 26.5`。不得自行添加或替换机型、系统版本、视频、账号或测试结果。
2. Test Devices and Operating Systems：从用户提供且符合 iPhone-only 范围的已完成自测记录中随机抽取 2–5 个设备，不重复；不纳入任何非 iPhone 设备。当前提供的有效样本为 `iPhone 15 Pro, iOS 18.6` 和 `iPhone 13, iOS 17.7.1`，因此当前样本量为 2。用户提供的记录声明这些设备已完成启动、主要功能、权限提示及计费流程自测且没有阻塞问题；不得扩写为其他未提及的测试。当前产品按既定要求没有账号或注册/登录功能，因此这些流程写 `No such feature`，不宣称已测试。计费/内购状态必须检查当前源码与配置：若实际存在，备注可按用户提供的记录说明已完成计费测试；若不存在则写 `No such feature`，不得声称测试过不存在的流程。
3. App Purpose, Intended Audience, and Problem Solved：只依据 `aduit/intro.md` 和当前实现说明产品用途、主要用户及解决的实际问题，不夸大。
4. Setup Steps：按审核人员可执行的顺序写安装/启动、点击 `Enter` 进入主要功能、分别打开摄像机/相册/麦克风的真实入口并触发权限提示、权限拒绝后的可用路径、`Settings` 中 `Clear Data` 的入口与二次确认及成功后返回欢迎页；写明 ATT 是否出现及其实际触发条件，无追踪时依据事实说明不显示 ATT 提示。计费或内购步骤仅在实际存在时提供，并按审核人员可执行顺序说明。按当前产品要求说明无需注册、登录、验证码、邀请码或测试账号；不存在的项目写 `No such feature`，无需特殊设置时明确写 `No additional setup is required.`
5. External Services：列出实际使用的外部平台、API、分析工具、支付服务、云服务及第三方 SDK，并逐项写用途；另设 `Advertising`、`AI services`、`Third-party SDKs` 三行，分别明确写 `Used: [confirmed service and purpose]`、`Not used.` 或 `Not provided; pending confirmation.`。将 App 当前配置的四个 WebView 协议目的地描述为已配置的链接及其用途，并明确目的地址可达性未验证；不得据此声称对应网站或服务已上线。只列项目实际依赖的外部服务，不暴露自有私有 package、内部模块、目录或实现细节。不得把仅供本地生成的 URL/占位地址说成已公开上线；需要公开地址但未确认时按缺失规则标注，不查询或要求域名。
6. Regional Differences：核对功能、内容、价格、权限、可用性和审核流程的地区差异；确认无差异时必须原样写 `All regions are the same.`；事实不足时写 `Not provided; pending confirmation.`，不能猜测。
7. Unique Value：用一句具体、可信且与当前功能一致的话概括与同类产品的差异和用户价值，避免空泛营销语。

基本信息与七项内容须全部包含。只使用源码、配置、实际测试记录或用户明确提供的已确认事实；不能编造设备、系统版本、测试、视频、账号、服务、SDK、地区支持或功能。缺失信息统一写 `Not provided; pending confirmation.`；已确认不存在的能力写 `No such feature` 或 `Not used.`。不适用的账号、注册、登录、订阅、内购和受限功能应明确说明没有对应能力及可执行路径；未知的计费状态不得擅自标为不存在。不要把 iPhone 模拟器测试写成真机测试。完成后检查全文仅为英语、字符数不超过 4,000、七项顺序正确、无 `**`、不出现 H5、B-side 或内部 package/模块信息，并与 App、`aduit/intro.md` 和审核事实一致；不等待用户审批或补充意见。

### 12.3 App Store 隐私披露、EULA 与提交材料

1. 根据实际数据流填写 App Store Connect 隐私披露，覆盖 App 本身、第三方 SDK 与 App 功能内 WebView。纯设备端处理的照片与录音不因访问系统权限就自动属于 Apple 定义的“收集”；若其他数据离开设备，按 Apple 当前定义分别判断用途、保留、关联身份与追踪，不直接套用 `Data Not Collected`。
2. App 内必须提供隐私政策入口；最终 Entry/Settings 目标按 `aduit/intro.md` `All URL` 原样配置，不执行公开部署或可达性验证。目标地址可达性须记为未验证，不通过回归测试发送网络请求，也不自行修复地址。若正式提交仍需要公开可访问的隐私政策 URL，单独记录为未验证发布前置条件；公开链接、真实开发者身份或联系渠道缺失时保留本地产物并记录缺口，不编造信息、不要求用户提供域名，也不因此停止其他本地实现。
3. 明确采用 Apple 标准 EULA，或在确需自定义 EULA 时依据 Apple 当前最低条款完整准备并正确配置；App 内 `Terms of Use` 不自动等同于 App Store 的自定义 EULA，不能宣称四份 HTML 已覆盖所有提交协议。
4. 审核说明必须给出无需登录的 `Enter` 路径、三项媒体功能的具体入口与用途、权限拒绝后的可用路径、清除本地数据的入口/二次确认/欢迎页返回，以及 ATT 适用性和触发条件；无追踪时明确无需 ATT 弹窗。截图、描述、年龄分级与二进制一致，不展示未实现能力或用户私有素材。
5. 检查最终构建的权限声明、隐私清单、SDK 要求、公开政策、协议版本、支持链接与审核说明。已知错误须修复，证据不足须明确标记；正式提交流程遵守用户已有授权与实际平台能力，不因宣称“协议完整”跳过 Apple 当前验证。

官方核对来源：开发与正式发布时重新查看适用版本并记录核对日期，不能假定本文永远覆盖后续政策变动。

- [Apple 用户隐私与数据使用／ATT](https://developer.apple.com/app-store/user-privacy-and-data-use/)
- [App Review Guidelines：2.5.14、5.1.1 与 5.1.2](https://developer.apple.com/app-store/review/guidelines/)
- [系统相册选择器与最小权限](https://developer.apple.com/documentation/photokit/selecting-photos-and-videos-in-ios)
- [App Store 隐私披露](https://developer.apple.com/app-store/app-privacy-details/)
- [隐私清单](https://developer.apple.com/documentation/bundleresources/privacy-manifest-files)
- [第三方 SDK 要求](https://developer.apple.com/support/third-party-SDK-requirements/)
- [自定义 EULA 最低条款](https://www.apple.com/legal/internet-services/itunes/dev/minterms/)
