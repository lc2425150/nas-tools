#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_NAME="企业微信IP同步"
BUILD_DIR="$PROJECT_DIR/build"
APP_DIR="$BUILD_DIR/$APP_NAME.app"

rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources/sync"

clang -fobjc-arc -framework Cocoa -framework SystemConfiguration \
  -o "$APP_DIR/Contents/MacOS/WeComAPISync" \
  "$PROJECT_DIR/app/main.m"

cp "$PROJECT_DIR/sync/"*.py "$APP_DIR/Contents/Resources/sync/"
cp "$PROJECT_DIR/sync/wecom_sync" "$APP_DIR/Contents/Resources/sync/"
chmod +x "$APP_DIR/Contents/Resources/sync/wecom_sync"

if [ -f "$PROJECT_DIR/Resources/AppIcon.icns" ]; then
  cp "$PROJECT_DIR/Resources/AppIcon.icns" "$APP_DIR/Contents/Resources/AppIcon.icns"
fi
if [ -f "$PROJECT_DIR/Resources/StatusIconTemplate.png" ]; then
  cp "$PROJECT_DIR/Resources/StatusIconTemplate.png" "$APP_DIR/Contents/Resources/StatusIconTemplate.png"
fi

cat > "$APP_DIR/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>zh_CN</string>
  <key>CFBundleExecutable</key>
  <string>WeComAPISync</string>
  <key>CFBundleIconFile</key>
  <string>AppIcon</string>
  <key>CFBundleIdentifier</key>
  <string>com.wecom.ipsync</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>$APP_NAME</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>4.0</string>
  <key>CFBundleSignature</key>
  <string>????</string>
  <key>CFBundleVersion</key>
  <string>4</string>
  <key>LSMinimumSystemVersion</key>
  <string>11.0</string>
  <key>NSRequiresAquaSystemAppearance</key>
  <true/>
</dict>
</plist>
PLIST

xattr -cr "$APP_DIR" 2>/dev/null || true
codesign --force --sign - "$APP_DIR" >/dev/null 2>&1 || true

echo "$APP_DIR"
