#!/usr/bin/env bash
# P04/P05 profile; the usual receiver/labels/retake workflow stays in record_part.sh.
set -euo pipefail
export CUE_PROTOCOL=p45
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$HERE/record_part.sh" "$@"
