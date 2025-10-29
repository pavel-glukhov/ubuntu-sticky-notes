"""Internationalization support for Ubuntu Sticky Notes.

Uses Python's gettext for translation management.
Supports multiple languages with easy extensibility.
"""

from __future__ import annotations
import gettext
import locale
import os
from pathlib import Path
from typing import Optional

# Get locale directory
LOCALE_DIR = Path(__file__).parent.parent.parent / "locale"

# Supported languages
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'tr': 'Türkçe',
    'es': 'Español',
    'fr': 'Français',
    'de': 'Deutsch',
    'zh': '中文',
    'hi': 'हिन्दी',
    'ar': 'العربية',
    'bn': 'বাংলা',
    'ru': 'Русский',
}

# Current language (default: system or English)
_current_lang: Optional[str] = None
_translator: Optional[gettext.GNUTranslations] = None


def init_translation(lang: Optional[str] = None) -> None:
    """
    Initialize translation system.
    
    Args:
        lang: Language code (e.g., 'en', 'tr', 'es'). If None, uses saved preference or system default.
    """
    global _current_lang, _translator
    
    if lang is None:
        # First try to get saved language preference
        try:
            from data.database import NotesDB
            db = NotesDB()
            saved_lang = db.get_setting("language")
            if saved_lang and saved_lang in SUPPORTED_LANGUAGES:
                lang = saved_lang
        except (ImportError, RuntimeError, OSError) as e:
            # Database might not be available yet or corrupted
            print(f"Could not load language preference from database: {e}")
        
        # If no saved preference, try system language
        if lang is None:
            try:
                system_lang = locale.getdefaultlocale()[0]
                if system_lang:
                    lang = system_lang.split('_')[0]  # Get 'tr' from 'tr_TR'
            except (ValueError, TypeError):
                # Locale detection failed, use English
                lang = 'en'
    
    # Fallback to English if language not supported
    if lang not in SUPPORTED_LANGUAGES:
        lang = 'en'
    
    _current_lang = lang
    
    try:
        _translator = gettext.translation(
            'ubuntu-sticky-notes',
            localedir=str(LOCALE_DIR),
            languages=[lang],
            fallback=True
        )
    except Exception as e:
        print(f"Translation init failed: {e}, using fallback")
        _translator = gettext.NullTranslations()


def _(text: str) -> str:
    """Translate text to current language.
    
    Args:
        text: Text to translate (in English)
    
    Returns:
        Translated text in the current language
    """
    global _translator
    
    if _translator is None:
        init_translation()
    
    return _translator.gettext(text) if _translator else text


def get_current_language() -> str:
    """Get current language code.
    
    Returns:
        Language code (e.g., 'en', 'tr', 'es')
    """
    global _current_lang
    if _current_lang is None:
        init_translation()
    return _current_lang or 'en'


def get_language_name(lang_code: str) -> str:
    """Get language name from code.
    
    Args:
        lang_code: Language code (e.g., 'en', 'tr')
    
    Returns:
        Native language name (e.g., 'English', 'Türkçe')
    """
    return SUPPORTED_LANGUAGES.get(lang_code, 'Unknown')


def get_supported_languages() -> dict[str, str]:
    """Get dictionary of supported languages.
    
    Returns:
        Dictionary mapping language codes to native names
    """
    return SUPPORTED_LANGUAGES


def set_language(lang: str) -> bool:
    """Change current language and save to database.
    
    Language change takes effect immediately without restart.
    
    Args:
        lang: Language code (e.g., 'en', 'tr', 'es')
    
    Returns:
        True if language was changed successfully, False otherwise
    """
    global _current_lang, _translator
    
    if lang not in SUPPORTED_LANGUAGES:
        print(f"Unsupported language: {lang}")
        return False
    
    # Save to database
    try:
        from data.database import NotesDB
        db = NotesDB()
        db.set_setting("language", lang)
    except (ImportError, RuntimeError, OSError) as e:
        print(f"Failed to save language preference: {e}")
        return False
    
    # Update current translation
    _current_lang = lang
    
    try:
        _translator = gettext.translation(
            'ubuntu-sticky-notes',
            localedir=str(LOCALE_DIR),
            languages=[lang],
            fallback=True
        )
    except Exception as e:
        print(f"Translation init failed: {e}, using fallback")
        _translator = gettext.NullTranslations()
        return False
    
    return True


# Initialize on module import
init_translation()
