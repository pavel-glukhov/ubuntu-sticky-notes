#!/bin/bash
# =========================================================
# Script to create a Debian package for Ubuntu Sticky Notes
# =========================================================

set -e  # stop on error

# ----------------------
# Define paths
# ----------------------
PACKAGE_DIR="ubuntu_sticky_notes_deb"
DEBIAN_DIR="$PACKAGE_DIR/DEBIAN"
USR_BIN_DIR="$PACKAGE_DIR/usr/local/bin"
USR_SHARE_DIR="$PACKAGE_DIR/usr/share"
APPLICATIONS_DIR="$USR_SHARE_DIR/applications"
APP_DIR="$USR_SHARE_DIR/ubuntu-sticky-notes"

APP_INFO_JSON="ubuntu-sticky-notes/app_info.json"
APP_EXEC="ubuntu-sticky-notes"
APP_ICON="/usr/share/ubuntu-sticky-notes/resources/icons/app.png"
APP_MAIN_SCRIPT="/usr/share/ubuntu-sticky-notes/main.py"

# ----------------------
# Create necessary directories if they don't exist
# ----------------------
for dir in "$DEBIAN_DIR" "$USR_BIN_DIR" "$APPLICATIONS_DIR" "$APP_DIR"; do
    [ ! -d "$dir" ] && mkdir -p "$dir"
done

# ----------------------
# Create executable script in /usr/local/bin
# ----------------------
cat > "$USR_BIN_DIR/$APP_EXEC" <<EOL
#!/bin/bash
python3 "$APP_MAIN_SCRIPT"
EOL
chmod +x "$USR_BIN_DIR/$APP_EXEC"

# ----------------------
# Copy all application files to /usr/share/ubuntu-sticky-notes
# ----------------------
cp -r ubuntu-sticky-notes/* "$APP_DIR/"

# ----------------------
# Read application info from JSON
# ----------------------
SERVICE_NAME=$(jq -r '.service_name' "$APP_INFO_JSON")
APP_NAME=$(jq -r '.app_name' "$APP_INFO_JSON")
VERSION=$(jq -r '.version' "$APP_INFO_JSON")
DESCRIPTION=$(jq -r '.description' "$APP_INFO_JSON")
MAINTAINER="$(jq -r '.author' "$APP_INFO_JSON") <$(jq -r '.email' "$APP_INFO_JSON")>"
ARCHITECTURE=$(jq -r '.architecture' "$APP_INFO_JSON")
DEPENDENCIES=$(jq -r '.dependencies | join(", ")' "$APP_INFO_JSON")

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
Description: $DESCRIPTION
EOL

# ----------------------
# Create DEBIAN/postinst to check PyQt5
# ----------------------
cat > "$DEBIAN_DIR/postinst" <<'EOL'
#!/bin/bash
# Check if PyQt5 is installed after package installation
if ! python3 -c "import PyQt5" &>/dev/null; then
    echo "PyQt5 is not installed. Please run: sudo apt install -y python3-pyqt5"
fi
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
Icon=$APP_ICON
Terminal=false
Type=Application
Categories=Utility;
StartupNotify=true
StartupWMClass=APP_NAME
EOL

# ----------------------
# Build the .deb package with flags
# ----------------------
DEB_FILE="${SERVICE_NAME}_${VERSION}_${ARCHITECTURE}.deb"
dpkg-deb --build --root-owner-group --verbose "$PACKAGE_DIR" "$DEB_FILE"

# ----------------------
# Print instructions
# ----------------------
echo ""
echo "Package built successfully: $DEB_FILE"
echo "Installation instructions:"
echo "  sudo dpkg -i $DEB_FILE"
echo "  sudo apt-get install -f  # to install missing dependencies if required"
echo ""
echo "You can launch the application from the menu or by running:"
echo "  $APP_EXEC"
