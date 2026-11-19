# Universal Final Visual Product Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (or superpowers:subagent-driven-development) to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Prevent every generated game, non-game, and mixed Flutter project from being treated as complete after a functional prototype or vertical slice; require a separate, machine-checkable final visual product contract before screenshots, release materials, or Git handoff.

**Architecture:** Keep the existing engine/native vertical slice as an early technical gate, then add a universal `.codex-work/final-visual-product.json` contract that records final visual maturity, authored assets, composition, materials/lighting, animation and state coverage, domain-specific UI quality, refinement rounds, and current-iPhone evidence. A new validator checks the contract and project-specific evidence; game validation delegates to it for game/mixed projects, release readiness requires a `final_visual_product` gate, and all workflow documents and installation entry points describe the same two-stage boundary.

**Tech Stack:** Python 3 standard library validators and unittest fixtures; Zsh workflow-integrity checks; Markdown workflow contracts; existing Flutter/iOS evidence conventions and `.codex-work` records.

**Spec:** `docs/superpowers/specs/2026-11-19-non-game-domain-architecture-design.md` plus the universal final-visual-product addendum recorded in that file.

## Global Constraints

- A vertical slice proves technical playability or a representative task loop only; it never proves final visual completion.
- `project_type` is always explicit: `game`, `non_game`, or `mixed`.
- Game projects must use a real `2.5d` or `3d` visual runtime and authored scene assets; non-game projects must use domain-specific visual systems and real component consumers.
- No project may ship simple line art, flat color-block collages, solid-color-only backgrounds, empty scenes, static screenshots, generic button boards, placeholder art, or a color/image-only reskin as the final visual product.
- Final visual acceptance requires current iPhone build evidence; missing runtime evidence is `Not verified` and blocks final readiness.
- Final screenshots, AppListing/Review Remarks publication status, and Git handoff are downstream of the final visual product gate.
- Internal development records may describe an early prototype or vertical slice, but final claims, public copy, release-readiness status, and user-facing completion messages must never call the delivered project a prototype or unfinished visual build.
- Existing iPhone-only, Portrait-only, bright-theme, accessibility, permission, resource, protocol, naming, `.codex-work/`, and no-commit Git handoff rules remain in force.

---

### Task 1: Extend the approved architecture specification

**Files:**
- Modify: `docs/superpowers/specs/2026-11-19-non-game-domain-architecture-design.md`

**Interfaces:**
- Consumes: The approved base-contract/domain-overlay design and the user addendum requiring non-game projects to obey the same final-visual rule as games.
- Produces: A canonical definition of `final-visual-product.json`, the vertical-slice versus final-product boundary, project-type-specific visual maturity fields, and release consequences.

- [x] **Step 1: Add the universal boundary section**

Document two explicit stages:

```text
technical_vertical_slice -> full domain/game implementation -> final_visual_product -> release materials -> Git handoff
```

State that the first stage cannot set final completion, generate final screenshots, or create the Git handoff.

- [x] **Step 2: Add the machine-readable contract shape**

Define required top-level fields:

```json
{
  "schema_version": 1,
  "project_type": "game | non_game | mixed",
  "claim": "final_visual_product",
  "development_stage": "final_visual_product",
  "prototype_boundary": {
    "vertical_slice_status": "Passed",
    "cannot_substitute_for_final": true
  },
  "common_visual_contract": {
    "no_simple_line_art": true,
    "no_flat_color_blocks": true,
    "no_solid_color_background": true,
    "no_placeholder_or_static_mock": true,
    "authored_asset_review": "Verified",
    "composition_review": "Verified",
    "motion_review": "Verified",
    "state_coverage_review": "Verified",
    "accessibility_review": "Verified",
    "refinement_rounds": 3,
    "current_iphone_evidence": [".codex-work/final-visual/iphone-recording.mp4"]
  },
  "game_visual_contract": null,
  "non_game_visual_contract": null,
  "evidence": [".codex-work/final-visual-product.md"]
}
```

Specify game-only and non-game-only fields and the mixed-project requirement for both sections.

- [x] **Step 3: Self-review the specification**

Search the spec for ambiguous language such as “prototype is enough,” “vertical slice is final,” “visual polish later,” or “time permits.” Remove or replace each occurrence with an explicit blocking rule.

### Task 2: Add the final visual product validator and regression tests

**Files:**
- Create: `flutter-engine-runner/scripts/validate_final_visual_product.py`
- Create: `flutter_check/test_validate_final_visual_product.py`

**Interfaces:**
- Consumes: `<project-root>/.codex-work/final-visual-product.json`, project files, and project-type-specific evidence paths.
- Produces: `validate_project(project_root) -> list[str]` and a CLI with `--project-root` and `--json`; an empty findings list is the source-contract pass.

- [x] **Step 1: Write failing validator tests**

Cover these fixtures:

1. Missing contract is reported.
2. `claim: "functional_prototype"` or `development_stage: "vertical_slice"` is rejected for final acceptance.
3. A contract with only vertical-slice evidence is rejected.
4. Game contract rejects fewer than three depth layers, fewer than four authored assets, missing materials/lighting, missing camera/composition, missing state variants, missing motion evidence, and missing current-iPhone evidence.
5. Non-game contract rejects missing primary domain, missing domain-specific visual language, fewer than three distinct result surfaces, missing real component consumers, and missing current-iPhone evidence.
6. Mixed contract rejects a missing game or non-game section.
7. A complete game fixture passes.
8. A complete non-game fixture passes.
9. A complete mixed fixture passes.
10. Final contract rejects placeholder/static-mock evidence paths and forbidden visual declarations.

- [x] **Step 2: Run the focused tests and confirm failure**

Run:

```bash
python3 -m unittest flutter_check/test_validate_final_visual_product.py
```

Expected: failures because the validator and contract fixtures do not exist yet.

- [x] **Step 3: Implement strict contract parsing**

Implement standard-library-only checks for:

- schema and project type;
- final claim/stage values;
- prototype boundary flag;
- common visual constraints and `Verified` statuses;
- at least three refinement rounds;
- evidence paths inside the project, with current-build/iPhone naming markers and regular files;
- game visual fields and authored asset paths;
- non-game domain, visual language, result surfaces, component consumers, and domain asset paths;
- mixed-project dual contracts;
- forbidden final status phrases and placeholder/static-mock markers.

Return actionable findings that identify the exact field and the required repair.

- [x] **Step 4: Run focused tests and confirm pass**

Run the same unittest command. Expected: all validator tests pass.

- [x] **Step 5: Run Python compilation and diff checks**

Run:

```bash
python3 -m py_compile flutter-engine-runner/scripts/validate_final_visual_product.py flutter_check/test_validate_final_visual_product.py
git diff --check
```

### Task 3: Make game validation require the final visual contract

**Files:**
- Modify: `flutter-engine-runner/scripts/validate_game_project.py`
- Modify: `flutter_check/test_validate_game_project.py`

**Interfaces:**
- Consumes: `validate_final_visual_product.validate_project` and existing game-engine/vertical-slice validation.
- Produces: Game/mixed validation that reports the vertical slice and final visual product as separate gates.

- [x] **Step 1: Add failing game tests**

Add tests that remove the final visual contract from an otherwise valid game fixture and assert a final-visual finding; add a test that marks only `vertical_slice_status: Passed` and asserts final completion remains blocked.

- [x] **Step 2: Update existing fixtures**

Add authored scene/UI/effect assets, final evidence files, and a complete `final-visual-product.json` to the passing Flame, Godot, and Flutter-native fixtures. Keep the intentionally colored-block fixture failing for both the visual contract and final contract.

- [x] **Step 3: Implement the delegation**

In `validate_project`, run the final visual validator for `game` and `mixed` projects after the existing engine/lobby checks. Prefix delegated findings with `final visual product:` and preserve vertical-slice findings separately. Do not make non-game projects pass through the game validator.

- [x] **Step 4: Run focused game tests**

Run:

```bash
python3 -m unittest flutter_check/test_validate_game_project.py
```

Expected: all existing and new tests pass.

### Task 4: Require the gate in release readiness and quality records

**Files:**
- Modify: `flutter-engine-runner/scripts/validate_release_readiness.py`
- Modify: `flutter-engine-runner/scripts/validate_quality_records.py`
- Modify: `flutter_check/test_validate_release_readiness.py`
- Modify: `flutter_check/test_validate_quality_records.py`

**Interfaces:**
- Consumes: `final_visual_product` release gate and final visual evidence referenced by `.codex-work/final-visual-product.json`.
- Produces: Release readiness that is `Not ready` unless final visual product is `Passed` or `Not applicable` for the declared project type; no `Ready for submission` result can omit it.

- [x] **Step 1: Add failing readiness tests**

Assert that the required gate set includes `final_visual_product`, that a missing gate is rejected, and that `final_visual_product: Blocked` or `Not verified` forces `Not ready`.

- [x] **Step 2: Add quality-matrix linkage checks**

Require a `final_visual_product` quality section containing the contract path, visual review status, refinement evidence, and current-iPhone evidence when the project is `game`, `non_game`, or `mixed`.

- [x] **Step 3: Implement and run focused tests**

Run both unittest files and confirm pass.

### Task 5: Update workflow documents and project prompts

**Files:**
- Modify: `工作流文档/00-总入口.md`
- Modify: `工作流文档/01-执行约定.md`
- Modify: `工作流文档/02-创意与思维导图.md`
- Modify: `工作流文档/03-产品定义与导航.md`
- Modify: `工作流文档/04-视觉与页面功能.md`
- Modify: `工作流文档/05-数据与工程架构.md`
- Modify: `工作流文档/06-素材与真实照片.md`
- Modify: `工作流文档/07-测试与质量验收.md`
- Modify: `工作流文档/08-发布与About材料.md`
- Modify: `工作流文档/09-实施顺序与交付报告.md`
- Modify: `工作流文档/10-第三方资源来源.md`
- Modify: `工作流文档/11-记录与证据契约.md`
- Modify: `README.md`
- Modify: `flutter-engine-runner/SKILL.md`
- Modify: `flutter-engine-runner/agents/openai.yaml`

**Interfaces:**
- Consumes: The canonical final visual contract and validator behavior from Tasks 1–4.
- Produces: One consistent rule set across planning, implementation, assets, testing, release materials, prompts, and records.

- [x] **Step 1: Add the canonical wording**

Use the exact distinction:

> “功能垂直切片只证明技术闭环；它不是最终视觉成品。游戏、非游戏和混合项目都必须另行通过 `final-visual-product.json` 的最终视觉成品门禁。未通过时只能记录 `Blocked`/`Not verified`，不得生成最终截图、发布材料或 Git handoff。”

Add the English equivalent to the skill and agent prompt.

- [x] **Step 2: Update planning and implementation order**

Change every “vertical slice passed, then expand” instruction to “vertical slice passed, then expand full scope, then final visual product gate, then release materials.” Add non-game coverage to the same sequence.

- [x] **Step 3: Add project-type-specific requirements**

Game: final 2.5D/3D authored scene, camera/occlusion, depth, materials/lighting, state variants, animation/feedback, HUD, full gameplay content and iPhone evidence.

Non-game: domain-owned visual language, distinct page/result compositions, real UI/visual component consumers, rich imagery/material/depth, states and iPhone evidence.

Mixed: both contracts must pass.

- [x] **Step 4: Add forbidden completion language**

State that final user-facing reports, public copy, readiness files, screenshots and Git-handoff reports may not describe the delivered project as a prototype, functional demo, rough build, visual prototype, unfinished art pass, or “to be polished.” Those words remain allowed only in internal historical/debug records that explicitly identify an earlier stage.

- [x] **Step 5: Update records and release order**

Add `final_visual_product` to the release-readiness gate list, records contract, final report table, and final screenshot prerequisites.

### Task 6: Add static workflow-integrity and onboarding regression coverage

**Files:**
- Modify: `flutter_check/test_workflow_integrity.sh`
- Modify: `flutter_check/test_onboarding_guide_workflow.sh`
- Modify: `flutter_check/run_all.sh`
- Modify: `flutter_check/test_bundle_layout.sh`

**Interfaces:**
- Consumes: canonical document names, validator path, and final-visual phrases.
- Produces: Regression checks that fail if a future edit removes the universal gate or omits the validator from the local run.

- [x] **Step 1: Add required file and phrase assertions**

Require `validate_final_visual_product.py`, its unittest, `.codex-work/final-visual-product.json`, `final_visual_product`, and the exact game/non-game wording in the source documents, skill, README, and agent prompt.

- [x] **Step 2: Add forbidden bypass assertions**

Reject phrases implying that a vertical slice, engine dependency, static screenshot, empty scene, functional prototype, or package installation is final visual completion.

- [x] **Step 3: Add the focused test to `run_all.sh`**

Run the final visual validator unittest in the parallel static-check list.

- [x] **Step 4: Run shell syntax and static checks**

Run:

```bash
zsh -n flutter_check/run_all.sh flutter_check/test_workflow_integrity.sh flutter_check/test_onboarding_guide_workflow.sh
```

### Task 7: Synchronize installation and verify the complete bundle

**Files:**
- Modify: `工作流文档/manifest.txt`
- Modify: `start.sh` (required-validator list and generated prompt)
- Modify: `flutter_check/test_start_remote_listing.sh`
- Synchronize: `/Users/admin/.codex/skills/flutter工程执行/` through `start.sh --install-only`

**Interfaces:**
- Consumes: updated source documents/scripts and the new validator.
- Produces: An installed skill whose workflow and scripts match the source bundle byte-for-byte where the installer copies them.

- [x] **Step 1: Update the manifest and installer prerequisites**

Add any new canonical workflow document to `manifest.txt`; require the new validator in `start.sh`; include the universal gate and non-game rule in the generated startup prompt.

- [x] **Step 2: Run bundle layout and integrity checks before installation**

Run:

```bash
zsh flutter_check/test_bundle_layout.sh
zsh flutter_check/test_workflow_integrity.sh
```

- [x] **Step 3: Synchronize the installed skill**

Run:

```bash
./start.sh --install-only
```

If remote AppListing synchronization is unavailable, use the installer's documented fallback and preserve the source/validation status; do not let that external source block copying the core workflow.

- [x] **Step 4: Verify source/installed parity**

Run:

```bash
zsh flutter_check/test_onboarding_guide_workflow.sh
```

Confirm the installed `SKILL.md`, installed workflow documents, and installed validator contain the same final-visual contract phrases and validator path.

### Task 8: Full regression and final self-review

**Files:**
- No new files; inspect all changed files and generated installation output.

- [x] **Step 1: Run the new focused tests**

Run the final-visual, game, release-readiness, quality-record, workflow-integrity, and onboarding tests individually so failures identify the responsible contract.

- [x] **Step 2: Run the complete local suite**

Run:

```bash
./flutter_check/run_all.sh
```

Expected: all local workflow checks pass. The suite must still state that this资料包 lacks a real Flutter App/iOS artifact and therefore cannot claim runtime readiness.

- [x] **Step 3: Scan every changed source for prototype bypasses**

Run:

```bash
rg -n -i '功能原型|视觉原型|functional prototype|visual prototype|prototype-only|vertical slice.*final|final.*vertical slice|color(ed)?[- ]block.*final|static screenshot.*final|unfinished.*visual|to be polished' \
  工作流文档 README.md flutter-engine-runner flutter_check start.sh
```

Only internal historical/debug wording explicitly scoped as non-final may remain; all completion and release paths must use the final visual product contract.

- [x] **Step 4: Run Python/Zsh/diff checks**

Run Python compilation for all changed Python files, `zsh -n` for changed shell files, and `git diff --check`.

- [x] **Step 5: Update the implementation plan status and report evidence**

Record the exact commands, exit codes, installed skill path, and any external AppListing limitation. Do not claim a real app, iPhone runtime, or final visual product has passed in this资料包.
