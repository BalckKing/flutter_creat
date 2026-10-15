# 通用 iOS AppListing Skill 项目适配改进方案

## 1. 目标与边界

当前 Skill 面向任意 Flutter / Swift iOS 项目，不能把某个项目名称、行业、功能、供应商或法律政策写成全局默认值。目标是让 App Store 文案、启动引导页、隐私政策、用户协议和 Support 都由目标项目的可核验证据驱动；证据不足时给出待确认项，不用看似合理的通用话术补齐。

本方案最初用于定义改进方向和验收标准；当前已按其中的项目事实档案、模板随机选择和证据绑定部分完成实现，不改变 `AppListing/` 固定输出结构。

适用范围：任意 iOS 项目；文中的 Pinfi 只用于说明可复现的问题，不构成默认配置或硬编码规则。

## 2. 本次 Pinfi 结果暴露的通用缺陷

Pinfi 仅作为问题样例，不作为 Skill 的专属配置：

- **能力分类把词面匹配当成产品能力。** 日记模型的 `location` 字段和示例故事里的 `map` 被误判成设备定位能力，进而污染引导页、隐私政策和 Terms。
- **能力字典没有覆盖产品自身核心实体。** 项目核心是旅行、日记、照片、时间线、备份；现有生成流程主要依据 profile、community、location 等固定分类，导致核心价值没有进入 onboarding。
- **引导卡片使用通用占位逻辑。** “Welcome / Location Tools / Ready to Begin”满足卡片数量，但不等于有项目适配；缺少证据与实际用户流程之间的对应校验。
- **隐私事实抽取偏向权限，不足以描述数据生命周期。** 能识别相机、相册和头像网络域名，却未充分纳入日记、旅行、导入媒体、本地持久化、用户主动分享、备份导出的数据流。
- **品牌 / 项目元数据没有统一来源优先级。** 自动生成的副标题可能与项目已确认的商店元数据不一致；Support 邮箱虽能从源码找到，但尚未确认可用，不能等同已验证联系渠道。
- **静态校验只检查结构和部分禁词。** 能确认 HTML 有卡片、桥接方法和分页点，却不能发现“功能文案虽合法但项目没有该功能”。

## 3. 总体方案：先构建项目事实档案，再生成文案

在生成任何面向用户的内容之前，建立一份统一的 `project_profile`（运行时中间数据，可放在 `/tmp` 或流水线临时目录，不增加默认 AppListing 输出文件）。它是文案与法律页共用的唯一事实输入，包含证据、置信度和待确认状态。

建议结构：

```json
{
  "identity": {
    "app_name": {"value": "Project name", "status": "confirmed", "evidence": [".../Info.plist"]},
    "subtitle": {"value": "Existing approved subtitle", "status": "confirmed", "evidence": ["operator input"]}
  },
  "product": {
    "purpose": {"value": "What users use the app for", "status": "confirmed", "evidence": ["docs/...", "lib/.../screen.dart"]},
    "features": [
      {"id": "journal_entry", "label": "Create and revisit journal entries", "status": "confirmed", "evidence": ["...view...", "...repository..."]}
    ],
    "user_flows": []
  },
  "data_flows": [
    {"data": "Imported photos", "source": "user selection", "processing": "on-device", "storage": "app container", "recipient": null, "status": "confirmed", "evidence": ["..."]}
  ],
  "unknowns": [],
  "conflicts": []
}
```

Schema 字段应可扩展，而不是把所有应用强行映射进少数固定行业类目。每个用于输出的事实都可以追溯到项目文件或操作者确认。

## 4. 证据来源优先级与冲突处理

### 4.1 来源优先级

从高到低建议采用：

1. 操作者本轮明确确认的事实及显式 authoring JSON；
2. 项目内当前有效的产品 / 数据 / 法律说明文档（排除 `AppListing/` 旧生成物、归档、构建输出）；
3. 可达的用户界面、路由、调用关系和实际业务逻辑；
4. 平台权限说明、隐私 manifest、StoreKit catalog；
5. 依赖声明、孤立源码符号、字符串和示例数据，仅作为候选线索。

低层证据不得推翻高层明确事实；如源代码与项目说明明显冲突，记录冲突并请求确认，不通过选择更方便的一项继续发布。

### 4.2 每条证据的判定状态

统一区分：

- `confirmed`: 有直接证据，且未发现冲突；
- `candidate`: 有弱线索，但未证明实际用户可达或运行；
- `unknown`: 证据不足；
- `conflict`: 来源相互矛盾；
- `confirmed_absent`: 已明确确认项目不具备该功能 / 数据流。

不得把 `unknown` 当作 `false`，也不得把“代码里出现词语”当作 `confirmed`。

## 5. 能力识别与产品核心表达

### 5.1 将词面命中改成上下文证据

能力分类必须结合来源类型、用户可达性和操作语义：

- 记录对象字段 `entry.location`、用户手填地点，不等于 GPS、定位权限、地图或附近搜索；
- 静态示例文本出现 “map”“trip”“community” 不足以确认对应能力；
- 依赖存在不等于 SDK 被初始化或实际处理数据；
- 菜单 / 路由候选需确认可达，并检查调用是否进入实际功能；
- 定位能力要求位置权限、CoreLocation / 定位服务调用，或明确可达的地图 / nearby 产品流程等强证据。弱词面命中只记 candidate。

### 5.2 从项目实体与操作抽取可扩展功能

除了通用分类，扫描器应允许从项目内界面与业务对象提取项目特有实体和动作，例如：

- 对象：日记、旅行、照片、保存的筛选条件；
- 动作：创建、编辑、搜索、筛选、收藏、分享、备份、恢复、删除；
- 表面：Journal、Albums、Timeline、Me 等实际页面。

抽取结果由当前 agent 根据证据归纳成用户语言，不直接把内部类名、数据库字段或检测器标签展示给用户。通用能力词库用于召回候选，不能直接充当最终产品分类或文案模板。

### 5.3 核心价值选择

- 先确定一个有证据支持的产品用途，再选 2–4 个用户真正可执行的核心流程；
- 排序依据为用户可达性、核心流程地位和项目说明，而非命中数量或固定分类顺序；
- 若没有足够证据生成 3 张有意义的卡片，不得用 “Explore available features” 等空泛内容凑数，应要求补充项目说明或输出需审阅状态。

## 6. Onboarding 与 App Store 文案生成规则

- 每张卡片应绑定 `project_profile.features[]` 中的已确认事实，并保留内部事实 ID，供渲染前校验追溯；ID 和证据不进入最终 HTML。
- 第一张说明产品解决什么需求，后续卡片展示不同核心操作；结束卡可简洁引导 Continue，但不得占用名额伪装成产品功能。
- 3–5 张卡片的数量要求不应压过真实性；允许在事实不足时停止发布 / 要求补充，而非生成虚构卡片。
- 标题、副标题、类别、品牌色优先使用项目中已确认的当前元数据；若来源互相矛盾或元数据缺失，显式列入确认清单，不随机生成“品牌副标题”。
- Continue 作为底部固定视觉主操作，移动端全宽、触控高度至少 60px；桌面可以限制最大宽度，但仍保持清晰的主按钮视觉层级。
- Onboarding 的 claim validator 应检查每个可见功能短语均可映射到已确认事实；不只检查 HTML 结构或是否存在轮播。

## 7. Privacy / Terms 的事实驱动生成

### 7.1 使用数据生命周期，而非功能类别推条款

每项数据分别记录：收集来源、是否由用户主动提交、设备端 / 服务器处理、存储位置、接收方、用途、保留期限、删除方式、用户可控行为。Privacy 页面根据已确认数据流生成章节，不从权限名称或功能类别推断上传和共享。

例如，相册权限只证明系统访问路径，不证明照片上传；分享 API 只证明用户可以调用系统分享面板，不证明运营方或某个社交平台收到数据；网络域名需确认其服务角色和实际传输数据后，才描述为 recipient。

### 7.2 网络目的地与第三方接收方

- 每个实际请求域名都要分类为 first-party / third-party / OS service / user-selected destination / unknown；
- 记录请求对应的数据类别和目的；只在项目代码可明确确认时从调用上下文自动抽取，否则由操作者确认；
- 缺少接收方分类时允许生成并部署审阅版；不得凭域名名称猜供应商、数据用途、处理地点或合同保护；
- 头像、地图、支付、分析等请求分别建模，不用一个 `network_hosts` 列表笼统代替数据流。

### 7.3 Legal unknown 与发布门槛

- 法律页中只呈现已确认的实际事实；不得写“联系运营方获取尚未制定的政策”来假装完成政策，也不能把待确认提示当最终法律文本；
- 未知的运营主体、司法辖区、儿童受众、保留政策、实际 recipient、AI 处理方式等输出为审核提醒，不由通用 Skill 自动设置发布 blocker；
- 本地生成和 About 部署均必须清晰输出 `legal_review_errors` / unknowns，供运营在正式公开法律文本和商店提交前确认；这些审核项不等同于技术校验失败，部署状态另由 `failures` / `deployment_ready` 表示。
- 用户确认内容写入 `legal.confirmed` authoring 数据后重新生成，Privacy、Terms、Support 与 App Store 文案从同一事实档案读取，防止不同页面口径冲突。

### 7.4 避免法律章节“模板惯性”

每条条款都需要触发条件和事实来源。没有对应能力 / 数据处理时，不生成章节；“通用限制责任”一类涉及法律效力的固定条款也应列为模板默认条款并单独审阅，不因常见就默认适用于所有司法辖区。

## 8. Validator 体系改造

新增或强化以下校验：

1. **Project fact coverage**：检查所有 onboarding / Intro / Privacy / Terms / Support 的具体声明是否能映射到确认事实；
2. **Unsupported claim**：如无定位服务证据，不允许 “Location Tools”“nearby”“GPS” 等声明；以实体与上下文区分手填地点；
3. **Core-feature omission review**：项目档案中标记为核心的功能需在 Intro / onboarding 有恰当体现，除非有明确理由不展示；
4. **Data-flow coverage**：确认的个人数据流需在 Privacy 中解释，未确认 recipient 不得被写成确定事实；
5. **Cross-page consistency**：品牌元数据、功能名称、邮箱、AI/Tracking/购买等事实在所有输出一致；
6. **Review reporting**：生成摘要读取 unknowns / conflicts 并区分事实提醒与生成失败；通用 Skill 不因未知法律事实自动阻止部署。

校验器避免只对固定英语词表做全文搜索；优先解析页面分段并检查生成时携带的事实引用清单，必要时再使用语义 / 禁词回归作为补充。

## 9. 建议实施阶段

### 阶段 A：项目资料收集与报告

- inspector 汇总源码、项目文档、配置和隐私 manifest；
- 过滤旧生成物和低可信目录；
- 输出 project profile、证据索引、unknowns 和 conflicts；
- 不改目标项目，不部署。

### 阶段 B：文案事实档案

- 将当前 AppHint / 固定 capability 映射改为“项目事实 + 可扩展特征”；
- 支持 agent/operator authoring JSON 为项目核心流程和品牌元数据提供确认；
- 对能力建立 `confirmed / candidate / unknown / conflict / confirmed_absent` 状态。

### 阶段 C：统一生成与校验

- Intro、Onboarding、Privacy、Terms、Support 使用同一 profile；
- 更新 legal facts schema，描述具体数据生命周期和 recipient；
- 增加事实引用追踪、无依据声明检测和跨页一致性校验；
- 缺失的关键事实只阻止部署，不阻止本地审阅草稿生成。

### 阶段 D：回归与验收

建立不依赖 Pinfi 特例的 fixture 矩阵，至少覆盖：

- 本地笔记 / 日记类：含手填 `location` 字段和旅行示例文本，但无 GPS；
- 真正定位类：含定位权限和可达地图流程；
- 纯本地照片工具：有相册导入，无照片上传；
- 头像使用远程服务：只发送头像资源请求，不能误写日记上传；
- 有后端账户 / UGC / Chat、AI、IAP 和 tracking 的项目；
- 项目说明与源码冲突、旧 AppListing 出现虚假能力、邮箱未验证等边界。

所有 fixture 都断言“应出现什么”和“不应出现什么”，并验证 `unknown` 不会静默变成 false。Onboarding 至少测试功能事实绑定、CTA 全宽 / 最小高度，以及每个模板的 3–5 张卡片结构。屏幕尺寸 / 自动轮播实测按用户另行要求执行，不纳入本方案默认验收。

## 10. Pinfi 样例应得到的通用结果

应用上述规则后，任何类似 Pinfi 的日记项目应由项目证据归纳出旅行日记、旅行集合、照片导入、时间线 / 筛选、用户主动备份与分享等实际流程；不得因为文本字段或故事出现 `location` / `map` 就生成定位功能。隐私页应描述本地记录与媒体行为、用户主动分享 / 导出，以及已确认的头像网络请求边界。头像请求的数据接收与用途、联系邮箱可用性、法务主体 / jurisdiction、受众与保留政策仍需操作者确认，不因属于样例而被 Skill 擅自补值。

以上仅作为方案验收期望，不在通用生成器中写入 Pinfi 名称、功能词或 host 特判。

## 11. 验收标准

- 同一个 Skill 在不同产品类型下不因固定 AppHint / 词表顺序产出相同的 onboarding 功能卡；
- 每条具体产品能力和法律事实都有可追溯证据或明确 operator confirmation；
- 误判能力不得进入任何面向用户的页面；
- 核心功能有证据时能进入文案，缺证据时要求补充而不是泛化凑数；
- 所有数据流按实际生命周期描述，权限不被误写成上传，域名不被误写成供应商；
- 未确认法律关键事实阻止发布并提供清楚诊断；
- Continue 按统一 CTA 样式显示为底部显著全宽按钮；
- 全量单测通过，至少覆盖上述跨行业 fixtures；不以某个目标项目写死的回归逻辑满足测试。

## 12. 已实施内容

- 新增通用 `project_profile`，从项目文档、页面 / 路由 / UI 证据和权限上下文提取可追溯的核心功能候选，避免把手填字段或示例文本直接当成系统能力。
- Onboarding 卡片改为读取确认的项目功能事实，不再使用固定的 Location / AI / 社区功能卡片作为默认补位。
- `index.html` 模板扩展为五种：`onboarding-cards`、`onboarding-spotlight`、`onboarding-compact`、`onboarding-minimal`、`onboarding-feature-list`；每次生成随机选择一个，也支持命令行显式覆盖。
- Continue 改为底部全宽、最小 60px 触控高度；五种模板共用安全区、单文件资源和桥接逻辑。
- 项目事实已进入站点概览和隐私数据分类；新增本地记录、导入媒体、集合、时间线、搜索筛选、备份导出和用户主动分享等通用事实字段。
- 已通过 Python 编译检查、219 项单元测试和 `git diff --check`。本轮未执行浏览器视口、自动轮播和真实 WKWebView 运行时验证。
