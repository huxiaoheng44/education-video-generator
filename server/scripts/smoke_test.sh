#!/usr/bin/env bash
# Verify the environment before/after setup. Fails loudly on any missing piece.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
LIB="$REPO/lemo-opuscar"
ok=1

check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "OK   $label"; else echo "FAIL $label"; ok=0; fi
}

check "node >= 20"        bash -c '[ "$(node -p "process.versions.node.split(\".\")[0]")" -ge 20 ]'
check "python3 >= 3.11"   bash -c '[ "$(python3 -c "import sys;print(sys.version_info[1])")" -ge 11 ]'
check "ffmpeg >= 7"       bash -c '[ "$(ffmpeg -version | head -1 | grep -oE "[0-9]+\.[0-9]+" | head -1 | cut -d. -f1)" -ge 7 ]'
check "git"               git --version

if [ -d "$LIB" ]; then echo "OK   lemo-opuscar present"; else echo "FAIL lemo-opuscar missing at $LIB"; ok=0; fi
if [ -f "$REPO/server/tts_minimax.py" ]; then echo "OK   tts_minimax present"; else echo "FAIL tts_minimax missing"; ok=0; fi

echo
if [ "$ok" = 1 ]; then echo "ALL CHECKS PASSED"; else echo "SOME CHECKS FAILED"; exit 1; fi
