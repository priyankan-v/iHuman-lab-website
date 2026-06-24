"""
Pre-render script: scans images/work/ and auto-updates:
  - gallery/index.qmd   (between GALLERY_START / GALLERY_END)
  - index.qmd           (between SLIDESHOW_START / SLIDESHOW_END)

Run automatically via _quarto.yml pre-render, or manually:
    python scripts/update_gallery.py
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
WORK_DIR = ROOT / "images" / "work"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def find_images():
    return sorted(
        p for p in WORK_DIR.iterdir()
        if p.suffix.lower() in IMAGE_EXTS
    )


def replace_between(text, start_marker, end_marker, replacement):
    pattern = re.compile(
        rf"({re.escape(start_marker)})\n.*?(\n\s*{re.escape(end_marker)})",
        re.DOTALL,
    )
    return pattern.sub(rf"\1\n{replacement}\2", text)


def write_if_changed(path, new_text):
    if path.read_text() != new_text:
        path.write_text(new_text)
        return True
    return False


def update_gallery(images):
    path = ROOT / "gallery" / "index.qmd"
    lines = []
    for img in images:
        rel = f"../images/work/{img.name}"
        lines.append(
            f'  <a href="{rel}" class="gallery-item lightbox" data-gallery="lab-gallery">\n'
            f'    <img src="{rel}" alt="iHuman Lab" loading="lazy" />\n'
            f'  </a>'
        )
    replacement = "\n".join(lines)
    text = replace_between(path.read_text(), "<!-- GALLERY_START -->", "<!-- GALLERY_END -->", replacement)
    changed = write_if_changed(path, text)
    print(f"  Gallery updated — {len(images)} photos" if changed else f"  Gallery unchanged — {len(images)} photos")


def update_slideshow(images):
    path = ROOT / "index.qmd"
    total = len(images)
    interval = 4  # seconds per photo
    cycle = total * interval

    filenames = ", ".join(f'"{img.name}"' for img in images)
    replacement = f"[{filenames}]"

    text = replace_between(path.read_text(), "/* SLIDESHOW_START */", "/* SLIDESHOW_END */", replacement)
    changed = write_if_changed(path, text)

    # Update animation duration in custom.scss
    scss_path = ROOT / "custom.scss"
    scss = scss_path.read_text()
    new_scss = re.sub(
        r"(animation: slideshow-fade )\d+s( infinite)",
        rf"\g<1>{cycle}s\2",
        scss,
    )
    scss_changed = write_if_changed(scss_path, new_scss)

    if changed or scss_changed:
        print(f"  Slideshow updated — {total} photos, {cycle}s cycle")
    else:
        print(f"  Slideshow unchanged — {total} photos, {cycle}s cycle")


def main():
    images = find_images()
    if not images:
        print("No images found in images/work/ — skipping gallery update.")
        return
    print(f"Found {len(images)} images in images/work/")
    update_gallery(images)
    update_slideshow(images)
    print("Done.")


if __name__ == "__main__":
    main()
