#!/bin/zsh

emulate -L zsh
set -euo pipefail

TASK_ROOT="${0:A:h:h}"
typeset -a TASK_SEQUENTIAL_CHECKS=(
  "$TASK_ROOT/flutter_check/test_bundle_layout.sh"
)

# After the layout prerequisite, all remaining checks read isolated fixtures
# and do not build/install or control the same App. Run them together; their
# output is replayed in the original list order after every process finishes.
typeset -a TASK_PARALLEL_CHECKS=(
  "$TASK_ROOT/flutter_check/test_default_performance_tier.sh"
  "$TASK_ROOT/flutter_check/test_workflow_integrity.sh"
  "$TASK_ROOT/flutter_check/test_onboarding_guide_workflow.sh"
  "$TASK_ROOT/flutter_check/test_validate_visual_implementation.py"
  "$TASK_ROOT/flutter_check/test_validate_game_project.py"
  "$TASK_ROOT/flutter_check/test_prepare_ios_config.py"
  "$TASK_ROOT/flutter_check/test_prepare_git_handoff.py"
  "$TASK_ROOT/flutter_check/test_validate_flutter_navigation.py"
  "$TASK_ROOT/flutter_check/test_validate_code_architecture.py"
  "$TASK_ROOT/flutter_check/test_validate_protocol_urls.py"
  "$TASK_ROOT/flutter_check/test_validate_launch_screen_visual.py"
  "$TASK_ROOT/flutter_check/test_validate_review_remarks.py"
  "$TASK_ROOT/flutter_check/test_validate_public_copy.py"
  "$TASK_ROOT/flutter_check/test_validate_path_names.py"
  "$TASK_ROOT/flutter_check/test_start_remote_listing.sh"
  "$TASK_ROOT/flutter_check/test_validate_about_copy.py"
  "$TASK_ROOT/flutter_check/test_validate_work_records.py"
  "$TASK_ROOT/flutter_check/test_validate_ios_artifacts.py"
  "$TASK_ROOT/flutter_check/test_validate_aduit_allowlist.py"
  "$TASK_ROOT/flutter_check/test_validate_welcome_flow.py"
  "$TASK_ROOT/flutter_check/test_validate_execution_state.py"
  "$TASK_ROOT/flutter_check/test_validate_capability_matrix.py"
  "$TASK_ROOT/flutter_check/test_validate_quality_records.py"
  "$TASK_ROOT/flutter_check/test_validate_final_visual_product.py"
  "$TASK_ROOT/flutter_check/test_asset_staging.py"
  "$TASK_ROOT/flutter_check/test_cleanup_generation_history.py"
  "$TASK_ROOT/flutter_check/test_validate_logo_quality.py"
  "$TASK_ROOT/flutter_check/test_validate_release_readiness.py"
)

TASK_RUN_TMP="$(mktemp -d "${TMPDIR:-/tmp}/flutter-check-run.XXXXXX")"
trap 'rm -rf -- "$TASK_RUN_TMP"' EXIT

run_check() {
  local task_check="$1"
  case "$task_check" in
    *.py) python3 "$task_check" ;;
    *) /bin/zsh "$task_check" ;;
  esac
}

for TASK_CHECK in "${TASK_SEQUENTIAL_CHECKS[@]}"; do
  print -r -- "运行检查：${TASK_CHECK:t}"
  run_check "$TASK_CHECK"
done

typeset -a TASK_PIDS=()
typeset -a TASK_OUTPUTS=()
typeset -a TASK_STATUSES=()
for TASK_INDEX in {1..${#TASK_PARALLEL_CHECKS}}; do
  TASK_CHECK="${TASK_PARALLEL_CHECKS[$TASK_INDEX]}"
  TASK_OUTPUT="$TASK_RUN_TMP/$TASK_INDEX.log"
  TASK_OUTPUTS[$TASK_INDEX]="$TASK_OUTPUT"
  (run_check "$TASK_CHECK") >"$TASK_OUTPUT" 2>&1 &
  TASK_PID=$!
  TASK_PIDS[$TASK_INDEX]="$TASK_PID"
done

TASK_FAILED=0
for TASK_INDEX in {1..${#TASK_PARALLEL_CHECKS}}; do
  if wait "${TASK_PIDS[$TASK_INDEX]}"; then
    TASK_STATUSES[$TASK_INDEX]=0
  else
    TASK_STATUSES[$TASK_INDEX]=$?
    TASK_FAILED=1
  fi
done

for TASK_INDEX in {1..${#TASK_PARALLEL_CHECKS}}; do
  TASK_CHECK="${TASK_PARALLEL_CHECKS[$TASK_INDEX]}"
  print -r -- "运行检查：${TASK_CHECK:t}"
  cat "${TASK_OUTPUTS[$TASK_INDEX]}"
  if (( TASK_STATUSES[$TASK_INDEX] != 0 )); then
    print -u2 -- "检查失败：${TASK_CHECK:t}（退出码 ${TASK_STATUSES[$TASK_INDEX]}）"
  fi
done

(( TASK_FAILED == 0 )) || exit 1
print -r -- "PASS: all local workflow checks completed."
