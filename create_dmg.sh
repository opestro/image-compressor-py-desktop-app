#!/bin/bash

# Create DMG installer for ImageCompressor
# This script creates a nice disk image for distributing the app

APP_NAME="ImageCompressor"
APP_PATH="dist/${APP_NAME}.app"
DMG_NAME="${APP_NAME}_Installer"
TEMP_DMG="temp_${DMG_NAME}.dmg"
FINAL_DMG="${DMG_NAME}.dmg"

# Check if app exists
if [ ! -d "$APP_PATH" ]; then
    echo "❌ Error: $APP_PATH not found!"
    echo "Please build the app first using: python build_multiplatform.py"
    exit 1
fi

echo "🚀 Creating DMG installer for $APP_NAME..."

# Clean up any existing DMG files
rm -f "$TEMP_DMG" "$FINAL_DMG"

# Create a temporary DMG
echo "📦 Creating temporary disk image..."
hdiutil create -size 100m -fs HFS+ -volname "$APP_NAME" "$TEMP_DMG"

# Mount the temporary DMG
echo "💿 Mounting disk image..."
hdiutil attach "$TEMP_DMG" -mountpoint "/Volumes/$APP_NAME"

# Copy the app to the mounted volume
echo "📋 Copying application..."
cp -R "$APP_PATH" "/Volumes/$APP_NAME/"

# Create a symbolic link to Applications folder
echo "🔗 Creating Applications link..."
ln -s /Applications "/Volumes/$APP_NAME/Applications"

# Create a nice background and layout (optional)
mkdir "/Volumes/$APP_NAME/.background"
if [ -f "assets/dmg_background.png" ]; then
    cp "assets/dmg_background.png" "/Volumes/$APP_NAME/.background/"
fi

# Set custom icon for the volume (if available)
if [ -f "assets/logo.icns" ]; then
    cp "assets/logo.icns" "/Volumes/$APP_NAME/.VolumeIcon.icns"
    SetFile -c icnC "/Volumes/$APP_NAME/.VolumeIcon.icns"
    SetFile -a C "/Volumes/$APP_NAME"
fi

echo "⏳ Waiting for Finder to process changes..."
sleep 2

# Unmount the temporary DMG
echo "📤 Ejecting disk image..."
hdiutil detach "/Volumes/$APP_NAME"

# Convert to compressed, read-only DMG
echo "🗜️ Creating final compressed DMG..."
hdiutil convert "$TEMP_DMG" -format UDZO -o "$FINAL_DMG"

# Clean up temporary DMG
rm -f "$TEMP_DMG"

echo "✅ DMG created successfully: $FINAL_DMG"
echo ""
echo "📋 Installation Instructions:"
echo "1. Double-click $FINAL_DMG to open it"
echo "2. Drag $APP_NAME.app to the Applications folder"
echo "3. Eject the disk image"
echo "4. Launch $APP_NAME from Applications or Spotlight"
echo ""
echo "🎉 Your app is ready for distribution!" 