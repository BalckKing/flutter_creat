#!/bin/zsh
TASK_BUNDLE_DIR="${0:A:h}"
exec /bin/zsh "$TASK_BUNDLE_DIR/start.sh" --install-only "$@"
