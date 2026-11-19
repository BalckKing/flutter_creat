# Non-game Product Depth and iOS Capability Expansion Implementation Plan

> **For agentic workers:** Execute this plan inline in the current session with test-first checkpoints. Do not commit or push.

**Goal:** Raise every non-game Flutter project from a shallow themed shell to a content-rich theme workbench, while allowing all theme-relevant iOS capabilities through a verified capability matrix.

**Architecture:** Update the workflow contract, installer prompt, static tests, and acceptance language together. Product generation will require 12 pages, 8 modules, 12 category/scenario families, 120 verified domain records, 12 end-to-end tasks, and 6 interaction forms; permission planning will use a capability matrix covering all relevant iOS APIs with runtime denial fallbacks, while ATT/IDFA/tracking remains excluded.

**Tech Stack:** Markdown workflow contracts, POSIX shell tests, Python static validators, YAML installer metadata.

**Spec:** User-approved design in the preceding conversation.

## Global Constraints

- All projects remain iPhone-only and Portrait-only.
- GetX and external routing packages remain forbidden; use Flutter native Navigator.
- Welcome remains a single native Flutter page with no pause control; `aduit/welcome.html` is delivery-only.
- The final site keeps exactly three protocol pages and no `index.html`.
- ATT, IDFA, tracking authorization, and advertising capability remain removed.
- No code is committed or pushed.

### Task 1: Add failing contract tests

**Files:**
- Modify: `flutter_check/test_workflow_integrity.sh`
- Modify: `flutter_check/test_onboarding_guide_workflow.sh`

- [ ] Add assertions for the expanded non-game scale and capability matrix.
- [ ] Run the focused shell tests and confirm they fail because the workflow text is still at the old scale/restricted permission language.

### Task 2: Raise product depth requirements

**Files:**
- Modify: `工作流文档/03-产品定义与导航.md`
- Modify: `工作流文档/02-创意与思维导图.md`
- Modify: `README.md`
- Modify: `flutter-engine-runner/SKILL.md`

- [ ] Replace the old 8/5/8/80/8/5 floors with 12/8/12/120/12/6.
- [ ] Require distinct discovery, creation, editing, analysis, history, settings, help, and result flows where the theme supports them.
- [ ] Require a theme domain model, cross-page data handoff, revisitable artifacts, and non-duplicate content evidence.
- [ ] State that non-game projects cannot use a simple list/detail/card shell as the finished product.

### Task 3: Expand iOS capability planning

**Files:**
- Modify: `工作流文档/01-执行约定.md`
- Modify: `工作流文档/05-数据与工程架构.md`
- Modify: `工作流文档/06-素材与真实照片.md`
- Modify: `工作流文档/07-测试与质量验收.md`
- Modify: `工作流文档/08-发布与About材料.md`
- Modify: `工作流文档/09-实施顺序与交付报告.md`

- [ ] Replace narrow optional-permission language with a capability matrix covering photos/camera, microphone/speech, notifications, location/maps, calendar/reminders, contacts/sharing, files, Bluetooth/NFC, motion, HealthKit, and other theme-relevant APIs.
- [ ] Require every theme-relevant capability to be either implemented and runtime verified or marked not appropriate with evidence; no silent skipping because of a former restriction.
- [ ] Require Info.plist purpose strings, entitlements, Podfile/plugin macros, runtime prompts, denial recovery, and final artifact checks per selected capability.
- [ ] Keep ATT/IDFA/tracking/advertising explicitly removed.

### Task 4: Update installer and metadata

**Files:**
- Modify: `start.sh`
- Modify: `flutter-engine-runner/agents/openai.yaml`

- [ ] Make the startup prompt describe the expanded non-game depth and capability matrix.

### Task 5: Verify and synchronize

**Files:**
- Synchronize source files to `/Users/admin/.codex/skills/flutter工程执行/`.

- [ ] Run `flutter_check/run_all.sh`, Python compilation, shell syntax, YAML parsing, and `git diff --check`.
- [ ] Confirm source and installed copies match.
- [ ] Confirm no commit, push, or repository association occurs.
