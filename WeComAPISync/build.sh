#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="企业微信IP同步"
BUILD_DIR="$SCRIPT_DIR/build"
echo "=== 编译 $APP_NAME ==="
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/$APP_NAME.app/Contents/MacOS"
mkdir -p "$BUILD_DIR/$APP_NAME.app/Contents/Resources"

# 编译二进制到临时路径
clang -fobjc-arc -framework Cocoa -o /tmp/WeComAppBuild "$SCRIPT_DIR/main.m"

# 构建 .app
cp /tmp/WeComAppBuild "$BUILD_DIR/$APP_NAME.app/Contents/MacOS/WeComAPISync"
cp "$SCRIPT_DIR/Resources/AppIcon.icns" "$BUILD_DIR/$APP_NAME.app/Contents/Resources/" 2>/dev/null

# 生成 Info.plist
python3 -c "
with open('$BUILD_DIR/$APP_NAME.app/Contents/Info.plist', 'w') as f:
    f.write('''<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">
<plist version=\"1.0\">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>zh_CN</string>
    <key>CFBundleExecutable</key>
    <string>WeComAPISync</string>
    <key>CFBundleIdentifier</key>
    <string>com.wecom.ipsync</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>2.0</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>CFBundleVersion</key>
    <string>2</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
</dict>
</plist>''')
"

# 复制到桌面
DESKTOP_APP="$HOME/Desktop/$APP_NAME.app"
rm -rf "$DESKTOP_APP"
cp -R "$BUILD_DIR/$APP_NAME.app" "$DESKTOP_APP"

# 清理 provenance 并签名
python3 -c "
import subprocess, os
for root, dirs, files in os.walk('$DESKTOP_APP'):
    for name in files + dirs:
        p = os.path.join(root, name)
        for attr in ['com.apple.provenance', 'com.apple.FinderInfo', 'com.apple.fileprovider.fpfs#P']:
            subprocess.run(['xattr', '-d', attr, p], capture_output=True)
"
codesign --force --sign - "$DESKTOP_APP" 2>/dev/null

echo "✅ 构建完成！$DESKTOP_APP"
