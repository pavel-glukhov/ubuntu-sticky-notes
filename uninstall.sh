#!/bin/bash
# =========================================================
# Ubuntu Sticky Notes - Safe Uninstall Script
# =========================================================
# This script removes only the application files.
# System packages (python3, GTK4, etc.) are NOT touched.
# Version: 2.0.0
# =========================================================

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Header
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Ubuntu Sticky Notes - Uninstall${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Application file locations (from build_deb_package.sh)
APP_EXEC="ubuntu-sticky-notes"
USR_BIN_PATH="/usr/local/bin/$APP_EXEC"
APP_DIR="/usr/share/ubuntu-sticky-notes"
DESKTOP_FILE="/usr/share/applications/$APP_EXEC.desktop"
METAINFO_FILE="/usr/share/metainfo/ubuntu-sticky-notes.metainfo.xml"

# User data locations
USER_DATA_DIR="$HOME/.local/share/ubuntu-sticky-notes"
USER_CONFIG_DIR="$HOME/.config/ubuntu-sticky-notes"

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ This script must be run with root privileges.${NC}"
    echo -e "${YELLOW}💡 Please use: sudo ./uninstall.sh${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠️  This will completely remove Ubuntu Sticky Notes.${NC}"
echo -e "${YELLOW}   System packages (Python, GTK4, etc.) will NOT be affected.${NC}"
echo ""

# User confirmation
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}❌ Uninstall cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}🗑️  Starting uninstall process...${NC}"
echo ""

# Stop application if running
if pgrep -f "$APP_EXEC" > /dev/null; then
    echo -e "${YELLOW}⏹️  Stopping running application...${NC}"
    pkill -f "$APP_EXEC" || true
    sleep 2
    echo -e "   ✅ Application stopped"
fi

# Remove system files
echo -e "${BLUE}📁 Removing application files...${NC}"

if [ -f "$USR_BIN_PATH" ]; then
    rm -f "$USR_BIN_PATH"
    echo -e "   ✅ Executable removed: $USR_BIN_PATH"
fi

if [ -d "$APP_DIR" ]; then
    rm -rf "$APP_DIR"
    echo -e "   ✅ Application directory removed: $APP_DIR"
fi

if [ -f "$DESKTOP_FILE" ]; then
    rm -f "$DESKTOP_FILE"
    echo -e "   ✅ Desktop entry removed: $DESKTOP_FILE"
fi

if [ -f "$METAINFO_FILE" ]; then
    rm -f "$METAINFO_FILE"
    echo -e "   ✅ Metainfo file removed: $METAINFO_FILE"
fi

# Remove .deb package if installed
echo -e "${BLUE}📦 Removing from package manager...${NC}"
if dpkg -l | grep -q "ubuntu-sticky-notes"; then
    dpkg --remove ubuntu-sticky-notes 2>/dev/null || true
    echo -e "   ✅ Removed from package manager"
else
    echo -e "   ℹ️  No package manager record found"
fi

# Remove error logs
echo -e "${BLUE}📄 Checking for error logs...${NC}"
removed_logs=0
for user_home in /home/*; do
    if [ -d "$user_home" ]; then
        user_log_dir="$user_home/.local/share/ubuntu-sticky-notes"
        if [ -d "$user_log_dir" ] && [ -f "$user_log_dir/errors.log" ]; then
            username=$(basename "$user_home")
            echo -e "   📋 Found logs for user: $username"
            ((removed_logs++))
        fi
    fi
done

if [ $removed_logs -eq 0 ]; then
    echo -e "   ℹ️  No error logs found"
fi

echo ""
echo -e "${YELLOW}❓ Do you want to remove user data as well?${NC}"
echo -e "${YELLOW}   This will DELETE all your notes and settings!${NC}"
echo -e "${YELLOW}   (Choose 'No' to keep your data)${NC}"
echo ""
read -p "Remove user data? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🗄️  Removing user data...${NC}"
    
    # Since running as root, check all user home directories
    removed_users=0
    for user_home in /home/*; do
        if [ -d "$user_home" ]; then
            username=$(basename "$user_home")
            user_data_dir="$user_home/.local/share/ubuntu-sticky-notes"
            user_config_dir="$user_home/.config/ubuntu-sticky-notes"
            
            if [ -d "$user_data_dir" ] || [ -d "$user_config_dir" ]; then
                if [ -d "$user_data_dir" ]; then
                    # Show what's being removed
                    db_file="$user_data_dir/stickies.db"
                    log_file="$user_data_dir/errors.log"
                    
                    if [ -f "$db_file" ]; then
                        note_count=$(sqlite3 "$db_file" "SELECT COUNT(*) FROM notes WHERE deleted=0" 2>/dev/null || echo "unknown")
                        echo -e "   📝 User $username: $note_count notes in database"
                    fi
                    
                    rm -rf "$user_data_dir"
                    echo -e "   ✅ Data removed for user: $username"
                fi
                
                if [ -d "$user_config_dir" ]; then
                    rm -rf "$user_config_dir"
                    echo -e "   ✅ Config removed for user: $username"
                fi
                
                ((removed_users++))
            fi
        fi
    done
    
    if [ $removed_users -eq 0 ]; then
        echo -e "   ℹ️  No user data found"
    else
        echo -e "   ${GREEN}✅ Removed data for $removed_users user(s)${NC}"
    fi
else
    echo -e "${GREEN}💾 User data preserved.${NC}"
    echo -e "${CYAN}ℹ️  Your data is located at:${NC}"
    echo -e "   📁 ~/.local/share/ubuntu-sticky-notes/ (database & logs)"
    echo -e "   ⚙️  ~/.config/ubuntu-sticky-notes/ (configuration)"
fi

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications/ 2>/dev/null || true
    echo -e "${BLUE}🔄 Desktop database updated${NC}"
fi

echo ""
echo -e "${GREEN}✅ Ubuntu Sticky Notes successfully uninstalled!${NC}"
echo ""
echo -e "${CYAN}📝 Removed components:${NC}"
echo -e "   🗂️  Application files: /usr/share/ubuntu-sticky-notes/"
echo -e "   🚀 Executable: /usr/local/bin/ubuntu-sticky-notes"
echo -e "   📱 Desktop entry: /usr/share/applications/"
echo -e "   📦 Package record (if existed)"
if [ $removed_logs -gt 0 ]; then
    echo -e "   📄 Error logs from $removed_logs user(s)"
fi
echo ""
echo -e "${YELLOW}⚠️  NOTE: System packages (python3, GTK4, etc.) were not affected.${NC}"
echo -e "${CYAN}   If you want to remove them, use: sudo apt remove python3-gi gir1.2-gtk-4.0 gir1.2-adw-1${NC}"
echo ""
echo -e "${BLUE}🙏 Thank you for using Ubuntu Sticky Notes!${NC}"
echo -e "${CYAN}   Project: https://github.com/omercngiz/ubuntu-sticky-notes${NC}"
echo ""