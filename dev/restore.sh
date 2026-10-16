#!/bin/bash
# Put the build sources back where the build scripts expect them, then build index.html.
# Usage (from the repo root): bash dev/restore.sh && python3 /home/claude/build_skyline.py && cp /mnt/user-data/outputs/skyline.html index.html
set -e
R="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p /home/claude/twbuild /home/claude/mock /mnt/user-data/outputs
cp "$R"/dev/src/*.py "$R"/dev/src/*.js /home/claude/
for f in daily_climate.html model_analysis.html quick_view.html; do cp "$R/dev/src/$f" /home/claude/; done
cp "$R/dev/src/the_weather.html" /mnt/user-data/outputs/the_weather.html
cp "$R"/dev/twbuild/* /home/claude/twbuild/
cp "$R"/dev/mock/* /home/claude/mock/
if [ ! -x /home/claude/twbuild/tailwindcss ]; then
  curl -sL -o /home/claude/twbuild/tailwindcss https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-linux-x64
  chmod +x /home/claude/twbuild/tailwindcss
fi
echo "Restored. Build: python3 /home/claude/build_skyline.py  (writes /mnt/user-data/outputs/skyline.html)"
