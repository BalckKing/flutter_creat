# iOS App Listing Skill：Intro 规范方案

> 本文档只描述 `Intro.md` 的当前生效规则。  
> 如与旧提案冲突，以 `SKILL.md`、`references/output-contract.md`、`validate_intro_output.py` 为准。

---

## 1. 固定结构

`Intro.md` 必须严格使用以下标题名称与顺序：

```markdown
# App Name — App Store Description

## App Name

## Sub Title

## Category

## Description

## Keywords

## Support URL

## Terms of Service URL

## All URL

## UGC

## Chat

## Copyright
```

不得新增、删除或改名。

---

## 2. 字段规则

### `# App Name — App Store Description`

- 总标题固定格式
- `App Name` 使用最终上架名称

### `## App Name`

- 只填写应用名
- 不写夸张词或功能堆砌词

### `## Sub Title`

- 必须是两个 Title Case 单词
- 中间固定用 ` & ` 连接
- 应为抽象氛围词，不应直接写功能词
- 避免：`Chat`、`Call`、`AI`、`Preview`、`Notes`、`Bag`

### `## Category`

- 必须是短双语 App Store 类别标签
- 示例：`社交 (Social Networking)`、`摄影与录像 (Photo & Video)`
- 必须与分类结果一致

### `## Description`

- 必须是纯文本，不写 HTML
- 每次生成必须从当前风格池中选择一种：
  - `concise`
  - `feature_3`
  - `feature_4`
  - `feature_5`
  - `benefit_3`
  - `benefit_4`
  - `you_can_3`
  - `you_can_4`
  - `why_choose_3`
  - `homebase_4`
  - `all_in_one`
  - `members_first`
  - `everyday_use`
  - `longform`
- 有 IAP 时，需在描述中自然提及 `purchase / credits / coins / virtual goods`
- 非 `feature_3`、`feature_4`、`feature_5` 风格下，避免使用过于底层的实现措辞，如 `video chat`、`1v1 call`、`preview flow`
- `UGC = Yes` 时，描述里应自然出现 community / public profile / post / sharing 一类语义；私人 Profile、笔记、照片和私聊不单独触发 UGC
- `Chat = Yes` 时，描述里应自然出现 chat / message / conversation 一类语义
- `Chat = No` 时，描述里不应暗示 App 内真人聊天能力

### `## Keywords`

- 英文逗号分隔
- 应与 inspect / classification 证据一致
- 避免误导词、竞品词、无关词

### `## Support URL`

- 必须是完整 `https://...` URL
- 一律使用 `https://xxx.xxx.xxx/Support.html`

### `## Terms of Service URL`

- 必须是完整 `https://...` URL
- 一律使用 `https://xxx.xxx.xxx/Terms&Conditions.html`

### `## All URL`

- 必须是固定 6 行结构
- 4 行 URL 一律使用 `https://xxx.xxx.xxx/...`
- 第一行和最后一行固定为：

```text
==================================================
```

- 中间 4 行标签与顺序固定：
  - `首页: <index url>`
  - `隐私政策: <privacy url>`
  - `用户协议: <terms url>`
  - `Support: <support url>`

### `## UGC`

- 只允许填写 `Yes` 或 `No`
- `Yes` 代表 inspect 已识别到用户生成内容相关业务，例如：
  - 社区 feed
  - 发帖 / 发布
  - 用户资料页与公开分享内容
- 不要因为只有私信能力就把 `UGC` 写成 `Yes`

### `## Chat`

- 只允许填写 `Yes` 或 `No`
- `Yes` 代表 inspect 已识别到真人消息、私信、inbox、thread、chat 等会话能力
- AI assistant / prompt chat 不应算作这里的 `Chat`

### `## Copyright`

- 使用真实版权行
- 推荐格式：`© YYYY Company Name. All rights reserved.`

---

## 3. AI Preview / face-data 特殊规则

当 inspect 命中：

```json
ai_signals.review_profile.needs_face_data_clauses = true
```

则 `## Description` 前 255 字必须明确说明以下内容：

- 这是带 AI Preview 的 app
- 用户可选择照片
- 会生成 preview / generated result
- 用户会先查看结果
- 结果可以可选保存到 Photos
- 若有 IAP，需提及 credits / purchase 语义

这条规则是当前 `validate_intro_output.py` 的硬校验之一。

---

## 4. 不再使用的旧口径

以下旧口径已失效，不应继续写入文档或 prompt：

- 旧版副标题 heading 名称
- 旧版 IAP 独立 section
- 无 IAP 时写占位行到 Intro

当前规则是：

- 标题名固定为 `## Sub Title`
- IAP 信息通过 `## Description` 中的自然语言体现

---

## 5. 提交前检查清单

- 标题名与顺序是否完全一致
- `Sub Title` 是否满足两词 + ` & ` + 抽象风格
- `Category` 是否为短双语类别标签
- `All URL` 是否为固定 6 行结构
- `UGC` / `Chat` 是否与 inspect 证据一致
- `Description` 是否与真实能力一致
- 是否包含禁用词：`mock`、`local data`、`offline only` 等
- 若命中 AI Preview / face-data，高风险规则是否已写入前 255 字

---

## 6. 参考

- [intro.md](./intro.md)
- [拒审预防与校验方案](./iOS应用上架文案Skill拒审预防与校验方案.md)
