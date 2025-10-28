#!/bin/bash
# =========================================================
# Ubuntu Sticky Notes - Güvenli Kaldırma Scripti
# =========================================================
# Bu script sadece uygulama dosyalarını kaldırır.
# Sistem paketlerine (python3, GTK4, vs.) DOKUNMAZ.
# =========================================================

set -e

# Renkli çıktı için
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Başlık
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Ubuntu Sticky Notes - Kaldırma${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Uygulama dosya konumları (build_deb_package.sh'dan alındı)
APP_EXEC="ubuntu-sticky-notes"
USR_BIN_PATH="/usr/local/bin/$APP_EXEC"
APP_DIR="/usr/share/ubuntu-sticky-notes"
DESKTOP_FILE="/usr/share/applications/$APP_EXEC.desktop"
METAINFO_FILE="/usr/share/metainfo/ubuntu-sticky-notes.metainfo.xml"

# Kullanıcı verisi konumları
USER_DATA_DIR="$HOME/.local/share/ubuntu-sticky-notes"
USER_CONFIG_DIR="$HOME/.config/ubuntu-sticky-notes"

# Root yetkisi kontrolü
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Bu script root yetkisiyle çalıştırılmalıdır.${NC}"
    echo -e "${YELLOW}💡 Lütfen şu komutu kullanın: sudo ./uninstall.sh${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠️  Bu işlem Ubuntu Sticky Notes uygulamasını tamamen kaldıracak.${NC}"
echo -e "${YELLOW}   Sistem paketleri (Python, GTK4, vs.) etkilenmeyecek.${NC}"
echo ""

# Kullanıcı onayı
read -p "Devam etmek istediğinizden emin misiniz? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}❌ İşlem iptal edildi.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}🗑️  Kaldırma işlemi başlıyor...${NC}"
echo ""

# Uygulama çalışıyorsa durdur
if pgrep -f "$APP_EXEC" > /dev/null; then
    echo -e "${YELLOW}⏹️  Çalışan uygulama durduruluyor...${NC}"
    pkill -f "$APP_EXEC" || true
    sleep 2
fi

# Sistem dosyalarını kaldır
echo -e "${BLUE}📁 Uygulama dosyları kaldırılıyor...${NC}"

if [ -f "$USR_BIN_PATH" ]; then
    rm -f "$USR_BIN_PATH"
    echo -e "   ✅ Executable kaldırıldı: $USR_BIN_PATH"
fi

if [ -d "$APP_DIR" ]; then
    rm -rf "$APP_DIR"
    echo -e "   ✅ Uygulama dizini kaldırıldı: $APP_DIR"
fi

if [ -f "$DESKTOP_FILE" ]; then
    rm -f "$DESKTOP_FILE"
    echo -e "   ✅ Desktop entry kaldırıldı: $DESKTOP_FILE"
fi

if [ -f "$METAINFO_FILE" ]; then
    rm -f "$METAINFO_FILE"
    echo -e "   ✅ Metainfo dosyası kaldırıldı: $METAINFO_FILE"
fi

# .deb paketi varsa kaldır
echo -e "${BLUE}📦 Paket yöneticisinden kaldırılıyor...${NC}"
if dpkg -l | grep -q "ubuntu-sticky-notes"; then
    dpkg --remove ubuntu-sticky-notes 2>/dev/null || true
    echo -e "   ✅ Paket yöneticisinden kaldırıldı"
else
    echo -e "   ℹ️  Paket yöneticisinde kayıt bulunamadı"
fi

echo ""
echo -e "${YELLOW}❓ Kullanıcı verilerini de kaldırmak ister misiniz?${NC}"
echo -e "${YELLOW}   Bu işlem tüm notlarınızı ve ayarlarınızı silecek!${NC}"
echo -e "${YELLOW}   (Hayır derseniz verileriniz korunur)${NC}"
echo ""
read -p "Kullanıcı verilerini sil? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🗄️  Kullanıcı verileri kaldırılıyor...${NC}"
    
    # Root olarak çalıştığımız için tüm kullanıcıları kontrol et
    for user_home in /home/*; do
        if [ -d "$user_home" ]; then
            username=$(basename "$user_home")
            user_data_dir="$user_home/.local/share/ubuntu-sticky-notes"
            user_config_dir="$user_home/.config/ubuntu-sticky-notes"
            
            if [ -d "$user_data_dir" ]; then
                rm -rf "$user_data_dir"
                echo -e "   ✅ $username kullanıcısının verileri kaldırıldı"
            fi
            
            if [ -d "$user_config_dir" ]; then
                rm -rf "$user_config_dir"
                echo -e "   ✅ $username kullanıcısının ayarları kaldırıldı"
            fi
        fi
    done
else
    echo -e "${GREEN}💾 Kullanıcı verileri korundu.${NC}"
    echo -e "${BLUE}ℹ️  Veriler şu konumlarda:${NC}"
    echo -e "   📁 ~/.local/share/ubuntu-sticky-notes/"
    echo -e "   ⚙️  ~/.config/ubuntu-sticky-notes/"
fi

# Desktop database güncelle
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications/ 2>/dev/null || true
fi

echo ""
echo -e "${GREEN}✅ Ubuntu Sticky Notes başarıyla kaldırıldı!${NC}"
echo ""
echo -e "${BLUE}📝 Kaldırılan bileşenler:${NC}"
echo -e "   🗂️  Uygulama dosyaları: /usr/share/ubuntu-sticky-notes/"
echo -e "   🚀 Executable: /usr/local/bin/ubuntu-sticky-notes"
echo -e "   📱 Desktop entry: /usr/share/applications/"
echo -e "   📦 Paket kaydı (varsa)"
echo ""
echo -e "${YELLOW}⚠️  NOT: Sistem paketleri (python3, GTK4, vb.) etkilenmedi.${NC}"
echo -e "${BLUE}🙏 Ubuntu Sticky Notes kullandığınız için teşekkürler!${NC}"
echo ""