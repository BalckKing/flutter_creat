# Game Engine Quality Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every selected Flutter game project use a real game engine, reach a playable vertical slice before expansion, and pass a visual/runtime quality gate that rejects crude placeholder scenes and recurring lifecycle/layout failures.

**Architecture:** Extend the existing Flutter workflow contract with a game-only engine manifest and vertical-slice evidence contract. Add a source preflight validator that inspects the actual Flutter project, engine dependency, scene entrypoint, game runtime ownership, assets, gameplay state markers, and evidence paths; keep runtime Simulator interaction as the final authority. Update the workflow documents, skill prompt, installer regression checks, and tests together so the rule cannot drift between source and installed skill.

**Tech Stack:** Markdown workflow contracts, Python 3 standard-library validator, POSIX/zsh regression scripts, Flutter/Dart source inspection, Flame/Godot/Unity integration evidence, iPhone Simulator runtime evidence.

**Spec:** Approved design in the preceding conversation; reference quality baselines are `/Volumes/00_files/program/2026.9/4/Cnida` and `/Volumes/00_files/program/2026.10/27/Naevo`.

## Global Constraints

- Game is optional; only confirmed game or mixed projects enter the game gate.
- A selected game must use one declared real engine with a precise version and actual iPhone integration; adding a dependency or showing a static scene is insufficient.
- Welcome reaches the primary game destination directly, with at most one visible Play/Start action.
- The vertical slice must prove real input, engine update, success/failure result, feedback, and restart before content expansion.
- Game visuals must include authored subject assets, scene depth, materials/lighting, animation/feedback, and readable HUD; colored blocks, empty scenes, static screenshots, and autoplay demos fail.
- Runtime verification uses one Bundle ID and one existing iPhone Simulator; test files never replace direct App interaction and logs.
- Native Navigator remains required; GetX, ATT, iPad/Mac targets and unrelated permissions remain forbidden.
- The source bundle and installed skill must remain synchronized through `start.sh`; no user App Git commit or push is performed.

---

### Task 1: Write the game engine and vertical-slice contract

**Files:**
- Modify: `工作流文档/05-数据与工程架构.md:364-390`
- Modify: `工作流文档/07-测试与质量验收.md:344-360`
- Modify: `工作流文档/09-实施顺序与交付报告.md:36-48`
- Modify: `README.md:19-52,250-270`

**Interfaces:**
- Consumes: Existing sections 9.5–9.6, 11.11–11.11.1, current iPhone runtime contract.
- Produces: Explicit engine manifest fields, vertical-slice order, visual-quality criteria, lifecycle failure list, and release-blocking language consumed by the validator and skill.

- [ ] **Step 1: Add an engine manifest schema to section 9.6**

  Define required `.codex-work/game-engine.json` fields: `project_type`, `engine.name`, `engine.version`, `engine.role`, `engine.integration`, `engine.entrypoint`, `engine.scene_assets`, `engine.runtime_owner`, `engine.native_bridge` (when applicable), `engine.build_commands`, and `engine.evidence`. Require exact engine versions and a reason for declining alternatives.

- [ ] **Step 2: Replace “minimum game loop” language with a vertical-slice gate**

  Require the order `engine environment → scene boot → authored asset load → input → update/physics → result → feedback → restart`, with the same Bundle ID and current iPhone. State that failure blocks all game content expansion, final screenshots, and Git handoff.

- [ ] **Step 3: Add visual quality and runtime defect gates**

  Name the defects that block release: `setState() called during build`, RenderFlex overflow, stale callbacks after dispose, duplicate engine registration, engine timeout, input mismatch, overlay occlusion, lifecycle resume duplication, and crash/white-screen/hang. Require scene depth, subject assets, material/light treatment, camera/occlusion, animation/particles, HUD hierarchy, and authored result feedback.

- [ ] **Step 4: Update implementation order and README summary**

  Make game execution order explicit: `engine setup → vertical slice → iPhone run → visual refinement → approved gameplay expansion`. Remove any wording that lets parallel work bypass the playable gate.

- [ ] **Step 5: Review the edited contract**

  Run `rg -n` for every required field and failure phrase; ensure non-game projects remain `Not applicable` and no rule accidentally mandates an engine for ordinary apps.

---

### Task 2: Add the game-project source preflight validator

**Files:**
- Create: `flutter-engine-runner/scripts/validate_game_project.py`
- Create: `flutter_check/test_validate_game_project.py`
- Modify: `flutter_check/run_all.sh`

**Interfaces:**
- Consumes: `--project-root <Flutter root>`, optional `--json`, `.codex-work/game-engine.json`, `pubspec.yaml`, `lib/`, `ios/`, engine project files, and local evidence paths.
- Produces: exit 0 only when the game contract is structurally satisfied; stdout findings identify exact missing/invalid fields and paths.

- [ ] **Step 1: Write failing validator tests**

  Cover:
  - missing `pubspec.yaml`/`lib`/`ios`;
  - missing `.codex-work/game-engine.json`;
  - engine dependency declared without a version or without an actual runtime import;
  - missing scene entrypoint/assets/evidence;
  - Flutter-only colored-block mock with no engine-owned update/input/result/restart markers;
  - valid Flame fixture;
  - valid Godot fixture with `project.godot`, pack/resource, Swift bridge and Flutter channel/view;
  - invalid evidence paths outside the project or inside `.codex-work` when bundled runtime assets are expected;
  - missing vertical-slice state markers and missing runtime recording.

- [ ] **Step 2: Implement project parsing**

  Use only Python standard library. Parse YAML-like dependency declarations conservatively without adding a YAML dependency; inspect Dart/Swift/Godot files with bounded regexes. Never execute project code or trust prose comments as runtime ownership.

- [ ] **Step 3: Implement engine-specific checks**

  Support at least:
  - Flame: pinned `flame` dependency, `Game`/`GameWidget`/component imports, a game entrypoint, input/event hooks, update loop, result/restart methods, local scene assets.
  - Godot: `project.godot`, scene file, exported pack or equivalent local bundle, SwiftGodot/host bridge, Flutter platform view/channel, and engine-owned scene calls.
  - Unity/other: require explicit adapter evidence and reject unsupported ambiguity rather than silently passing.

- [ ] **Step 4: Implement visual/runtime evidence checks**

  Require authored subject/scene assets, at least one nontrivial visual implementation path, HUD/feedback references, lifecycle handling, and `.codex-work` evidence records containing a current iPhone build identity and recording/screenshot paths.

- [ ] **Step 5: Run the focused validator tests**

  Run `python3 -m unittest flutter_check/test_validate_game_project.py -v`; expected all fixtures pass/fail as designed.

---

### Task 3: Wire the validator and game rules into the execution skill

**Files:**
- Modify: `flutter-engine-runner/SKILL.md:93-99,379-407`
- Modify: `flutter-engine-runner/agents/openai.yaml`
- Modify: `工作流文档/02-创意与思维导图.md:111,551`
- Modify: `工作流文档/04-视觉与页面功能.md:97-123,282-293`

**Interfaces:**
- Consumes: Validator CLI from Task 2 and engine manifest contract from Task 1.
- Produces: Skill instructions that route game projects to engine-first implementation and invoke `validate_game_project.py` before gameplay expansion and before final acceptance.

- [ ] **Step 1: Add an engine-first routing paragraph**

  State that selecting a game prevents a Flutter-only mock fallback. The selected engine must own runtime scene/entity/input/update/result behavior; Flutter owns navigation/HUD/storage boundaries.

- [ ] **Step 2: Add mandatory commands and evidence outputs**

  Require:
  ```sh
  python3 <skill-root>/scripts/validate_game_project.py --project-root <target-project-root> --json
  ```
  before full gameplay expansion and again after native/build changes. Require `.codex-work/game-engine.json`, `.codex-work/game-vertical-slice.md`, `.codex-work/game-runtime.json`, and current iPhone `.mp4`/screenshots/logs.

- [ ] **Step 3: Add anti-crude-art direction**

  Require layered scene composition, authored assets, materials/lighting, camera/occlusion, animation/particle feedback, and HUD readability. Explicitly reject screenshots that resemble the supplied crude references.

- [ ] **Step 4: Add error-repair instructions**

  Require systematic repair for build-phase state mutation, layout overflow, stale engine callbacks, duplicate lifecycle registration, timeout, and input/result mismatch. No repeated identical command loops; after each fix rebuild and replay the same path.

- [ ] **Step 5: Update YAML prompt metadata and mind-map wording**

  Ensure the installed agent receives the same game route and does not describe ordinary app animation as a game engine.

---

### Task 4: Add regression coverage to workflow integrity and installer synchronization

**Files:**
- Modify: `flutter_check/test_workflow_integrity.sh`
- Modify: `flutter_check/test_onboarding_guide_workflow.sh`
- Modify: `flutter_check/test_start_remote_listing.sh` only if installer assertions need a new copied file
- Modify: `start.sh` only if the new script is not already copied by the recursive scripts step

**Interfaces:**
- Consumes: Task 1 contract, Task 2 validator path, Task 3 skill text.
- Produces: Fail-fast checks preventing the old “engine optional / static mock acceptable” wording from returning.

- [ ] **Step 1: Require game contract phrases**

  Assert engine manifest fields, vertical-slice order, scene/entity/input/update ownership, visual-quality requirements, lifecycle defect names, and release-blocking language in source docs and skill.

- [ ] **Step 2: Forbid bypass phrases**

  Reject “Flutter-only game fallback”, “colored block demo”, “static screenshot as gameplay”, “engine dependency alone passes”, “hidden game route”, and “expand content before vertical slice”.

- [ ] **Step 3: Require validator references**

  Assert `validate_game_project.py` appears in the skill, workflow order, README, and installed-script copy contract.

- [ ] **Step 4: Verify installer behavior**

  Confirm `start.sh` copies the new script with the existing recursive `scripts` copy and that installed `references/工作流文档` remains complete.

---

### Task 5: Run full verification and synchronize the installed skill

**Files:**
- Modify: generated installed copy under `/Users/admin/.codex/skills/flutter工程执行/` via `start.sh`; do not hand-edit it.

**Interfaces:**
- Consumes: all source changes and tests from Tasks 1–4.
- Produces: synchronized installed skill, passing local regression suite, and an honest runtime status for the absent user App.

- [ ] **Step 1: Run focused Python checks**

  ```sh
  python3 -m unittest flutter_check/test_validate_game_project.py -v
  python3 -m py_compile flutter-engine-runner/scripts/*.py
  ```

- [ ] **Step 2: Run full workflow regression**

  ```sh
  ./flutter_check/run_all.sh
  /bin/zsh -n start.sh flutter_check/run_all.sh flutter_check/test_workflow_integrity.sh flutter_check/test_onboarding_guide_workflow.sh
  ruby -e "require 'yaml'; YAML.load_file('flutter-engine-runner/agents/openai.yaml'); puts 'yaml ok'"
  git diff --check
  ```

- [ ] **Step 3: Reinstall the skill**

  ```sh
  /bin/zsh ./start.sh --install-only --no-open --no-clipboard
  ```

  Verify the installed validator, references, and skill text match source paths.

- [ ] **Step 4: Re-run full regression after installation**

  Run `./flutter_check/run_all.sh` again and inspect the complete output.

- [ ] **Step 5: Record runtime limitation**

  Confirm the current bundle still has no `pubspec.yaml`, `lib/`, or `ios/`; report the game runtime gate as `Blocked` until a real Flutter project root is provided. Do not build or alter Cnida/Naevo as substitutes.
