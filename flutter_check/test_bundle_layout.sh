#!/bin/zsh

emulate -L zsh
set -euo pipefail

TASK_ROOT="${0:A:h:h}"
TASK_CHECK_DIR="$TASK_ROOT/flutter_check"

fail() {
  print -u2 -- "FAIL: $1"
  exit 1
}

[[ -d "$TASK_CHECK_DIR" && ! -L "$TASK_CHECK_DIR" ]] || fail "缺少普通检查目录：$TASK_CHECK_DIR"
[[ ! -e "$TASK_ROOT/tests" ]] || fail "残留旧检查目录：$TASK_ROOT/tests"

typeset -a task_expected=(
  run_all.sh
  test_bundle_layout.sh
  test_default_performance_tier.sh
  test_workflow_integrity.sh
  test_onboarding_guide_workflow.sh
  test_start_remote_listing.sh
  test_validate_visual_implementation.py
  test_validate_game_project.py
  test_prepare_ios_config.py
  test_prepare_git_handoff.py
  test_validate_flutter_navigation.py
  test_validate_code_architecture.py
  test_validate_protocol_urls.py
  test_validate_launch_screen_visual.py
  test_validate_review_remarks.py
  test_validate_public_copy.py
  test_validate_path_names.py
  test_validate_about_copy.py
  test_validate_work_records.py
  test_validate_ios_artifacts.py
  test_validate_aduit_allowlist.py
  test_validate_welcome_flow.py
  test_validate_execution_state.py
  test_validate_capability_matrix.py
  test_validate_quality_records.py
  test_validate_final_visual_product.py
  test_asset_staging.py
  test_cleanup_generation_history.py
  test_validate_logo_quality.py
  test_validate_release_readiness.py
)

for task_file in "${task_expected[@]}"; do
  [[ -f "$TASK_CHECK_DIR/$task_file" && ! -L "$TASK_CHECK_DIR/$task_file" ]] || \
    fail "检查目录缺少普通文件：$TASK_CHECK_DIR/$task_file"
done

task_actual_count="$(find "$TASK_CHECK_DIR" -maxdepth 1 -type f -not -name '.DS_Store' | wc -l | tr -d ' ')"
[[ "$task_actual_count" -eq "${#task_expected[@]}" ]] || \
  fail "检查目录文件数量错误：期望 ${#task_expected[@]}，实际 $task_actual_count"

TASK_START="$TASK_ROOT/start.sh"
TASK_RUN_ALL="$TASK_CHECK_DIR/run_all.sh"
TASK_SKILL="$TASK_ROOT/flutter-engine-runner/SKILL.md"
TASK_README="$TASK_ROOT/README.md"
TASK_YAML="$TASK_ROOT/flutter-engine-runner/agents/openai.yaml"

rg -q 'TASK_BUNDLE_DIR/flutter_check/test_workflow_integrity\.sh' "$TASK_START" || \
  fail 'start.sh 未指向 flutter_check/test_workflow_integrity.sh'
if rg -q 'TASK_BUNDLE_DIR/tests/' "$TASK_START"; then
  fail 'start.sh 残留旧 tests/ 路径'
fi

for task_file in "$TASK_RUN_ALL" "$TASK_START" "$TASK_README"; do
  rg -q 'flutter_check' "$task_file" || fail "缺少新检查目录引用：$task_file"
done
ruby -e 'require "yaml"; YAML.load_file(ARGV.fetch(0));' "$TASK_YAML" >/dev/null 2>&1 || \
  fail "openai.yaml 不是有效 YAML：$TASK_YAML"
for task_file in \
  "$TASK_RUN_ALL" "$TASK_START" "$TASK_README" \
  "$TASK_ROOT/工作流文档/01-执行约定.md" \
  "$TASK_ROOT/工作流文档/07-测试与质量验收.md" \
  "$TASK_ROOT/工作流文档/09-实施顺序与交付报告.md"; do
  if rg -q 'tests/' "$task_file"; then
    fail "文件残留旧 tests/ 路径：$task_file"
  fi
done

for task_file in "${task_expected[@]:1}"; do
  rg -q "flutter_check/${task_file}" "$TASK_RUN_ALL" || \
    fail "run_all.sh 未纳入检查：$task_file"
done

if rg -q 'generation/flutter_check/build/package' "$TASK_SKILL"; then
  fail 'SKILL.md 将英文 tests 动作误替换为 flutter_check'
fi
rg -q 'generation/tests/build/package' "$TASK_SKILL" || \
  fail 'SKILL.md 缺少 generation/tests/build/package 原文'

rg -q 'TASK_PARALLEL_CHECKS' "$TASK_RUN_ALL" || \
  fail 'run_all.sh 缺少可并行静态检查清单'
rg -q 'TASK_PIDS' "$TASK_RUN_ALL" || \
  fail 'run_all.sh 缺少并行检查进程收集'
rg -q 'wait ' "$TASK_RUN_ALL" || \
  fail 'run_all.sh 缺少并行检查等待与结果汇总'
rg -q 'TASK_SEQUENTIAL_CHECKS' "$TASK_RUN_ALL" || \
  fail 'run_all.sh 缺少串行门禁清单'

print -r -- 'PASS: flutter_check layout, references, and check-list coverage are complete.'
