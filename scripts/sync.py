#!/usr/bin/env python3
"""Copy data/projects.json into the static parts of index.html.

Run after editing data/projects.json:

    python3 scripts/sync.py          # rewrite index.html and scripts/og-image.html
    python3 scripts/sync.py --check  # exit 1 if they are out of date (nothing is written)

What it updates:
- the headline (site.headline) in the meta description, Open Graph, Twitter and JSON-LD
- the <noscript> fallback lists for every data-driven section, so crawlers and
  visitors without JavaScript see the same entries as the rendered page
- the headline in scripts/og-image.html (re-take the preview image afterwards, see README.md)

Standard library only; the site itself needs no build step.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "projects.json"
INDEX = ROOT / "index.html"
OG = ROOT / "scripts" / "og-image.html"


def esc(s):
    return html.escape(s or "", quote=True)


def todo_html(todos):
    out = []
    for t in todos or []:
        out.append("<!-- TODO(Davide): %s -->" % t["need"].replace("--", "-"))
        if t.get("show"):
            out.append('<span class="todo">%s</span>' % esc(t["show"]))
    return "".join(out)


def links_html(links):
    if not links:
        return ""
    return " " + " · ".join('<a href="%s">%s</a>' % (esc(l["url"]), esc(l["label"])) for l in links)


def fallback_featured(items):
    rows = []
    for p in items:
        extra = ""
        if p.get("items"):
            extra = "<ul>%s</ul>" % "".join("<li>%s</li>" % esc(i) for i in p["items"])
        rows.append(
            "<li><h3>%s</h3><p>%s</p><p><strong>Problem:</strong> %s</p>"
            "<p><strong>Contribution:</strong> %s</p>%s<p><strong>Outcome:</strong> %s</p>"
            "<p><strong>Stack:</strong> %s</p>%s<p>%s</p></li>"
            % (esc(p["title"]), esc(p["meta"]), esc(p["problem"]), esc(p["did"]), extra,
               esc(p["outcome"]), esc(", ".join(p.get("stack", []))), todo_html(p.get("todo")),
               links_html(([p["demo"]] if p.get("demo") else []) + (p.get("links") or [])).strip())
        )
    return '<div class="fallback"><ul>%s</ul></div>' % "".join(rows)


def fallback_more(items):
    groups = {}
    for m in items:
        groups.setdefault(m["group"], []).append(m)
    out = []
    for g, ms in groups.items():
        heading = "<h3>%s</h3>" % esc(g) if len(groups) > 1 else ""
        rows = []
        for m in ms:
            title = '<a href="%s">%s</a>' % (esc(m["url"]), esc(m["title"])) if m.get("url") else esc(m["title"])
            years = " (%s)" % esc(m["years"]) if m.get("years") else ""
            demo = ' <a href="%s">%s</a>' % (esc(m["demo"]["url"]), esc(m["demo"]["label"])) if m.get("demo") else ""
            rows.append("<li><strong>%s</strong>%s: %s%s %s</li>" % (title, years, esc(m["line"]), demo, todo_html(m.get("todo"))))
        out.append("%s<ul>%s</ul>" % (heading, "".join(rows)))
    return '<div class="fallback">%s</div>' % "".join(out)


def when(e):
    return " · ".join(esc(x) for x in (e.get("dates"), e.get("place")) if x)


def fallback_experience(items):
    # An entry with "roles" is one employer with several roles (see main.js).
    rows = []
    for e in items:
        head = "<strong>%s</strong>, %s" % (esc(e["role"]), esc(e["org"])) if e.get("role") else "<strong>%s</strong>" % esc(e["org"])
        line = (" " + esc(e["line"])) if e.get("line") else ""
        sub = ""
        if e.get("roles"):
            sub = "<ul>%s</ul>" % "".join(
                "<li>%s. %s. %s</li>" % (esc(r["role"]), when(r), esc(r.get("line"))) for r in e["roles"])
        rows.append("<li>%s. %s.%s%s %s</li>" % (head, when(e), line, sub, todo_html(e.get("todo"))))
    return '<div class="fallback"><ul>%s</ul></div>' % "".join(rows)


def fallback_education(items):
    rows = ["<li><strong>%s</strong>, %s. %s. %s</li>" % (esc(e["degree"]), esc(e["org"]), esc(e["dates"]), esc(e.get("line")))
            for e in items]
    return '<div class="fallback"><ul>%s</ul></div>' % "".join(rows)


def fallback_writing(items):
    rows = []
    for w in items:
        meta = " · ".join(esc(x) for x in (w.get("role"), w.get("venue"), w.get("date")) if x)
        rows.append("<li><strong>%s</strong>. %s. %s%s</li>" % (esc(w["title"]), meta, todo_html(w.get("todo")), links_html(w.get("links"))))
    return '<div class="fallback"><ul>%s</ul></div>' % "".join(rows)


FALLBACKS = {
    "featured": fallback_featured,
    "more": fallback_more,
    "experience": fallback_experience,
    "education": fallback_education,
    "writing": fallback_writing,
}


def replace_marker(text, name, value):
    pattern = re.compile(r"(<!-- sync:%s -->).*?(<!-- /sync:%s -->)" % (re.escape(name), re.escape(name)), re.S)
    if not pattern.search(text):
        sys.exit("marker sync:%s not found" % name)
    return pattern.sub(lambda m: m.group(1) + value + m.group(2), text)


def replace_attr(text, selector, value):
    # selector is e.g. 'name="description"' or 'property="og:description"'
    pattern = re.compile(r'(<meta %s content=")[^"]*(")' % re.escape(selector))
    if not pattern.search(text):
        sys.exit("meta tag %s not found" % selector)
    return pattern.sub(lambda m: m.group(1) + esc(value) + m.group(2), text)


def main():
    check = "--check" in sys.argv[1:]
    data = json.loads(DATA.read_text(encoding="utf-8"))
    site = data["site"]
    headline = site["headline"]

    index = INDEX.read_text(encoding="utf-8")
    # The hero no longer shows the headline; fill the marker only if it is there.
    new = replace_marker(index, "headline", esc(headline)) if "<!-- sync:headline -->" in index else index
    for sel in ('name="description"', 'property="og:description"', 'name="twitter:description"'):
        new = replace_attr(new, sel, headline)
    new = re.sub(r'("@type": "Person",(?:.|\n)*?"description": )"[^"]*"',
                 lambda m: m.group(1) + json.dumps(headline, ensure_ascii=False), new, count=1)
    for key, fn in FALLBACKS.items():
        new = replace_marker(new, "fallback:" + key, fn(data.get(key, [])))

    og = OG.read_text(encoding="utf-8")
    new_og = replace_marker(og, "headline", esc(headline))

    stale = [p.name for p, old, cur in ((INDEX, index, new), (OG, og, new_og)) if old != cur]
    if check:
        if stale:
            print("Out of date: %s. Run python3 scripts/sync.py" % ", ".join(stale))
            sys.exit(1)
        print("Up to date.")
        return
    INDEX.write_text(new, encoding="utf-8")
    OG.write_text(new_og, encoding="utf-8")
    print("Updated: %s" % (", ".join(stale) or "nothing changed"))
    if OG.name in stale:
        print("The headline changed: re-take assets/img/og-image.png (see README.md).")


if __name__ == "__main__":
    main()
