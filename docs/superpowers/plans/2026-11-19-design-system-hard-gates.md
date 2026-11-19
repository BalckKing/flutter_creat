# Design System and UI Quality Hard Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make theme selection, design-system selection, UI/UX evaluation, component adoption, and visual acceptance one mandatory chain that rejects unfinished or low-quality Flutter interfaces.

**Architecture:** After the theme is fixed, the runner selects the smallest matching `awesome-design-md` reference or records a custom `DESIGN.md` when no catalog entry fits. It then persists a `ui-ux-pro-max` design system for the detected Flutter/iPhone stack and records a hard-gate review. The actual project ledger and source preflight validator require these artifacts before visual completion; applicable requirements are release-blocking, while only genuinely inapplicable product capabilities may be excluded with evidence.

**Tech Stack:** Markdown workflow contracts, Python standard-library JSON/path validation, zsh regression checks, `awesome-design-md`, `ui-ux-pro-max`, Flutter/iPhone runtime evidence.

**Spec:** User-confirmed design-system workflow and the existing visual/game quality contracts in `工作流文档/04-视觉与页面功能.md` and `工作流文档/07-测试与质量验收.md`.

## Global Constraints

- No visual requirement is soft: unfinished, placeholder, low-fidelity, or unverified UI blocks release readiness.
- After theme confirmation, select one smallest-fit `awesome-design-md` `DESIGN.md`, or create a clearly labeled custom `DESIGN.md` when no catalog reference fits.
- After the reference decision, run `ui-ux-pro-max --design-system` for the detected Flutter/iPhone stack and persist its master system under the project root.
- `DESIGN.md`, the persisted design-system master, and the UI/UX review record are required before component selection and implementation.
- Every applicable finding must be resolved and verified on the current iPhone build; only a documented `Not appropriate` capability may be excluded.
- Do not force an unrelated brand reference, copy proprietary assets/fonts, or treat a package install, mockup, screenshot, or source prose as runtime proof.

---

### Task 1: Add the design-system contract to the workflow

**Files:**
- Modify: `README.md`
- Modify: `flutter-engine-runner/SKILL.md`
- Modify: `flutter-engine-runner/agents/openai.yaml`
- Modify: `工作流文档/01-执行约定.md`
- Modify: `工作流文档/02-创意与思维导图.md`
- Modify: `工作流文档/04-视觉与页面功能.md`
- Modify: `工作流文档/05-数据与工程架构.md`
- Modify: `工作流文档/07-测试与质量验收.md`
- Modify: `工作流文档/09-实施顺序与交付报告.md`

**Interfaces:**
- Produces: exact artifact paths, ordering, hard-gate language, and evidence fields consumed by the validator and installer checks.

- [ ] **Step 1:** Add a mandatory theme-to-design-system sequence and the `DESIGN.md`, `design-system/<slug>/MASTER.md`, and `.codex-work/ui-ux-review.md` artifact contract.
- [ ] **Step 2:** State that `awesome-design-md` is the first reference source and custom design is the fallback only when no catalog entry fits; prohibit forced references and proprietary copying.
- [ ] **Step 3:** State that `ui-ux-pro-max` must evaluate Flutter/iPhone accessibility, touch targets, safe areas, typography, color contrast, responsive layout, motion, navigation, and reduced motion before component selection.
- [ ] **Step 4:** Replace soft quality language with release-blocking language, preserving capability applicability decisions as the only valid exclusion path.
- [ ] **Step 5:** Add the sequence to the execution order and final report fields.

### Task 2: Extend the visual ledger and validator

**Files:**
- Modify: `flutter-engine-runner/scripts/validate_visual_implementation.py`
- Modify: `flutter_check/test_validate_visual_implementation.py`

**Interfaces:**
- Consumes: `.codex-work/ui-visual-gates.json` with `design_system` and `ui_ux_review` objects.
- Produces: deterministic failures for missing, incomplete, stale, or unresolved design-system evidence.

- [ ] **Step 1:** Add a validator helper that requires `DESIGN.md`, persisted `MASTER.md`, and a nonempty UI/UX review file inside the project boundary.
- [ ] **Step 2:** Require source provenance, custom/reference status, selection rationale, Flutter stack, command/query, review status, findings, resolutions, and current iPhone evidence.
- [ ] **Step 3:** Reject review statuses other than `Verified`, unresolved findings, placeholder language, missing accessibility/interaction categories, and records that only cite screenshots or package names.
- [ ] **Step 4:** Add fixtures for valid catalog reference, valid custom reference, missing artifact, unresolved review, and invalid external path.

### Task 3: Add regression checks and synchronize the installed skill

**Files:**
- Modify: `flutter_check/test_workflow_integrity.sh`
- Modify: `flutter_check/test_onboarding_guide_workflow.sh`
- Modify: `flutter_check/run_all.sh` only if a new focused test is added.

**Interfaces:**
- Consumes: Tasks 1–2 contract text and validator behavior.
- Produces: fail-fast protection against reintroducing soft visual requirements or bypassing design review.

- [ ] **Step 1:** Require the two skills, artifact paths, sequence, hard-gate wording, and applicability-only exclusion rule in source docs and `SKILL.md`.
- [ ] **Step 2:** Forbid phrases that permit half-finished/low-quality UI or treat design references, package installation, static mockups, or screenshots as completion.
- [ ] **Step 3:** Run focused tests, syntax checks, full workflow regression, and installer synchronization.
- [ ] **Step 4:** Verify source and installed copies match and report the absent real Flutter project honestly.
