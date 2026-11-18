#!/bin/zsh

emulate -L zsh
set -euo pipefail

TASK_ROOT="${0:A:h:h}"
typeset -a TASK_CHECKS=(
  "$TASK_ROOT/flutter_done_check/test_bundle_layout.sh"
  "$TASK_ROOT/flutter_done_check/test_default_performance_tier.sh"
  "$TASK_ROOT/flutter_done_check/test_workflow_integrity.sh"
  "$TASK_ROOT/flutter_done_check/test_onboarding_guide_workflow.sh"
  "$TASK_ROOT/flutter_done_check/test_validate_visual_implementation.py"
  "$TASK_ROOT/flutter_done_check/test_validate_game_project.py"
  "$TASK_ROOT/flutter_done_check/test_prepare_ios_config.py"
  "$TASK_ROOT/flutter_done_check/test_prepare_git_handoff.py"
  "$TASK_ROOT/flutter_done_check/test_validate_flutter_navigation.py"
  "$TASK_ROOT/flutter_done_check/test_validate_protocol_urls.py"
  "$TASK_ROOT/flutter_done_check/test_validate_launch_screen_visual.py"
  "$TASK_ROOT/flutter_done_check/test_validate_review_remarks.py"
  "$TASK_ROOT/flutter_done_check/test_validate_public_copy.py"
  "$TASK_ROOT/flutter_done_check/test_validate_path_names.py"
  "$TASK_ROOT/flutter_done_check/test_start_remote_listing.sh"
  "$TASK_ROOT/flutter_done_check/test_validate_about_copy.py"
)

for TASK_CHECK in "${TASK_CHECKS[@]}"; do
  print -r -- "运行检查：${TASK_CHECK:t}"
  case "$TASK_CHECK" in
    *.py) python3 "$TASK_CHECK" ;;
    *) /bin/zsh "$TASK_CHECK" ;;
  esac
done

print -r -- "PASS: all local workflow checks completed."
