#!/usr/bin/env bash
# Install everything needed to run the server on a fresh Ubuntu/Debian box.
# Run as root or with sudo:  bash server/scripts/setup_server.sh
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
LIB="$REPO/lemo-opuscar"

echo "==> system packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y curl ca-certificates git xz-utils ffmpeg

# lemo-opuscar mux.sh requires ffmpeg 7+ (6.x under-reports audio length under loudnorm).
ffver="$(ffmpeg -version 2>/dev/null | head -1 | grep -oE '[0-9]+\.[0-9]+' | head -1 || echo 0)"
if [ "$(printf '%s\n' "7.0" "$ffver" | sort -V | head -1)" != "7.0" ]; then
  echo "==> ffmpeg $ffver is too old, installing ffmpeg 7 static build"
  curl -L -o /tmp/ffmpeg.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
  tar -xf /tmp/ffmpeg.tar.xz -C /tmp
  install -m 755 /tmp/ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ffmpeg
  install -m 755 /tmp/ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ffprobe
fi
echo "ffmpeg: $(ffmpeg -version | head -1)"

# Node 20+
if ! command -v node >/dev/null 2>&1 || [ "$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)" -lt 20 ]; then
  echo "==> installing Node 20"
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi
echo "node: $(node -v)"

# Python 3.11+
if ! command -v python3 >/dev/null 2>&1; then
  apt-get install -y python3 python3-venv python3-pip
fi
echo "python: $(python3 --version)"

echo "==> lemo-opuscar core deps (no local voice models; voice is MiniMax API)"
(cd "$LIB" && bash plugin/skills/lemo-opuscar/scripts/setup.sh deps)

echo "==> server venv"
python3 -m venv "$REPO/server/.venv"
"$REPO/server/.venv/bin/pip" install --upgrade pip
"$REPO/server/.venv/bin/pip" install -r "$REPO/server/requirements.txt"

echo
echo "==> done. Next:"
echo "    1. cp server/.env.example server/.env  and fill in keys + AGENT_CMD"
echo "    2. bash server/scripts/smoke_test.sh"
echo "    3. bash server/scripts/run_local.sh"
