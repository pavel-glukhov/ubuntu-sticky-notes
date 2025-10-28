"""Internationalization support for Ubuntu Sticky Notes.

Uses Python's gettext for translation management.
Supports multiple languages with easy extensibility.
"""

import gettext
import os
from pathlib import Path

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
_current_lang = None
_translator = None


def init_translation(lang=None):
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
        except:
            pass
        
        # If no saved preference, try system language
        if lang is None:
            import locale
            try:
                system_lang = locale.getdefaultlocale()[0]
                if system_lang:
                    lang = system_lang.split('_')[0]  # Get 'tr' from 'tr_TR'
            except:
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


def _(text):
    """
    Translate text to current language.
    
    Args:
        text: Text to translate (in English)
    
    Returns:
        Translated text
    """
    global _translator
    
    if _translator is None:
        init_translation()
    
    return _translator.gettext(text)


def get_current_language():
    """Get current language code."""
    global _current_lang
    if _current_lang is None:
        init_translation()
    return _current_lang


def get_language_name(lang_code):
    """Get language name from code."""
    return SUPPORTED_LANGUAGES.get(lang_code, 'Unknown')


def get_supported_languages():
    """Get list of supported languages."""
    return SUPPORTED_LANGUAGES


def set_language(lang):
    """
    Change current language and save to database.
    
    Args:
        lang: Language code
    """
    # Save to database
    try:
        from data.database import NotesDB
        db = NotesDB()
        db.set_setting("language", lang)
    except Exception as e:
        print(f"Failed to save language preference: {e}")
    
    # Update current translation
    init_translation(lang)


# Initialize on module import
init_translation()
