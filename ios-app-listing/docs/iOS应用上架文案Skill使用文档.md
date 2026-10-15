# iOS App Listing Skill 使用文档

## 1. 这个 skill 现在做什么

`ios-app-listing` 是一个基于源码证据生成 `AppListing/` 的 skill。

它当前负责：

- 识别 Flutter iOS app 或原生 Swift iOS app
- 从源码提取权限、能力、IAP、AI、UGC、品牌与 logo 候选
- 生成 `Intro.md`
- 生成 `site/index.html`、`PrivacyPolicy.html`、`Terms&Conditions.html`、`Support.html`
- 在生成后自动运行一组校验器，不通过不交付

它不负责：

- 修改 app 业务代码
- 修复审核环境、真机行为、IAP 逻辑 bug
- 代替 App Store Connect 人工配置

它还有一个强约束：

- 不关注也不改动任何名为 `package` 或 `packages` 的目录及其内容
- 不在这些目录里执行格式化、生成、安装、迁移等会产生文件变更的操作
- 生成证据、能力判断、URL 推断、logo 候选都只看第一方 app 代码和业务材料

---

## 2. 当前目录结构

```text
ios-app-listing/
  SKILL.md
  assets/
    site-render/
      templates-manifest.json
  docs/
  references/
  scripts/
  tests/
```

说明：

- `assets/site-render/templates-manifest.json` 是当前站点渲染仍在使用的模板清单。
- 不再使用旧的仓库内静态 HTML 模板目录作为模板源。
- `scripts/render_app_listing.py` 负责真正写出 `site/*.html`。

---

## 3. 生成结果

默认只输出：

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

不要额外生成契约外文件，除非用户明确要求。

---

## 4. 标准流程

1. 定位 app root
2. 运行 `scripts/inspect_app.py`
3. 识别 active capabilities、隐私信号、AI 信号
4. 运行 `scripts/generate_app_listing.py --target /abs/path/to/app --select-description-style`，先拿到这次 `## Description` 应该使用的 style
5. 当前代理基于 inspect、classification 和选中的 style 编写 authoring JSON，其中至少包含 `description` 与 `description_style_label`，推荐同时包含 `brand_overview`、`index_subtitle`、`purpose`、`members_intro`
6. 运行 `scripts/generate_app_listing.py --authoring-json ...` 生成 `Intro.md` 与 `site/*.html`
7. 复制最佳 logo 到 `AppListing/site/img/logo.png`
8. 自动运行 validators
9. 如果没有可用 logo，直接失败，不生成不完整的 `AppListing/`
10. 全部通过后默认自动部署 `AppListing/site/`
11. 如果 `app_name` 子域名查询超时、失败或返回无效域名，必须停止部署并保留 `https://xxx.xxx.xxx/...` 占位 URL，不得借用其他项目的已存在域名继续发版
12. 部署任务成功后，默认等待 3 分钟再探测线上页面可用性；只有探测到真实可用 URL 时才把 `Intro.md` 回填为真实线上 URL

常用命令：

```bash
python3 scripts/inspect_app.py --target /abs/path/to/app
python3 scripts/generate_app_listing.py --target /abs/path/to/app --select-description-style
python3 scripts/generate_app_listing.py --target /abs/path/to/app
python3 scripts/generate_app_listing.py --target /abs/path/to/app --authoring-json /tmp/app_listing_authoring.json
python3 scripts/generate_app_listing.py --target /abs/path/to/app --no-deploy-about
python3 scripts/generate_app_listing.py --target /abs/path/to/app --deploy-publish-ready-delay 180
```

---

## 5. inspect 输出里最重要的字段

- `source_stack`
- `app_name` / `app_slug`
- `support_email` / `support_email_source`
- `permissions`
- `iap_codes` / `iap_shop_code_display`
- `capability_candidates`
- `privacy_signals`
- `ai_signals`
- `logo_candidates`

`score >= 1.0` 的 capability 候选通常视为 active capability。

---

## 6. `Intro.md` 当前规则

`Intro.md` 必须严格使用以下标题：

- `# App Name — App Store Description`
- `## App Name`
- `## Sub Title`
- `## Category`
- `## Description`
- `## Keywords`
- `## Support URL`
- `## Terms of Service URL`
- `## All URL`
- `## UGC`
- `## Chat`
- `## Copyright`

关键约束：

- `Sub Title` 必须是两个 Title Case 单词，用 ` & ` 连接
- 如果当前 agent 没有显式提供 `subtitle`，生成器会从固定 50 个抽象副标题池里按全局顺序轮转分配，不再按 app slug 固定映射
- `Category` 必须是短双语 App Store 类别标签
- `Description` 由当前 18 种风格池生成：`concise`、`feature_3`、`feature_4`、`feature_5`、`benefit_3`、`benefit_4`、`longform`、`summary_plus_feature_3`、`summary_plus_benefit_3`、`community_then_purchase`、`feature_then_value`、`you_can_3`、`you_can_4`、`why_choose_3`、`homebase_4`、`all_in_one`、`members_first`、`everyday_use`
- style 不是全局随机，而是先按 app 信号筛出候选池，再在候选池内按顺序轮转；同一个 app 重新生成时也会继续向下轮换，不再固定复用旧 style
- 如果先调用 `--select-description-style`，再传 authored copy 生成，应该把同一个 style 回填到 `description_style_label`
- 有 IAP 时，不再输出旧版 IAP 独立标题，而是在 `Description` 中自然提及 `purchase / credits / coins / virtual goods`
- `All URL` 必须是固定 6 行结构
- `UGC` 必须是 `Yes` / `No`，用于标记是否存在用户生成内容业务
- `Chat` 必须是 `Yes` / `No`，用于标记是否存在真人消息/聊天业务
- 当 `UGC = Yes` 或 `Chat = Yes` 时，`Description` 也必须自然体现对应能力，不能只在字段里勾选
- `Support URL`、`Terms of Service URL`、`All URL` 一律统一使用 `https://xxx.xxx.xxx/...` 占位
- 默认会先写占位 URL，等 About 部署成功后再把 `Intro.md` 回填成真实线上 URL；只有显式传 `--no-deploy-about` 才会保留占位值作为最终结果
- 这里的 “部署 About” 指发布远端 `AppListing/site/*.html`，不是默认修改 App 内 About 页面结构
- 默认源码同步是 replacement-only：只替换项目里原本已有的协议 / listing URL，不新增 `Support` / `index` 入口、按钮、控制器方法或文案

如果命中高风险 AI Preview / face-data 场景：

- `Description` 前 255 字内必须明确说明：
  - 用户选择照片
  - 生成 preview
  - 查看结果
  - 可选保存到 Photos
  - 若有 IAP，提及 credits / purchase 语义

模板文件见：[intro.md](./intro.md)

---

## 7. HTML 当前规则

`site/index.html`：

- 必须与 inspect 证据一致
- 必须使用当前 renderer 的统一视觉系统
- 不得凭空宣称功能

`site/PrivacyPolicy.html`：

- 根据权限、IAP、UGC、AI 信号动态注入章节
- 当 `ai_signals.review_profile.needs_face_data_clauses = true` 时，必须进入 AI Preview / face-data 专项分支

`site/Terms&Conditions.html`：

- 根据 UGC / IAP / AI / translation 信号动态注入章节
- AI Preview 高风险场景下，必须写允许用途与禁止用途

`site/Support.html`：

- FAQ 必须与 app 能力相关
- AI Preview 高风险场景下，必须包含：
  - `How does AI Preview work?`
  - `Why does the app request camera, photo-library, or add-to-library access?`

---

## 8. AI Preview / face-data 分支

当前 skill 已实现一条更严格的 AI Preview / face-data 生成分支。

当 inspect 同时识别出以下信号时，会强制进入这条分支：

- `ai_image_generation`
- `camera` / `photo_library`
- `selected_photo`
- `consent_prompt`
- `generated_result`
- `save_to_photos`

对应字段：

```json
ai_signals.review_profile.needs_face_data_clauses = true
```

进入后会强制改写：

- `Intro.md`
- `site/index.html`
- `site/PrivacyPolicy.html`
- `site/Terms&Conditions.html`
- `site/Support.html`

---

## 9. 当前主要校验器

- `validate_intro_output.py`
- `validate_privacy_output.py`
- `validate_permission_privacy.py`
- `validate_terms_ai_output.py`
- `validate_ugc_legal_output.py`
- `validate_iap_legal_output.py`
- `validate_support_output.py`
- `validate_listing_claims.py`
- `validate_review_wording.py`
- `validate_listing_contract.py`

说明：

- `validate_privacy_output.py` 现在不只检查“泛 AI 段落”，也会检查 AI Preview / face-data 的章节名、收集项、provider、retention、deletion、禁止用途等。
- `validate_permission_privacy.py` 现在会把 AI Preview 权限链路一起检查。

---

## 10. 哪些 docs 是当前规范，哪些是历史方案

优先级：

1. `SKILL.md`
2. `references/output-contract.md`
3. `references/privacy-ai-rules.md`
4. 本文档

历史专题方案文档已清理；当前实现说明以上述文件及实际脚本行为为准。

---

## 11. 什么时候停下来确认

以下情况不应硬猜：

- 存在多个可能的 app root
- 找不到 `pubspec.yaml`、`.xcodeproj`、`Info.plist`、`Package.swift`
- inspect 无法确定 `app_name` / `app_slug`
- 分类校验器持续拒绝所有合理结果

---

## 12. 相关文档

- [Intro 规范方案](./iOS应用上架文案Skill%20Intro规范方案.md)
- [拒审预防与校验方案](./iOS应用上架文案Skill拒审预防与校验方案.md)
