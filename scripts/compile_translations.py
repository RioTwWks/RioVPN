"""Compile message catalogs."""

import subprocess
from pathlib import Path


def compile_translations():
    """Compile .po files to .mo files."""
    locales_dir = Path(__file__).parent / "locales"

    for locale_dir in locales_dir.iterdir():
        if locale_dir.is_dir():
            po_file = locale_dir / "LC_MESSAGES" / "messages.po"
            mo_file = locale_dir / "LC_MESSAGES" / "messages.mo"

            if po_file.exists():
                print(f"Compiling {locale_dir.name}...")
                subprocess.run(
                    ["msgfmt", "-o", str(mo_file), str(po_file)],
                    check=True,
                )
                print(f"  ✓ {mo_file}")

    print("\nTranslations compiled successfully!")


if __name__ == "__main__":
    compile_translations()
