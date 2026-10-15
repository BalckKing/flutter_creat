# iOS App Listing Skill：拒审预防与条件校验方案

> 本文档定义：在现有 skill 职责范围内，如何参照 `validate_privacy_output.py`（AI 隐私）的模式，  
> 对 **隐私/法律 HTML** 与 **提审文案** 做「有信号 → 专项校验 → 不通过不交付」的拒审预防。  
>  
> 数据来源：[拒审记录统计-汇总分析.md](./拒审记录统计-汇总分析.md)

> 状态说明（2026-05-22）：本文包含“当前实现”与部分“历史规划”内容。  
> 当前以 `SKILL.md`、`references/output-contract.md`、`references/privacy-ai-rules.md` 以及实际脚本行为为准。  
> 已落地的校验器包括：`validate_review_wording.py`、`validate_privacy_output.py`、`validate_ugc_legal_output.py`、`validate_iap_legal_output.py`、`validate_permission_privacy.py`、`validate_terms_ai_output.py`、`validate_listing_claims.py`、`validate_support_output.py`、`validate_listing_contract.py`。

---

## 1. 背景与边界

### 1.1 Skill 负责的两块内容

| 板块 | 产出 | 与拒审的关系 |
|------|------|----------------|
| **法律 / 隐私 HTML** | `PrivacyPolicy.html`、`Terms&Conditions.html`、`Support.html` | 主要影响 **1.2**、**5.1.1** 等「书面说明」类问题 |
| **提审文案 / 站点** | `Intro.md`、`index.html` 等 | 主要影响 **2.3** 元数据不实、部分 **2.1** 说明不足 |

### 1.2 能预防 vs 不能预防

| 能辅助预防（文案层） | 不能由本 skill 替代 |
|----------------------|---------------------|
| 隐私/条款缺段、表述过泛、与 inspect 能力明显不符 | App 内无举报、IAP 买不了、ATT 不弹 |
| Intro 吹了没有的功能 | Connect 年龄分级未勾选 |
| IAP 码与文案不一致 | **4.3** 模板同质化、账号级欺诈 |
| Support 页缺邮箱/占位 FAQ | 审核 Notes 七项、录屏、测试账号 |

**原则：** 校验脚本保证「**该写的写全、写的和项目信号一致**」；**不保证**审核员满意或 App 已实现功能。

### 1.3 统一模式（对标 AI 隐私）

```text
inspect_app.py → app_inspect.json（signals / capabilities）
       ↓
生成 Privacy / Terms / Intro / Support / index（payload 或 Agent 填槽）
       ↓
按信号调用 validate_*（仅相关项；无信号则跳过）
       ↓
全部通过 → 交付 AppListing；否则重写对应文件并 rerun
```

**已有范例：**

```bash
# ai_signals.active = true 时必跑
python3 scripts/validate_privacy_output.py \
  --inspect-json /tmp/app_inspect.json \
  --privacy-html .../AppListing/site/PrivacyPolicy.html
```

---

## 2. 拒审类型 → 校验策略总览

| Guideline（汇总） | 高频表现 | Skill 校验手段 | 优先级 |
|-------------------|----------|----------------|--------|
| **1.2** UGC | 缺 EULA、举报、过滤、24h、拉黑 | `validate_ugc_legal_output.py` | P0 |
| **5.1.1** 隐私 | 相册/相机/跟踪等说明不清 | `validate_permission_privacy.py` | P0 |
| **2.1(b)** / IAP | IAP 说明、credits 用途（书面） | `validate_iap_legal_output.py` | P0 |
| **AI** | 隐私与条款 AI 段不全 | `validate_privacy_output.py` + `validate_terms_ai_output.py` | P1 |
| **2.3** 元数据 | 描述功能在 App 中找不到 | `validate_listing_claims.py` | P1 |
| **1.5** / **2.1** | Support 信息不足 | `validate_support_output.py` | P2 |
| **—** | 目录/文件名漂移 | `validate_listing_contract.py`（每次必跑） | P0 |
| **2.1** 审核材料 | Notes 七项、录屏 | 另见 §6「提审资料模板」（非 validate） | P2 |
| **2.3.6** 年龄分级 | Connect 未勾选 UGC | 人工清单 / 未来 Connect 检查 | 范围外 |
| **4.3(a)** | 包相似 | 产品策略 | 范围外 |
| **审核观感 / 2.3 / 4.3** | 文案暴露「本地模拟、离线假数据」 | `validate_review_wording.py`（禁用词） | **P0** |

---

## 3. 审核不利表述（禁用词）— 全局规则

### 3.0.1 为什么要单独做

App Store 审核要求产品呈现为**可用的真实应用**。用户可见文案若出现 `mock`、`local data`、`offline only` 等字样，易被理解为：

- 功能依赖本地假数据或未接后端；
- 处于演示 / 开发态；
- 与商店描述、隐私声明中的「在线服务」叙事矛盾。

此类问题**不**一定对应某一条 Guideline 编号，但会叠加 **2.3**（不实/误导）、**4.3**（粗糙模板感）风险，且与汇总表中「审核找不到功能」「元数据与体验不符」同类。

**本 skill 要求：** 所有 **AppListing 交付物**中的用户可见文案（及写入 App 的字符串若由本 skill 管线产出）**不得**出现下列禁用表述；生成后**每次必跑**校验脚本。

### 3.0.2 禁用词列表（初版）

规则维护于 `references/review-banned-phrases.md`（建议实现为 JSON 词表 + 例外表）。

**短语 / 词（英文，大小写不敏感，按词边界或完整短语匹配）：**

| 类型 | 禁用项 |
|------|--------|
| 单词 | `mock` |
| 单词 | `offline`（见例外） |
| 短语 | `mock data` |
| 短语 | `local data` |
| 短语 | `local storage` |
| 短语 | `device storage` |
| 短语 | `offline only` |
| 单词 | `local`（**仅**在描述数据/存储/实现时禁用；见 §3.0.4 例外） |

**禁用原因（统一口径）：** 不得向用户或审核员暴露「本地模拟数据、仅离线、设备本地库」等产品实现细节；对外应使用**服务、账户、内容、同步、云端**等产品化表述。

### 3.0.3 适用范围

| 必检 | 说明 |
|------|------|
| `Intro.md` | Description、Sub Title、Keywords 全文 |
| `site/index.html` | 去 HTML 后的可见文案 |
| `site/Support.html` | FAQ、标题、按钮、空态说明 |
| `site/PrivacyPolicy.html` | 面向用户的正文（少用实现细节用语） |
| `site/Terms&Conditions.html` | 面向用户的正文 |
| **建议同步约束** | App 内 UI 文案（按钮、Toast、空态、页面标题）— 若不由本 skill 生成，应在 reskin 规范中引用同一词表 |

**不检：** 源码路径、注释、`app_inspect.json`、脚本名、远程 manifest 键名。

### 3.0.4 合法例外（避免误杀）

以下**不**视为违规（校验器应用例外表）：

| 例外 | 示例 |
|------|------|
| 法律管辖 | `local laws`、`local regulations` |
| 一般英语 | `local community`（非数据含义）、`locale` |
| 已约定替换 | 生成阶段即改写，不依赖例外兜底 |

**隐私页替代表述（生成规范）：**

| 避免 | 建议 |
|------|------|
| data stored in local storage on your device | preferences and account settings saved in the app |
| mock / sample / test data | 不写；无数据时用「暂无内容」类中性文案 |
| offline only | 不写；若需说明无网，用 limited connectivity without implying fake data |
| device storage | storage used by the app / on your device（仅说明权限时简短带过，不强调「本地库」） |

### 3.0.5 与拒审类型的关系

| 关联 | 说明 |
|------|------|
| **2.3** | 商店/站点文案暗示在线能力，页面或 App 文案却写 offline/mock → 审核认为不实 |
| **4.3** | 批量 reskin 常漏改占位文案，易残留 mock/local → 加重「未完成产品」印象 |
| **5.1.1** | 隐私页过度强调「仅本地、不上传」可能与实际上传行为冲突（需与 inspect 一致） |

### 3.0.6 生成侧要求（写入 SKILL / output-contract）

- 生成 Intro、站点页、法律页时，**默认词表生效**；clause 库与 FAQ 模板**不得**含禁用词。
- Agent 重写时：校验失败应返回 `matched_phrase` + `file` + `suggested_rewrite`（脚本输出）。

---

## 4. 条件校验器规格（拟新增 / 已有）

### 4.1 拟新增：`validate_review_wording.py`（审核不利表述 · 每次必跑）

| 项 | 说明 |
|----|------|
| **触发** | **每次**生成 AppListing 后（无信号门槛） |
| **对象** | `Intro.md`；`site/index.html`、`Support.html`、`PrivacyPolicy.html`、`Terms&Conditions.html` |
| **检查** | 命中 §3.0.2 禁用词表 → 失败；应用 §3.0.4 例外表 |
| **输出** | `{ "valid": false, "errors": [{ "file", "phrase", "excerpt", "hint" }] }` |
| **参考** | 业务规则：禁止暴露本地模拟实现细节 |
| **局限** | 不扫描 App 源码；不检中文同义词（可二期加「模拟」「离线」「本地数据」等） |

**建议实现：** `references/review-banned-phrases.json` + 共享 `scripts/review_wording_common.py` 供测试复用。

**优先级：** 与 `validate_listing_contract` 同为 **P0**，且在 claims/UGC 校验之前执行（先挡明显不利表述）。

---

### 4.2 当前已实现：`validate_privacy_output.py`（AI 隐私）

| 项 | 说明 |
|----|------|
| **触发** | `ai_signals.active == true` |
| **对象** | `site/PrivacyPolicy.html` |
| **检查** | AI 专段、发送数据类型、接收方、用户同意、用途、第三方同等保护等（见 `references/privacy-ai-rules.md`） |
| **加强** | 当命中 `ai_signals.review_profile.needs_face_data_clauses = true` 时，还会检查 AI Preview / face-data 的章节标题、selected photo、facial features、provider、retention、deletion、禁止 identity verification / biometric profiling 等内容 |
| **配套** | Terms 侧由 `validate_terms_ai_output.py` 负责 |

---

### 4.3 当前已实现：`validate_ugc_legal_output.py`（1.2 UGC 书面）

| 项 | 说明 |
|----|------|
| **触发** | `privacy_signals.user_content == true`，或 `feed` / `post_creation` / `messaging` / `profile` 等 capability `score >= 1.0`（与契约一致） |
| **对象** | `PrivacyPolicy.html`、`Terms&Conditions.html`；可选 `Support.html`（FAQ 含举报指引） |
| **Privacy 宜含** | user content / community、收集与展示 UGC、moderation 概述 |
| **Terms 宜含** | 用户行为规范、禁止内容、**report** / 举报、**block** / 拉黑、内容过滤或审核、**24 hour** / timely 处理、违反条款后果、联系开发者 |
| **Terms 宜含（可选加强）** | EULA / Terms acceptance、匿名发布风险、建议 **18+** 分级表述（Obex 类拒审） |
| **参考** | [拒审记录统计-汇总分析.md](./拒审记录统计-汇总分析.md) §三.3、Kavinor / Gelira / Obex |
| **局限** | **不验证** App 内是否真有举报按钮、过滤服务是否上线 |

**规则来源建议：** `references/apple-review-clauses.md` 中 `guideline_1_2_ugc` 词条 + 单元测试固定样例句。

---

### 4.4 当前已实现：`validate_iap_legal_output.py`（IAP / 虚拟货币书面）

| 项 | 说明 |
|----|------|
| **触发** | `privacy_signals.payments == true` 或 `iap_codes` 非空 或 `recharge` capability 活跃 |
| **对象** | `Terms&Conditions.html`、`PrivacyPolicy.html`、`Intro.md` |
| **Terms/Privacy 宜含** | in-app purchase / Apple、虚拟币或 credits/coins、不可退款或退款限制、使用范围 |
| **Terms 宜含（按需）** | 不可提现 / not redeemable for cash（对应 Sorel 类「coins 是否可兑现」） |
| **Intro 宜含** | `Description` 中自然出现 `purchase / credits / coins / virtual goods` 等 IAP 语义 |
| **参考** | 汇总 §三.1、Deryx / Elinova / Jeniva |
| **局限** | 不验证沙盒购买、Paid Apps Agreement、审核员能否找到 IAP 入口 |

---

### 4.5 当前已实现：`validate_permission_privacy.py`（5.1.1 权限）

按权限**分别**触发子规则（可一个脚本多 mode）：

| 触发（inspect） | Privacy 宜含 | 对应拒审 |
|---------------|--------------|----------|
| `photo_library` 或 `camera` | 相册/照片访问、用途、是否上传用户内容 | Obex 5.1.1(ii) |
| `microphone` 或 `speech_recognition` | 麦克风/语音、用途 | 通用 5.1.1 |
| `tracking` | 跟踪、广告标识、第三方分析 | ATT 相关说明（弹窗本身不在此验） |
| `location_*` | 定位数据、用途 | 5.1.1 |

**当前加强：** 当命中 AI Preview / face-data 高风险分支时，还会检查相机 / 相册 / add-to-library 权限是否与 selected photo、consent、save-to-Photos 链路绑定。

---

### 4.6 当前已实现：`validate_terms_ai_output.py`

| 项 | 说明 |
|----|------|
| **触发** | `ai_signals.active == true` |
| **对象** | `Terms&Conditions.html` |
| **宜含** | AI 输出限制、免责声明、用户责任、第三方模型、不得依赖 AI 做医疗/法律等专业建议（按产品调整） |
| **加强** | 当命中 AI Preview / face-data 高风险分支时，还会强制检查 visual styling preview allowed use、identity verification / face recognition / biometric 限制、legal / medical / safety-critical 禁用用途 |
| **与** | `validate_privacy_output.py` 成对执行 |

---

### 4.7 当前已实现：`validate_listing_claims.py`（2.3 元数据与证据）

| 项 | 说明 |
|----|------|
| **触发** | 每次生成（或 `claimable_features` 非空） |
| **对象** | `Intro.md` 的 Description/Keywords、`index.html` 正文（去 HTML 后） |
| **思路** | ① 高风险词表（如 `1v1 video call`、`AI try-on`）若出现，必须在 `claimable_features` 或 classification 中有对应能力；② 禁止 unsupported superlatives（契约已有，脚本化） |
| **参考** | Geniva「元数据描述功能找不到」、Ivolora 无关关键词 |
| **局限** | 无法验证截图；需维护词表与 capability 映射 |

---

### 4.8 当前已实现：`validate_support_output.py`（Support 页）

| 项 | 说明 |
|----|------|
| **触发** | 每次生成 |
| **对象** | `site/Support.html` |
| **宜含** | `support_email` 与 inspect 一致、FAQ 与能力相关、无 `lorem` / `placeholder` / `TBD` |
| **加强** | AI Preview / face-data 高风险分支下，必须包含 AI Preview 工作方式与 camera / photo-library / add-to-library 权限原因 FAQ |
| **参考** | Avivion 1.5（Support URL 无效需在 Connect 填对 URL；本脚本保证页面内容可用） |

---

### 4.9 拟新增：`validate_listing_contract.py`（每次必跑）

| 项 | 说明 |
|----|------|
| **触发** | 每次生成 |
| **对象** | 整个 `AppListing/` 目录 |
| **检查** | 固定白名单；`Intro.md` 章节顺序；无多余文件 |
| **与拒审** | 间接：避免 Support / Terms 路径错误导致审核打不开页 |

---

## 5. 生成后校验流程（建议写入 SKILL.md）

```text
1. inspect_app.py → app_inspect.json
2. classify + validate_app_listing_classification
3. 生成 AppListing（render 或 Agent）
4. 校验（按序）：
   a. validate_listing_contract.py          # 始终：固定目录
   b. validate_review_wording.py            # 始终：禁用 mock/local/offline 等
   c. validate_support_output.py            # 始终
   d. validate_listing_claims.py            # 始终
   e. validate_privacy_output.py            # if ai_signals.active
   f. validate_terms_ai_output.py            # if ai_signals.active
   g. validate_ugc_legal_output.py           # if user_content
   h. validate_iap_legal_output.py           # if payments / iap_codes
   i. validate_permission_privacy.py         # per permission flags
5. 任一失败 → 仅重写失败文件对应章节 → 重跑相关 validate
6. validate_site_layout.py                  # P4 固定 HTML 后增加
```

---

## 6. 与模板池 / clause 库的关系（P3）

| 层级 | 作用 | 与 validate 关系 |
|------|------|------------------|
| **clause 库** | 按信号组装 UGC/IAP/权限/AI 标准段落 | 提供「应写入」的正文来源 |
| **布局模板** | 10+ 套 Terms 版式随机 | 不改变章节有无 |
| **validate_* ** | 生成后守门 | 检查 clause 是否真正落入 HTML/Markdown |

**流程：** `select_terms_template` → `compose_terms_content`（选 clause_ids）→ `render` → `validate_*`。

章节有无由 **evidence 决定**（与「仅随机布局」一致），validator 检查 **clause 要点是否出现**。

---

## 7. 不在 validate 内、但建议单独交付（提审资料）

针对 **2.1 Information Needed**（kivo / Pelivo / Berina 等），skill 可另生成（不强制进固定白名单，或放 `AppListing/review/` 待业务确认）：

| 产物 | 内容 |
|------|------|
| `ReviewNotes.md`（示例名） | 真机录屏说明、测试设备、产品用途、登录方式、演示账号、IAP 入口步骤、第三方服务列表 |
| 按 inspect 勾选 | 有 UGC → 注明需录屏举报/EULA；有 IAP → 注明沙盒账号与购买路径 |

**性质：** 辅助运营粘贴到 App Store Connect Notes，**不是** HTML 校验器。

---

## 8. 明确不做（避免范围蔓延）

| 拒审 / 事项 | 原因 |
|-------------|------|
| **4.3(a)** 包相似 | 二进制与产品设计 |
| **2.1(a)** 崩溃、无限加载 | 运行时 QA |
| **2.1(b)** IAP 逻辑 bug、token 为空 | 客户端代码 |
| **账号级欺诈**（Neovion） | 账号与商务策略 |
| **2.3.6** Connect 年龄分级 | App Store Connect 配置 |
| ATT 是否弹窗 | 需在真机测；validator 最多检查隐私是否提到 tracking |

---

## 9. 实施阶段建议

建议按以下顺序实施：

| 阶段 | 校验 / 拒审相关交付 |
|------|---------------------|
| **P0** | `validate_listing_contract.py`；**`validate_review_wording.py` + `references/review-banned-phrases.md`**；`references/apple-review-clauses.md` |
| **P3** | `legal-clauses/`（模板正文预检禁用词）+ `validate_ugc_legal` + `validate_iap_legal` + `validate_permission_privacy` |
| **P1** | `validate_terms_ai_output` 或扩展 AI 校验；`validate_listing_claims` 初版 |
| **P4** | `validate_site_layout.py`（布局错乱，非 Guideline 条号但影响审核观感） |
| **P2+** | `ReviewNotes.md` 生成模板；plist 与隐私用途一致性（可选）；禁用词中文扩展 |

**建议实现顺序：**  
`listing_contract` → **`review_wording`** → `ugc_legal` → `iap_legal` → `permission_privacy` → `terms_ai` → `listing_claims` → `support` → `review_notes模板`

---

## 10. 验收标准（本方案）

1. 每种 `validate_*` 有对应 `tests/test_validate_*.py`，且 **无信号时不误报**（`review_wording` 为始终执行）。  
2. 用 [拒审记录统计-汇总分析](./拒审记录统计-汇总分析.md) 中典型包型各至少 1 个 fixture 用例。  
3. **禁用词：** 含 `mock data` 的 Intro 样例必须失败；含 `local laws` 的 Terms 样例必须通过。  
4. `SKILL.md` / 使用文档中列出「生成后必跑 / 条件跑」的脚本表及禁用词原则。  
5. 失败时 JSON 输出 `errors[]` 可指导 Agent 重写（与 `validate_privacy_output` 一致）。  

---

## 11. 相关文档

| 文档 | 用途 |
|------|------|
| [拒审记录统计-汇总分析.md](./拒审记录统计-汇总分析.md) | 拒审原因与优先级 |
| [iOS应用上架文案Skill使用文档.md](./iOS应用上架文案Skill使用文档.md) | 当前 skill 用法 |
| `references/output-contract.md` | 条件章节契约 |
| `references/privacy-ai-rules.md` | AI 隐私规则（已有） |
| `references/review-banned-phrases.md` | **拟新增** 禁用词与例外表（实现 `validate_review_wording` 时落地） |

---

## 12. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-05-19 | 初稿：拒审映射、条件校验器规格、流程与实施顺序 |
| 2026-05-19 | 新增 §3 审核不利表述（禁用词）及 `validate_review_wording.py` |
