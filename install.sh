#!/usr/bin/env bash
set -euo pipefail

# install.sh - attempt to download latest N_m3u8DL-RE linux binary (if repository provides it)
GITHUB_REPO="nmm/N_m3u8DL-RE"  # change if necessary

echo "Querying GitHub for latest release..."
API_JSON=$(curl -s "https://api.github.com/repos/${GITHUB_REPO}/releases/latest")
ASSET_URL=$(echo "$API_JSON" | grep -E "browser_download_url.*linux|browser_download_url.*x86_64" | head -n1 | sed -E 's/.*"(https.*)".*/\1/')

if [ -z "$ASSET_URL" ]; then
  echo "No matching linux asset found automatically. You can upload N_m3u8DL-RE to the repo yourself."
  exit 0
fi

echo "Downloading: $ASSET_URL"
curl -L "$ASSET_URL" -o N_m3u8DL-RE
chmod +x N_m3u8DL-RE
ls -l N_m3u8DL-RE

echo "Done."
