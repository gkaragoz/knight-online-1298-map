#!/usr/bin/env bash
# Rebuild index.html from the upstream Open-KO data.
#
#   ./build.sh            clone/update data, build, open the map
#   ./build.sh --no-open  build without opening a browser
#
# Needs: git, python3. Pillow is installed into a local .venv.
# Data and venv land in ./data and ./.venv (both git-ignored). Re-runnable.

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

OPEN=1; [ "${1:-}" = "--no-open" ] && OPEN=0
DATA="data"; VENV=".venv"
export GIT_LFS_SKIP_SMUDGE=1

say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
die() { printf '\033[31mError: %s\033[0m\n' "$*" >&2; exit 1; }

command -v git >/dev/null     || die "git not found."
command -v python3 >/dev/null || die "python3 not found."

mkdir -p "$DATA"

say "OpenKO-db (spawn & monster data)"
if [ -d "$DATA/OpenKO-db/.git" ]; then
  git -C "$DATA/OpenKO-db" pull --ff-only --depth 1 || echo "Using existing copy."
else
  git clone --depth 1 https://github.com/Open-KO/OpenKO-db "$DATA/OpenKO-db"
fi

say "ko-client-assets @ openko-1298 (Zones/ minimaps only)"
A="$DATA/ko-client-assets"
if [ -d "$A/.git" ]; then
  git -C "$A" pull --ff-only --depth 1 || echo "Using existing copy."
else
  git clone --depth 1 --branch openko-1298 --filter=blob:none --sparse \
    https://github.com/Open-KO/ko-client-assets "$A"
  git -C "$A" sparse-checkout set Zones
fi

say "Python environment (Pillow)"
[ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --quiet --upgrade pip
"$VENV/bin/python" -m pip install --quiet pillow

say "Building index.html"
"$VENV/bin/python" build.py "$DATA/OpenKO-db/ManualSetup" "$A/Zones"

OUT="$(pwd)/index.html"
say "Done: $OUT"
if [ "$OPEN" = 1 ]; then
  if   command -v open     >/dev/null; then open "$OUT"
  elif command -v xdg-open >/dev/null; then xdg-open "$OUT" >/dev/null 2>&1 || true
  fi
fi
