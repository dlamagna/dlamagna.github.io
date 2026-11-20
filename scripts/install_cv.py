#!/usr/bin/env python3
"""Install a CV PDF as DavideLamagnaCV.pdf and bump its <lastmod> in sitemap.xml.

    python3 scripts/install_cv.py PATH            # PATH is a .pdf, or a text file holding the PDF as base64
    python3 scripts/install_cv.py PATH --dry-run  # validate only, write nothing

Checks before anything is written: the data is a real PDF, pdfinfo can read it,
the page count is printed (the CV is meant to stay on 2 pages), and the text
contains the name. The old PDF is kept as DavideLamagnaCV.pdf.bak (git-ignored)
until the next run. Standard library plus poppler's pdfinfo/pdftotext.
"""
import base64
import datetime
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "DavideLamagnaCV.pdf"
SITEMAP = ROOT / "sitemap.xml"


def load_pdf(path):
    raw = Path(path).read_bytes()
    if raw.startswith(b"%PDF"):
        return raw
    try:  # the Drive connector returns base64 text
        decoded = base64.b64decode(b"".join(raw.split()), validate=True)
    except Exception:
        sys.exit("%s is neither a PDF nor base64 of one" % path)
    if not decoded.startswith(b"%PDF"):
        sys.exit("%s decodes to something that is not a PDF" % path)
    return decoded


def run(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv[1:]
    if len(args) != 1:
        sys.exit(__doc__)
    pdf = load_pdf(args[0])

    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp) / "cv.pdf"
        probe.write_bytes(pdf)
        info = run("pdfinfo", str(probe))
        text = run("pdftotext", "-layout", str(probe), "-")
    pages = int(re.search(r"^Pages:\s+(\d+)", info, re.M).group(1))
    print("PDF OK: %d bytes, %d page(s)" % (len(pdf), pages))
    if "Lamagna" not in text:
        sys.exit("The text does not contain the name; is this the right file?")
    if pages > 2:
        print("WARNING: %d pages; the CV is meant to be 2" % pages)
    if dry:
        print("Dry run: nothing written.")
        return

    if TARGET.exists():
        shutil.copy2(TARGET, TARGET.with_suffix(".pdf.bak"))
    TARGET.write_bytes(pdf)

    today = datetime.date.today().isoformat()
    sm = SITEMAP.read_text(encoding="utf-8")
    pattern = re.compile(r"(<loc>[^<]*DavideLamagnaCV\.pdf</loc>\s*<lastmod>)[^<]*(</lastmod>)")
    if not pattern.search(sm):
        sys.exit("CV entry not found in sitemap.xml")
    SITEMAP.write_text(pattern.sub(lambda m: m.group(1) + today + m.group(2), sm), encoding="utf-8")
    print("Wrote %s and set sitemap lastmod to %s" % (TARGET.name, today))


if __name__ == "__main__":
    main()
