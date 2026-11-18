# Workflow Evidence Hardening Implementation Plan

> **For agentic workers:** This plan is executed inline in the current workspace. Each task ends with a focused verification command.

**Goal:** Strengthen the Flutter execution workflow with a `.codex-work` record contract, fresh evidence rules, artifact-level release gates, and a machine-readable readiness decision while preserving the package boundary between workflow checks and real App runtime validation.

**Architecture:** Keep project-owned source and delivery artifacts outside the internal `.codex-work` directory. Add small read-only Python validators under `flutter-engine-runner/scripts/`, fixture-driven checks under `flutter_done_check/`, and wire them into `run_all.sh` and `test_workflow_integrity.sh`. The validators report `Passed`, `Failed`, or `Not verified` and never turn missing real-App evidence into a pass.

**Tech Stack:** POSIX shell, Python 3 standard library, JSON/Markdown contracts, existing Flutter workflow scripts.

**Spec:** This plan is the approved implementation of the confirmed audit gaps and the requested legacy work-record directory → `.codex-work` migration.

## Global Constraints

- All internal workflow records use `.codex-work`; the user explicitly exempted this directory name from the project-owned Codex/AI naming ban.
- `aduit/` remains the only final delivery directory and must contain only approved delivery materials.
- Validators are static/preflight checks and must state when an iPhone build, simulator action, or final artifact is still `Not verified`.
- No generated Flutter App is created in this materials package.
- No Git commit, push, or remote mutation is performed by this change.

### Task 1: Rename the internal work-record contract

**Files:**
- Modify: all tracked text files containing `.codex-work`
- Modify: `flutter-engine-runner/scripts/validate_path_names.py`
- Modify: `flutter_done_check/test_workflow_integrity.sh`
- Modify: `README.md`, `工作流文档/*.md`, `flutter-engine-runner/SKILL.md`, `docs/superpowers/plans/*.md`

- [x] Replace every internal legacy work-record path with `.codex-work`.
- [x] Update path validator roots, glossary location, diagnostics, and test expectations.
- [x] Add an explicit exception sentence that the user-requested `.codex-work` record directory is exempt from the project-owned naming ban.
- [x] Remove stale prose claiming the legacy work-record directory must be migrated away.
- [x] Verify no tracked text retains a standalone legacy work-record path reference.

### Task 2: Add a machine-readable work-record schema and freshness contract

**Files:**
- Create: `工作流文档/11-记录与证据契约.md`
- Create: `flutter-engine-runner/scripts/validate_work_records.py`
- Create: `flutter_done_check/test_validate_work_records.py`
- Modify: `工作流文档/manifest.txt`, `README.md`, `flutter-engine-runner/SKILL.md`, `flutter_done_check/run_all.sh`, `flutter_done_check/test_workflow_integrity.sh`

- [x] Define required record fields: `schema_version`, `run_id`, `project_root`, `bundle_id`, `build_id`, `device`, `udid`, `recorded_at`, `status`, `evidence`, `next_action`.
- [x] Define status enum `Planned`, `In progress`, `Passed`, `Failed`, `Blocked`, `Not verified` and evidence item fields including `path`, `sha256`, `captured_at`, `source`, `kind`.
- [x] Require UTC ISO-8601 timestamps and reject future timestamps or evidence older than the record’s `freshness_window_hours`.
- [x] Require evidence identity to include the current build/device where a record claims runtime verification.
- [x] Validate a target `.codex-work/records/*.json` directory when present; report `Not verified` when the real target project or records are absent rather than silently passing.
- [x] Add fixtures for valid, stale, malformed, mismatched-build, and missing-record cases.

### Task 3: Add artifact and delivery boundary gates

**Files:**
- Create: `flutter-engine-runner/scripts/validate_ios_artifacts.py`
- Create: `flutter-engine-runner/scripts/validate_aduit_allowlist.py`
- Create: `flutter_done_check/test_validate_ios_artifacts.py`
- Create: `flutter_done_check/test_validate_aduit_allowlist.py`
- Modify: `工作流文档/06-素材与真实照片.md`, `工作流文档/07-测试与质量验收.md`, `工作流文档/08-发布与About材料.md`, `工作流文档/09-实施顺序与交付报告.md`, `README.md`, `flutter-engine-runner/SKILL.md`, `run_all.sh`, integrity test

- [x] Check actual iOS source artifacts when a target root is supplied: `Info.plist`, `AppFrameworkInfo.plist` with `MinimumOSVersion`, Podfile validity, `PERMISSION_PHOTOS=1` when PhotoKit library access is used, and absence of ATT traces.
- [x] Distinguish `Not applicable` from `Not verified` and never infer a successful archive from source text alone.
- [x] Check `aduit/` contains only the approved three policy pages, `welcome.html`, `imgs/` with exactly five PNGs when final delivery is claimed, and the preserved logo location; reject `index.html` and symlinks.
- [x] Add explicit release ordering and evidence paths for these gates.

### Task 4: Add flow, protocol, execution-state, and capability checks

**Files:**
- Create: `flutter-engine-runner/scripts/validate_welcome_flow.py`
- Create: `flutter-engine-runner/scripts/validate_execution_state.py`
- Create: `flutter-engine-runner/scripts/validate_capability_matrix.py`
- Modify: `flutter-engine-runner/scripts/validate_protocol_urls.py`
- Create: matching `flutter_done_check/test_*.py` fixtures
- Modify: workflow docs, README, skill, run_all, integrity test

- [x] Validate Welcome/Initialization rules, including `Enter`, no pause controls, clear-data-only initialization, and exactly one native Flutter Welcome entry.
- [x] Validate parallel execution state fields (`run_id`, `pid`, `started_at`, `heartbeat_at`, `retry_count`, `blocked_reason`, `resume_action`) and reject stale heartbeats for active runs.
- [x] Validate capability matrix rows, real consumer, permission/declined fallback, runtime evidence, and formula record; reject package-only entries.
- [x] Strengthen protocol URL checks for exactly three Settings entries, concrete project host, no `index.html`, and no bundle/runtime dependency on policy HTML.

### Task 5: Add release-readiness aggregation and documentation

**Files:**
- Create: `flutter-engine-runner/scripts/validate_release_readiness.py`
- Create: `flutter_done_check/test_validate_release_readiness.py`
- Modify: `工作流文档/07-测试与质量验收.md`, `工作流文档/08-发布与About材料.md`, `工作流文档/09-实施顺序与交付报告.md`, `README.md`, `flutter-engine-runner/SKILL.md`, `run_all.sh`, integrity test

- [x] Define a machine-readable `.codex-work/release-readiness.json` aggregate with gate names, status, evidence references, blocker reasons, generated timestamp, and `release_readiness`.
- [x] Allow `Ready for submission` only when every applicable gate is `Passed`, no blocker exists, and runtime/iOS/artifact evidence is fresh; otherwise return `Not ready` or `Not verified` with actionable gaps.
- [x] Add a fixture proving a missing simulator artifact cannot be reported ready.
- [x] Keep final reporting language aligned with the existing `Release readiness: Ready for submission` contract.

### Task 6: Add resource, accessibility, resilience, and security evidence

**Files:**
- Create: `flutter-engine-runner/scripts/validate_quality_records.py`
- Create: `flutter_done_check/test_validate_quality_records.py`
- Modify: `工作流文档/06-素材与真实照片.md`, `工作流文档/07-测试与质量验收.md`, `工作流文档/09-实施顺序与交付报告.md`, `工作流文档/11-记录与证据契约.md`, `README.md`, `flutter-engine-runner/SKILL.md`, `flutter_done_check/run_all.sh`, `flutter_done_check/test_bundle_layout.sh`, `flutter_done_check/test_workflow_integrity.sh`

- [x] Define `.codex-work/quality-matrix.json` for resource hashes/byte ceilings, source/license, real consumers, accessibility, resilience, and secret scanning.
- [x] Reject missing/stale resource hashes, oversized images, invalid signatures, package-only consumers, missing VoiceOver/Dynamic Type/Reduce Motion/contrast rows, missing offline/permission/background/interrupt scenarios, and secret-like values.
- [x] Make `quality_records` a required release-readiness gate and require `generated_at` plus non-empty evidence paths.
- [x] Keep missing target-project evidence as `Not verified`; never infer real-App acceptance from this materials package.

## Verification

Run after implementation:

```bash
/bin/zsh flutter_done_check/run_all.sh
python3 -m py_compile flutter-engine-runner/scripts/*.py flutter_done_check/*.py
/bin/zsh -n start.sh start.command install.command flutter_done_check/*.sh
ruby -e "require 'yaml'; YAML.load_file('flutter-engine-runner/agents/openai.yaml')"
git diff --check
```
