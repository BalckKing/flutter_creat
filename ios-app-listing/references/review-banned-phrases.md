# App Store 审核不利表述 — 禁用词表

> 供 `validate_review_wording.py` 与生成阶段共用。  
> 方案说明：[docs/iOS应用上架文案Skill拒审预防与校验方案.md](../docs/iOS应用上架文案Skill拒审预防与校验方案.md) §3。

## 原则

- 用户可见文案不得暴露「本地模拟 / 仅离线 / 设备本地库」等实现细节。
- 对外呈现为**真实、可用的在线产品**（与 inspect 证据一致）。
- 匹配：**大小写不敏感**；英文按词边界；多词短语优先整句匹配。

## 禁用词与短语

| ID | 匹配项 | 类型 |
|----|--------|------|
| `mock` | `mock` | word |
| `offline` | `offline` | word |
| `mock_data` | `mock data` | phrase |
| `local_data` | `local data` | phrase |
| `local_storage` | `local storage` | phrase |
| `device_storage` | `device storage` | phrase |
| `offline_only` | `offline only` | phrase |
| `local_impl` | `local` | word |

`local` 仅在描述**数据、存储、同步实现**时禁止；法律语境见例外表。

## 合法例外（不报错）

| 短语 | 场景 |
|------|------|
| `local laws` | Terms 适用法律 |
| `local regulations` | 法律/合规 |
| `local community` | 社区（非存储含义） |
| `locale` | 语言/地区 |

## 建议替代表述

| 避免 | 建议 |
|------|------|
| mock / mock data / test data | 删除或改为中性空态（如 no content yet） |
| local data / local storage | your content in the app / saved preferences / service information |
| device storage | storage used by the app（权限说明时简短带过） |
| offline only | 避免；无网可用 limited features when connection is unavailable |
| stored locally on device for offline use | preferences saved in the app / synced when online |

## 校验范围（AppListing）

- `Intro.md`
- `site/index.html`
- `site/Support.html`
- `site/PrivacyPolicy.html`
- `site/Terms&Conditions.html`

## 二期扩展（可选）

中文禁用：`模拟`、`假数据`、`离线仅`、`本地存储`、`本地数据`、`设备存储` 等。

App 内 UI 字符串若由其他流水线生成，应引用本表或同一 JSON 配置。
