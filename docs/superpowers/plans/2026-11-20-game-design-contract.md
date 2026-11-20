# 游戏设计契约失效修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为所有游戏和混合 Flutter 项目建立单一、可测量、可追溯的游戏设计契约，并阻断粗糙视觉、领域与渲染脱节、虚假证据和文档状态冲突。

**Architecture:** 新增独立 `validate_game_design_contract.py` 静态检查器，读取项目 `.codex-work/game-design-contract.json`，检查唯一设计来源、视觉结构、模式领域消费、资产管线、逐页契约、证据绑定、状态一致性和硬性否决规则。现有 `validate_game_project.py` 在 `game`/`mixed` 项目中先调用它，再执行已有引擎/垂直切片检查；非游戏项目保持原路径。工作流文档、README、SKILL、安装器和回归测试同步写入同一契约。

**Tech Stack:** Python 3 标准库、unittest、zsh 静态契约检查；不新增运行时包。

**Spec:** `docs/superpowers/specs/2026-11-20-game-design-contract-design.md`

## Global Constraints

- 游戏/混合项目必须有 `.codex-work/game-design-contract.json`；非游戏项目不执行游戏契约。
- 契约唯一权威优先于其他设计文件；冲突必须失败，不能自行拼接。
- 2.5D/3D 必须由可检查的投影、层级、资产、材质/光照、遮挡和动态阈值构成。
- 每个模式的领域数据必须绑定到实际渲染消费者；只改标题、颜色、数量或文案必须失败。
- 每个页面必须有真实路由、独立布局、交互/错误状态和当前运行证据。
- 计划、实现、验证、发布状态分离；状态冲突和先写结论后补证据必须失败。
- 纯色几何拼接、占位资产、重复截图、静态图冒充动效、未实现路由、无当前设备证据均为阻断。
- 现有 iOS、最终视觉成品、有界长命令和 Git handoff 顺序保持不变。

### Task 1: Add failing regression fixtures

**Files:**
- Modify: `flutter_check/test_validate_game_project.py`
- Create: `flutter_check/test_validate_game_design_contract.py`

- [ ] Add a valid contract fixture with two modes, domain render consumers, asset pipeline, page contracts, evidence bindings and synchronized statuses.
- [ ] Add failures for missing contract, conflicting source-of-truth files, missing measurable visual thresholds, mode data without render consumers, placeholder/flat geometry assets, missing route/page evidence, duplicate evidence, stale device/build evidence, and status contradictions.
- [ ] Run the new tests and confirm they fail before the validator exists.

### Task 2: Implement the contract validator

**Files:**
- Create: `flutter-engine-runner/scripts/validate_game_design_contract.py`

- [ ] Implement JSON loading, schema/type checks, safe project-relative path checks and deterministic findings.
- [ ] Implement source-of-truth conflict detection, measurable visual contract checks, per-mode domain/render consumer checks, asset pipeline checks, page contract checks, evidence identity/hash checks, status consistency and rejection rules.
- [ ] Return JSON with `status`, `findings`, `errors`, `warnings`, `contract_path`, and `checked_at`; return nonzero on blocking findings.
- [ ] Run the focused tests and make them pass.

### Task 3: Integrate with the existing game preflight

**Files:**
- Modify: `flutter-engine-runner/scripts/validate_game_project.py`
- Modify: `flutter_check/test_validate_game_project.py`
- Modify: `flutter_check/run_all.sh`
- Modify: `flutter_check/test_bundle_layout.sh`
- Modify: `flutter_check/test_start_remote_listing.sh`
- Modify: `start.sh`

- [ ] Load the new validator by path without importing the installed package as a module.
- [ ] Invoke it for `game` and `mixed` projects before existing engine checks, preserving non-game behavior.
- [ ] Add the script to required bundle files, layout list, install-copy checks and parallel regression.
- [ ] Add integration tests proving missing/invalid contract blocks `validate_game_project.py`.

### Task 4: Synchronize workflow documents and static gates

**Files:**
- Modify: `工作流文档/02-创意与思维导图.md`
- Modify: `工作流文档/03-产品定义与导航.md`
- Modify: `工作流文档/04-视觉与页面功能.md`
- Modify: `工作流文档/05-数据与工程架构.md`
- Modify: `工作流文档/07-测试与质量验收.md`
- Modify: `工作流文档/09-实施顺序与交付报告.md`
- Modify: `工作流文档/11-记录与证据契约.md`
- Modify: `README.md`
- Modify: `flutter-engine-runner/SKILL.md`
- Modify: `flutter-engine-runner/agents/openai.yaml`
- Modify: `flutter_check/test_workflow_integrity.sh`
- Modify: `flutter_check/test_onboarding_guide_workflow.sh`

- [ ] Add the single-truth priority and conflict rule.
- [ ] Replace subjective visual language with measurable fields and explicit rejection rules.
- [ ] Require the domain-to-render consumer matrix, asset pipeline, page contracts, evidence identity and status synchronization.
- [ ] Require the new validator before final visual product and before release materials/Git handoff.
- [ ] Add static assertions for every new contract rule.

### Task 5: Verify source, installed copy and full regression

**Files:**
- No new files.

- [ ] Run focused contract tests, existing game tests, shell syntax, Python compilation and diff checks.
- [ ] Run `flutter_check/run_all.sh`.
- [ ] Run `./start.sh --install-only` and verify installed copy plus `test_start_remote_listing.sh`.
- [ ] Confirm all changes remain uncommitted and report real limitations; no real Flutter app build is claimed from this workflow bundle.
