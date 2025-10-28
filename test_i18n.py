#!/usr/bin/env python3
"""
Test script to verify i18n translations
"""
import sys
import os

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "src")
sys.path.insert(0, src_path)

from core.i18n import init_translation, set_language, get_current_language, _

print("=" * 60)
print("Ubuntu Sticky Notes - Translation Test")
print("=" * 60)

# Test default language (system locale)
init_translation()
print(f"\n1. Default language: {get_current_language()}")
print(f"   'Sticky Notes' → '{_('Sticky Notes')}'")
print(f"   'New Note' → '{_('New Note')}'")
print(f"   'Delete' → '{_('Delete')}'")

# Test Turkish
print(f"\n2. Switching to Turkish...")
set_language("tr")
print(f"   Current language: {get_current_language()}")
print(f"   'Sticky Notes' → '{_('Sticky Notes')}'")
print(f"   'New Note' → '{_('New Note')}'")
print(f"   'Delete' → '{_('Delete')}'")

# Test English
print(f"\n3. Switching to English...")
set_language("en")
print(f"   Current language: {get_current_language()}")
print(f"   'Sticky Notes' → '{_('Sticky Notes')}'")
print(f"   'New Note' → '{_('New Note')}'")
print(f"   'Delete' → '{_('Delete')}'")

# Test unsupported language (should fallback to English)
print(f"\n4. Switching to unsupported language (ja)...")
set_language("ja")
print(f"   Current language: {get_current_language()}")
print(f"   'Sticky Notes' → '{_('Sticky Notes')}'")
print(f"   'New Note' → '{_('New Note')}'")
print(f"   'Delete' → '{_('Delete')}'")

print("\n" + "=" * 60)
print("Translation test completed!")
print("=" * 60)
