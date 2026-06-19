#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="企业微信IP自动同步"
BUILD_DIR="$SCRIPT_DIR/build"
echo "=== 编译 $APP_NAME ==="
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/$APP_NAME.app/Contents/MacOS"
mkdir -p "$BUILD_DIR/$APP_NAME.app/Contents/Resources"

# 编译到临时路径（避免中文路径bug）
clang -fobjc-arc -framework Cocoa -o /tmp/WeComSyncBuild "$SCRIPT_DIR/main.m"
cp /tmp/WeComSyncBuild "$BUILD_DIR/$APP_NAME.app/Contents/MacOS/WeComAPISync"

# 图标
if [ -f "$SCRIPT_DIR/Resources/AppIcon.icns" ]; then
    cp "$SCRIPT_DIR/Resources/AppIcon.icns" "$BUILD_DIR/$APP_NAME.app/Contents/Resources/"
fi

# Info.plist
cat > "$BUILD_DIR/$APP_NAME.app/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>WeComAPISync</string>
    <key>CFBundleIdentifier</key>
    <string>com.wecom.apisync</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>2.0</string>
    <key>CFBundleVersion</key>
    <string>2</string>
    <key>NSAppTransportSecurity</key>
    <dict><key>NSAllowsArbitraryLoads</key><true/></dict>
</dict>
</plist>
PLIST

# 复制到桌面
DESKTOP_APP="$HOME/Desktop/$APP_NAME.app"
rm -rf "$DESKTOP_APP"
cp -R "$BUILD_DIR/$APP_NAME.app" "$DESKTOP_APP"
xattr -cr "$DESKTOP_APP" 2>/dev/null

echo "✅ 构建完成！大小: $(du -sh "$DESKTOP_APP" | cut -f1)"
