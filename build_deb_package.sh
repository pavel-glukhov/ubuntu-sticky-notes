#!/bin/bash
# =========================================================
# Script to create a Debian package for Ubuntu Sticky Notes
# =========================================================

set -e

PACKAGE_DIR="ubuntu_sticky_notes_deb"
DEBIAN_DIR="$PACKAGE_DIR/DEBIAN"
USR_BIN_DIR="$PACKAGE_DIR/usr/local/bin"
USR_SHARE_DIR="$PACKAGE_DIR/usr/share"
APPLICATIONS_DIR="$USR_SHARE_DIR/applications"
APP_DIR="$USR_SHARE_DIR/ubuntu-sticky-notes"
METAINFO_DIR="$USR_SHARE_DIR/metainfo"
APP_INFO_JSON="src/core/app_info.json"
APP_EXEC="ubuntu-sticky-notes"
APP_MAIN_SCRIPT="/usr/share/ubuntu-sticky-notes/main.py"
ICON_PATH="/usr/share/ubuntu-sticky-notes/resources/icons/app.png"

# ----------------------
# Create necessary directories if they don't exist
# ----------------------
for dir in "$DEBIAN_DIR" "$USR_BIN_DIR" "$APPLICATIONS_DIR" "$APP_DIR" "$METAINFO_DIR"; do
    [ ! -d "$dir" ] && mkdir -p "$dir"
done

# ----------------------
# Copy application to /usr/share/ubuntu-sticky-notes (refactored layout)
# ----------------------
cp main.py "$APP_DIR/"
cp -r src "$APP_DIR/"
cp -r resources "$APP_DIR/"

# ----------------------
# Read application info from JSON
# ----------------------
SERVICE_NAME=$(jq -r '.service_name' "$APP_INFO_JSON")
APP_NAME=$(jq -r '.app_name' "$APP_INFO_JSON")
VERSION=$(jq -r '.version' "$APP_INFO_JSON")
DESCRIPTION=$(jq -r '.description' "$APP_INFO_JSON")
AUTHOR=$(jq -r '.author' "$APP_INFO_JSON")
EMAIL=$(jq -r '.email' "$APP_INFO_JSON")
MAINTAINER="$AUTHOR <$EMAIL>"
ARCHITECTURE=$(jq -r '.architecture' "$APP_INFO_JSON")
DEPENDENCIES=$(jq -r '.dependencies | join(", ")' "$APP_INFO_JSON")
WEBSITE=$(jq -r '.website' "$APP_INFO_JSON")
LICENSE=$(jq -r '.license' "$APP_INFO_JSON")

# ----------------------
# Create executable script in /usr/local/bin
# ----------------------
cat > "$USR_BIN_DIR/$APP_EXEC" <<EOL
#!/bin/bash
python3 "$APP_MAIN_SCRIPT"
EOL
chmod +x "$USR_BIN_DIR/$APP_EXEC"

# ----------------------
# Create DEBIAN/control file
# ----------------------
cat > "$DEBIAN_DIR/control" <<EOL
Package: $SERVICE_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCHITECTURE
Depends: $DEPENDENCIES
Maintainer: $MAINTAINER
Vendor: $AUTHOR
Homepage: $WEBSITE
Description: $DESCRIPTION
EOL

# ----------------------
# Create DEBIAN/postinst to check GTK/GI
# ----------------------
cat > "$DEBIAN_DIR/postinst" <<'EOL'
#!/bin/bash
# Check if GTK4/libadwaita GI bindings are installed after package installation
python3 - <<'PY'
try:
  import gi
  gi.require_version('Gtk', '4.0')
  gi.require_version('Adw', '1')
  from gi.repository import Gtk, Adw  # noqa: F401
  print('GTK4/libadwaita GI found')
except Exception as e:
  print('GTK4/libadwaita not available. Please install:', e)
  print('  sudo apt update')
  print('  sudo apt install -y python3-gi gir1.2-gtk-4.0 gir1.2-adw-1')
PY
EOL
chmod +x "$DEBIAN_DIR/postinst"

# ----------------------
# Create desktop entry file
# ----------------------
DESKTOP_FILE="$APPLICATIONS_DIR/$APP_EXEC.desktop"
cat > "$DESKTOP_FILE" <<EOL
[Desktop Entry]
Name=$APP_NAME
Comment=$DESCRIPTION
Exec=/usr/local/bin/$APP_EXEC
Icon=$ICON_PATH
Terminal=false
Type=Application
Categories=Utility;
StartupNotify=true
StartupWMClass=$APP_NAME
EOL

# ----------------------
# Create AppStream metainfo file
# ----------------------
METAINFO_FILE="$METAINFO_DIR/$SERVICE_NAME.metainfo.xml"
cat > "$METAINFO_FILE" <<EOL
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>$APP_EXEC.desktop</id>
  <name>$APP_NAME</name>
  <summary>$DESCRIPTION</summary>
  <developer_name>$AUTHOR</developer_name>
  <description>
    <p>$DESCRIPTION</p>
  </description>
  <url type="homepage">$WEBSITE</url>
  <project_license>$LICENSE</project_license>
</component>
EOL

# ----------------------
# Build the .deb package with flags
# ----------------------
DEB_FILE="${SERVICE_NAME}_${VERSION}_${ARCHITECTURE}.deb"
dpkg-deb --build --root-owner-group --verbose "$PACKAGE_DIR" "$DEB_FILE"

echo ""
echo "Package built successfully: $DEB_FILE"
echo "Installation instructions:"
echo "  sudo dpkg -i $DEB_FILE"
echo "  sudo apt-get install -f  # to install missing dependencies if required"
echo ""
echo "You can launch the application from the menu or by running:"
echo "  $APP_EXEC"
