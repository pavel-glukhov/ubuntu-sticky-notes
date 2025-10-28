# Ubuntu Sticky Notes

A modern, fast, and beautiful sticky notes app for Linux, built with Python, GTK 4, and libadwaita.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://python.org)
[![GTK](https://img.shields.io/badge/GTK-4.0-purple.svg)](https://gtk.org)
[![libadwaita](https://img.shields.io/badge/libadwaita-1.x-7a3.svg)](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/)


## Why you might love it

- Rich Text Editor: Bold, italic, underline, strikethrough, font size, text color, and paragraph alignment. Styles are persisted with your note.
- 10 Languages, truly global: English, Türkçe, Español, Français, Deutsch, 中文, हिन्दी, العربية, বাংলা, Русский. Switch from the menu. Your choice is saved and restored at startup.
- Clean, productive main window: Sortable columns (Title, Modified, Created), quick search, and clear actions.
- Auto‑save and crash‑safe: Your content is continuously saved (with lightweight deltas) every few seconds.
- Trash with restore: Deleted notes go to Trash. Restore or permanently delete with confirmations.
- Lightweight SQLite backend: Timestamps for created_at and updated_at; a separate settings table for preferences (like language).
- Native GTK 4 UI: Follows GNOME HIG, smooth libadwaita widgets.
- No system tray clutter: Tray support is intentionally removed for a simpler UX.


## Screenshots

You can find example screenshots in `pic/`:

- `pic/1.png`
- `pic/2.png`
- `pic/3.png` (legacy reference; tray is no longer used)


## Features in detail

### Rich text that persists

- Formatting powered by GTK TextTags and serialized into JSON alongside your note’s text.
- Styles survive app restarts: bold/italic/underline/strikethrough, font size, text color, left/center/right alignment.

### Powerful list view

- Four-column layout: Title, Modified, Created, Actions.
- 6 sorting options: Name A→Z / Z→A, Created New→Old / Old→New, Modified New→Old / Old→New.
- Fast search entry.

### Smart save & reliability

- Automatic saves happen on an interval to keep data safe with minimal overhead.
- Updated timestamps are tracked accurately (created_at stays immutable; updated_at changes on edits).

### Trash & recovery

- Delete sends a note to Trash.
- Trash window supports Restore and Permanent Delete (with safety prompts).

### Internationalization (i18n)

- Gettext-based translations live in `locale/<lang>/LC_MESSAGES/ubuntu-sticky-notes.mo`.
- Supported language codes and native names are centralized in `src/core/i18n.py`.
- Language selection is in the main window menu: Menu → Language.
- Your selection is stored in the database settings and reloaded on startup.


## Architecture overview

- Entry point: `main.py` (adds `src/` to `sys.path`, initializes i18n, starts GTK application)
- Core:
  - `src/core/i18n.py`: Gettext integration, language persistence (via database), helpers like `_()`
  - `src/core/config.py`: Paths and configuration helpers
  - `src/core/application.py`, `src/core/gtk_application.py`: App wiring (libadwaita)
- Data:
  - `src/data/database.py`: SQLite access layer
    - Tables: `notes` (id, title, content, x, y, w, h, color, deleted, deleted_at, created_at, updated_at, always_on_top, is_open)
    - Table: `settings` (key, value), used for things like `language`
- GTK app:
  - `src/gtk_app/windows/main_window.py`: Main window, list view, sort menu, search, “New Note” dialog, menu with Language & About
  - `src/gtk_app/windows/sticky_window.py`: Rich text editor window, auto-save
  - `src/gtk_app/windows/trash_window.py`: Trash list, restore/permanent delete flows
  - `src/gtk_app/dialogs/about_dialog.py`: About dialog
  - UI files under `resources/gtk/ui/*.ui`
- Utilities:
  - `compile_translations.py`: Compiles all `.po` into `.mo`


## Install

Ubuntu 22.04+ (or any distro with GTK 4 + libadwaita available). Recommended: run with the system Python so PyGObject (gi) bindings are provided by the OS.

### A) Run from source (System Python)

```bash
sudo apt update
sudo apt install -y \
  python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 gettext git

git clone https://github.com/omercngiz/ubuntu-sticky-notes.git
cd ubuntu-sticky-notes

# Compile translations (once, or whenever .po files change)
python3 compile_translations.py

# Run the app
python3 main.py
```

If GTK/libadwaita bindings are missing, the app prints clear instructions and exits.

### B) Run from source (Virtualenv with system packages)

PyGObject (gi) is provided by the OS, not pip. If you prefer a venv for your Python packages, create it with system site packages enabled:

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate

# Still need system packages from A) above
python3 main.py
```

### VS Code tasks

This repo includes useful tasks (View → Command Palette → “Run Task”):

- Run Ubuntu Sticky Notes (System Python)
- Run Ubuntu Sticky Notes (venv)


## Using the app

- Create a note: Click “+ Add”.
- Format your note: Use the toolbar for bold/italic/underline/strikethrough, font size, color, alignment.
- Sort the list: Click the sort button in the header to choose any of the 6 orderings.
- Search: Type in the search box to filter notes quickly.
- Trash: Click the trash icon to browse deleted notes, restore, or empty the trash.
- Change language: Menu → Language. Your choice is saved and loaded next time you open the app.


## Build a .deb package (optional)

There’s a helper script for creating a Debian package.

```bash
chmod +x build_deb_package.sh
./build_deb_package.sh

# Install
sudo dpkg -i ubuntu-sticky-notes_*.deb || sudo apt -f install

# Uninstall later
sudo apt remove ubuntu-sticky-notes
```


## Uninstall

If you ran from source, no system installation was performed. To remove local data only:

```bash
rm -rf ~/.local/share/ubuntu-sticky-notes
```

If you installed the .deb package:

```bash
sudo apt remove ubuntu-sticky-notes
```


## Translations (i18n)

Translations are stored in `locale/<lang>.po` and compiled to:

```
locale/<lang>/LC_MESSAGES/ubuntu-sticky-notes.mo
```

Supported languages today:

- en (English)
- tr (Türkçe)
- es (Español)
- fr (Français)
- de (Deutsch)
- zh (中文)
- hi (हिन्दी)
- ar (العربية)
- bn (বাংলা)
- ru (Русский)

Compile all translations:

```bash
python3 compile_translations.py
```

Add a new language (example: Italian):

```bash
cp locale/en.po locale/it.po
# Translate msgstr values in locale/it.po
python3 compile_translations.py
```

Then add the language code and native name in `src/core/i18n.py` under `SUPPORTED_LANGUAGES`.


## Troubleshooting

### “ImportError: No module named gi” or GTK bindings not found

Install required system packages:

```bash
sudo apt install -y python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
```

Running in a venv? Use `--system-site-packages` as shown above.

### msgfmt not found when compiling translations

```bash
sudo apt install -y gettext
```

### Where are my notes stored?

Your database is kept under the user data directory, typically:

```
~/.local/share/ubuntu-sticky-notes/stickies.db
```

It includes a `notes` table for content and a `settings` table for preferences (e.g., `language`).


## Contributing

Issues and PRs are welcome! Some easy ways to help:

- Improve translations in `locale/*.po`
- Add a new language (see i18n section)
- Report UI/UX improvements or file bugs


## License

MIT © The contributors. See [LICENSE](LICENSE).
# Ubuntu Sticky Notes

🗒️ Modern yapışkan not uygulaması - Ubuntu için Python ve GTK4/libadwaita ile geliştirildi.

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)
[![GTK](https://img.shields.io/badge/GTK-4.0-purple.svg)](https://gtk.org)

## ✨ Özellikler

- 📝 **Zengin Metin Düzenleyici**  
  Kalın, italik, altı çizili, yazı boyutu, renk ve hizalama özellikleriyle notlarınızı biçimlendirin

- � **Çok Dilli Destek**  
  10 farklı dilde kullanılabilir (Türkçe, İngilizce, İspanyolca, Fransızca, Almanca, Çince, Hintçe, Arapça, Bengalce, Rusça)

- 📊 **Tablo Görünümü**  
  Not adı, değiştirilme tarihi, oluşturulma tarihi ve eylemlerle düzenli liste görünümü

- � **Akıllı Sıralama**  
  Notlarınızı isme, oluşturulma veya değiştirilme tarihine göre artan/azalan şekilde sıralayın

- 🎨 **Özelleştirme**  
  Daha iyi organizasyon için arka plan renklerini değiştirin

- 🗑️ **Çöp Kutusu**  
  Silinen notlar çöp kutusuna gider, buradan geri yüklenebilir veya kalıcı olarak silinebilir

- 💾 **Otomatik Kaydetme**  
  Notlarınız ve biçimlendirmeleriniz otomatik olarak SQLite veritabanında saklanır

## 🚀 Kurulum

### Sistem Gereksinimleri

Ubuntu 20.04 veya daha yeni sürüm gereklidir. Diğer Linux dağıtımları da desteklenir.

### 📦 Sıfırdan Kurulum (Önerilen)

**1. Sistem bağımlılıklarını yükleyin:**

```bash
sudo apt update
sudo apt install -y python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 git gettext
```

**2. Projeyi klonlayın:**

```bash
git clone https://github.com/omercngiz/ubuntu-sticky-notes.git
cd ubuntu-sticky-notes
```

**3. Çevirileri derleyin:**

```bash
python3 compile_translations.py
```

**4. Uygulamayı çalıştırın:**

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

### 🗑️ Kaldırma (Uninstall)

Uygulamayı tamamen kaldırmak için güvenli uninstall scriptini kullanın:

```bash
# Kaynak koddan kaldırma
sudo ./uninstall.sh

# Veya .deb paketi kurduysanız
sudo /usr/share/ubuntu-sticky-notes/uninstall.sh
```

Bu script:
- ✅ **Güvenli kaldırma:** Sadece uygulama dosyalarını siler
- ✅ **Sistem koruması:** Python, GTK4 gibi sistem paketlerine dokunmaz  
- ✅ **Kullanıcı seçimi:** Notlarınızı koruma seçeneği sunar
- ✅ **Temiz kaldırma:** Tüm uygulama izlerini temizler

## 🎯 Kullanım

- **Not Oluşturma:** Ana pencereden "+ Ekle" butonuna tıklayın
- **Not Düzenleme:** Bir nota çift tıklayarak düzenleme penceresini açın
- **Biçimlendirme:** Not penceresindeki format menüsünü (Aa butonu) kullanarak metninizi biçimlendirin
  - Yazı boyutu (8-72pt)
  - Metin rengi (10+ renk seçeneği)
  - Kalın, italik, altı çizili, üstü çizili
  - Sola hizala, ortala, sağa hizala
- **Renk Değiştirme:** Not penceresindeki renk paletini kullanın
- **Sıralama:** Ana penceredeki sıralama butonunu kullanarak notları organize edin
- **Not Silme:** Silmek istediğiniz notu seçin ve sil butonuna basın
- **Çöp Kutusu:** Silinen notları görmek ve geri yüklemek için çöp kutusu simgesine tıklayın
- **Dil Değiştirme:** Sistem diliniz otomatik olarak algılanır (desteklenen diller için)

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
