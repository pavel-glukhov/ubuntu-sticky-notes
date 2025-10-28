# Ubuntu Sticky Notes

🗒️ Modern yapışkan not uygulaması - Ubuntu için Python ve GTK4/libadwaita ile geliştirildi.

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)
[![GTK](https://img.shields.io/badge/GTK-4.0-purple.svg)](https://gtk.org)

## ✨ Özellikler

- 📝 **Yapışkan Notlar**  
  Otomatik kaydedilen notlar oluşturun, düzenleyin ve yönetin

- 🎨 **Özelleştirme**  
  Daha iyi organizasyon için arka plan renklerini değiştirin

- 🔍 **Aranabilir Liste**  
  Tüm notlarınızı hızlı erişim ile aranabilir listede yönetin

- 🗑️ **Çöp Kutusu**  
  Silinen notlar çöp kutusuna gider, buradan geri yüklenebilir veya kalıcı olarak silinebilir

- 🖥️ **Arka Plan Çalışması**  
  Uygulama kapatıldığında arka planda çalışmaya devam eder

- � **Kalıcı Depolama**  
  Notlar ve ayarlar yerel SQLite veritabanında saklanır

- 🔔 **Sistem Tepsisi**  
  StatusNotifierItem protokolü ile sistem tepsisi entegrasyonu

## 🚀 Kurulum

### Sistem Gereksinimleri

Ubuntu 20.04 veya daha yeni sürüm gereklidir. Diğer Linux dağıtımları da desteklenir.

### 📦 Sıfırdan Kurulum (Önerilen)

**1. Sistem bağımlılıklarını yükleyin:**

```bash
sudo apt update
sudo apt install -y python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 git
```

**2. Projeyi klonlayın:**

```bash
git clone https://github.com/omercngiz/ubuntu-sticky-notes.git
cd ubuntu-sticky-notes
```

**3. Uygulamayı çalıştırın:**

```bash
python3 main.py
```

### 🔧 Geliştirici Kurulumu

Geliştirme yapacaksanız aşağıdaki adımları takip edin:

```bash
# Projeyi klonlayın
git clone https://github.com/omercngiz/ubuntu-sticky-notes.git
cd ubuntu-sticky-notes

# Sistem paketlerini erişebilen bir sanal ortam oluşturun
python3 -m venv --system-site-packages .venv
source .venv/bin/activate

# Uygulamayı çalıştırın
python3 main.py
```

### 📱 Sistem Tepsisi Entegrasyonu (İsteğe Bağlı)

GNOME/Ubuntu'da sistem tepsisi simgesi görünmesi için AppIndicator uzantısını etkinleştirin:

```bash
# AppIndicator uzantısını yükleyin
sudo apt install -y gnome-shell-extension-appindicator

# Uzantısını etkinleştirin
gnome-extensions enable ubuntu-appindicators@ubuntu.com
```

Değişikliklerin etkili olması için GNOME Shell'i yeniden başlatın (Alt+F2, 'r' yazın, Enter) veya oturumu kapatıp açın.

## 📋 .deb Paketi Oluşturma ve Kurulum

Kendi .deb paketinizi oluşturup sistemde kalıcı olarak kurmak için:

```bash
# Projeyi klonlayın (eğer henüz yapmadıysanız)
git clone https://github.com/omercngiz/ubuntu-sticky-notes.git
cd ubuntu-sticky-notes

# Build scriptini çalıştırılabilir yapın
chmod +x build_deb_package.sh

# Paketi oluşturun
./build_deb_package.sh

# Paketi kurun
sudo dpkg -i ubuntu-sticky-notes_2.0.0_all.deb

# Eksik bağımlılıkları otomatik olarak çözün
sudo apt-get install -f
```

## 🎯 Kullanım

- **Not Oluşturma:** Ana pencereden "Yeni Not" butonuna tıklayın
- **Not Düzenleme:** Bir notun üzerine çift tıklayarak düzenleyin
- **Renk Değiştirme:** Not penceresindeki renk butonlarını kullanın
- **Not Silme:** Silmek istediğiniz notu seçin ve sil butonuna basın
- **Çöp Kutusu:** Silinen notları görmek ve geri yüklemek için çöp kutusu simgesine tıklayın
- **Uygulamayı Kapatma:** Ana pencereyi kapatmak uygulamayı arka planda çalıştırır. Tamamen çıkmak için menüden "Çıkış" seçeneğini kullanın

## ⚠️ Önemli Notlar

> **Arka Plan Çalışması:** Ana pencereyi kapattığınızda uygulama arka planda çalışmaya devam eder. Uygulamayı tamamen kapatmak için uygulama menüsünden (☰) **Çıkış** seçeneğini kullanın.

> **GTK Bağımlılıkları:** Bu uygulama GTK4/libadwaita kullanır ve sistem paketleri gerektirir. PyGObject (gi) pip ile venv içine kurulamaz, sistem Python'u kullanılmalıdır.

## 🛠️ Geliştirme

VS Code'da geliştirme yapıyorsanız:
- Önceden tanımlanmış task'ları kullanın: "Run Ubuntu Sticky Notes (System Python)" veya "Run Ubuntu Sticky Notes (venv)"
- Veya doğrudan `python3 main.py` komutunu çalıştırın

## 🐛 Sorun Giderme

**"GTK4/libadwaita bindings bulunamadı" hatası:**
```bash
sudo apt install -y python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
```

**Sistem tepsisi simgesi görünmüyor:**
```bash
sudo apt install -y gnome-shell-extension-appindicator
gnome-extensions enable ubuntu-appindicators@ubuntu.com
# GNOME Shell'i yeniden başlatın: Alt+F2, 'r', Enter
```

**Uygulama başlamıyor:**
- Python 3.8+ sürümü kullandığınızdan emin olun: `python3 --version`
- Tüm sistem bağımlılıklarının yüklü olduğunu kontrol edin
- Terminal'den çalıştırarak hata mesajlarını görün: `python3 main.py`

## 📄 Lisans

Bu proje MIT Lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 🤝 Katkıda Bulunma

Katkılarınızı memnuniyetle karşılıyoruz! Issue açabilir veya pull request gönderebilirsiniz.

---

**Sürüm:** 2.0.0  
**Geliştirici:** Pavel Glukhov (Orijinal), Ömer Can Giz (Fork)  
**Repository:** https://github.com/omercngiz/ubuntu-sticky-notes
