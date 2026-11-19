"""Add East-Asian (a:ea) and complex-script (a:cs) typefaces next to every a:latin run font.

pptxgenjs writes only <a:latin>. PowerPoint falls back to the theme's East-Asian font,
but LibreOffice (used for the PDF export) drops Hangul glyphs instead, so the exported
PDF loses all Korean text. Running this after writeFile keeps both renderers correct.

usage: python3 fix_ea_fonts.py deck.pptx "Apple SD Gothic Neo"
"""
import re
import shutil
import sys
import zipfile

TARGETS = ("ppt/slides/", "ppt/slideLayouts/", "ppt/slideMasters/", "ppt/notesSlides/")


def patch_xml(xml: str, font: str) -> str:
    def repl(m: re.Match) -> str:
        tag = m.group(0)
        return f'{tag}<a:ea typeface="{font}"/><a:cs typeface="{font}"/>'

    # Only add after a latin tag that is not already followed by an ea tag.
    return re.sub(r'<a:latin typeface="[^"]*"(?: [^>]*)?/>(?!<a:ea)', repl, xml)


def main() -> None:
    path, font = sys.argv[1], sys.argv[2]
    src = path + ".orig"
    shutil.move(path, src)
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zout:
        changed = 0
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith(TARGETS) and item.filename.endswith(".xml"):
                text = data.decode("utf-8")
                fixed = patch_xml(text, font)
                if fixed != text:
                    changed += 1
                data = fixed.encode("utf-8")
            zout.writestr(item, data)
    print(f"ea/cs font applied to {changed} parts in {path}")


if __name__ == "__main__":
    main()
