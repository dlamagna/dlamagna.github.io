# dlamagna.github.io

Personal site of Davide Lamagna, served by GitHub Pages at <https://dlamagna.github.io>.

Plain HTML, CSS and one small JavaScript file. There is no build step: GitHub Pages serves the repository root of `main` as-is (`.nojekyll` turns Jekyll off).

## What's where

| Path | What it is |
|---|---|
| `index.html` | The page: hero, About, services and roles are written here directly |
| `data/projects.json` | **Every project, side venture, job, degree and paper**, plus the headline |
| `assets/js/main.js` | Renders the sections from `data/projects.json` |
| `assets/css/site.css` | Styles; light by default, dark when picked with the header toggle |
| `assets/img/` | Photo crops, preview image, favicon |
| `scripts/sync.py` | Copies `data/projects.json` into the static parts of `index.html` (see below) |
| `scripts/og-image.html` | Template for the social preview image |
| `demos/<project>/` | Concept pages for projects in private repositories (agentic-devops, Listen2MyDay), linked from their cards. Hand-written HTML on the same stylesheet; made-up data only |
| `DavideLamagnaCV.pdf` | The CV linked from the site |
| `robots.txt`, `sitemap.xml` | For search engines |

### Why `scripts/sync.py` exists

The page renders projects with JavaScript, but search engines, link previews and visitors without JavaScript read the raw HTML. `sync.py` writes the same entries into `<noscript>` blocks in `index.html` and copies the headline into the meta tags and JSON-LD. It only needs Python 3 (no packages). Run it after every edit to `data/projects.json`:

```sh
python3 scripts/sync.py          # updates index.html
python3 scripts/sync.py --check  # just reports whether index.html is up to date
```

## Preview locally

```sh
python3 -m http.server 8000      # then open http://localhost:8000
```

Open it through the server, not by double-clicking `index.html`: browsers block `fetch()` of the data file from `file://`, and the page then falls back to the plain lists.

## Add a project

1. Open `data/projects.json`.
2. For a **featured case card**, add an object to `featured`:

   ```json
   {
     "id": "my-project",
     "title": "My project: what it is in a few words",
     "meta": "Client or context · 2026",
     "problem": "One or two sentences on the problem.",
     "did": "What you built or ran.",
     "stack": ["Python", "AWS"],
     "outcome": "What changed, with numbers where you have them.",
     "links": [{ "label": "Code", "url": "https://github.com/dlamagna/my-project" }]
   }
   ```

   Optional fields: `"wide": true` makes the card full width; `"items": [...]` adds a bullet list under "Contribution"; `"demo": { "label": "Check it out", "url": "..." }` adds a primary button before the links (also works on `more` entries, as a link).

3. For a **one-line entry** in "More projects and side ventures", add to `more`:

   ```json
   { "group": "Smaller projects", "title": "my-project", "years": "2026",
     "line": "One sentence.", "url": "https://github.com/dlamagna/my-project" }
   ```

   `group` decides the heading (`Side ventures` or `Smaller projects`; a new name makes a new group). `url` is optional.

4. Jobs go in `experience`, degrees in `education`, papers and posts in `writing`, all with the same pattern as the entries already there. For one employer with several roles (like S&P Global), leave out `role` and give the entry a `roles` list of `{ "role", "dates", "place", "line" }`: the employer becomes the heading and the roles are listed under it.
5. Run `python3 scripts/sync.py`, preview, commit.

Cards appear in the order they are listed.

### Placeholders for missing facts

Any entry can carry a `todo` list:

```json
"todo": [{ "show": "Results to add", "need": "p95 latency before and after" }]
```

`show` is printed on the page as a yellow placeholder; `need` becomes an HTML comment `<!-- TODO(Davide): ... -->`. Leave out `show` for a comment only. Delete the `todo` once the fact is in. To list what is still open:

```sh
grep -o 'TODO(Davide)[^>]*' index.html data/projects.json
```

## Light and dark mode

The site opens in light mode. A button in the header switches to dark, and the browser remembers the choice. To keep the site light only, change `data-theme-toggle="on"` to `"off"` on the `<html>` tag in `index.html`: the button disappears and saved choices are ignored.

The project sites under the same domain (`/agentraffic/`, `/kubernetes-edge-healer/`, `/margin/`) open in whichever theme this site is showing: `main.js` writes it into their own saved-theme keys (`agentraffic-theme`, `edge-healer-theme`, `margin-theme`). This only works on the live site, not on `localhost`. If a project site renames its key, update `PROJECT_THEME_KEYS` in `main.js`.

## Change the headline

Edit `site.headline` at the top of `data/projects.json`, then run `python3 scripts/sync.py`. That updates the meta description, the Open Graph and Twitter tags, the JSON-LD and the preview image template. Then re-take the preview image (next section).

## Change the photo

1. Start from the new photo (the original is kept locally as `assets/profile.jpg`, which is not committed).
2. Make the square crops the page uses: `assets/img/profile-320.webp` (320×320), `assets/img/profile-192.webp` (192×192) and `assets/img/profile-og.jpg` (480×480, for the preview image). Any image editor or <https://squoosh.app> works. Keep the face centred, as the page shows it in a circle.
3. Re-take the preview image.

If the photo files are missing, the page shows a "DL" initials avatar instead.

## Social preview image

`assets/img/og-image.png` (1200×630) is a screenshot of `scripts/og-image.html`. To re-take it after changing the headline or photo:

```sh
npx playwright@1.59.1 screenshot --viewport-size=1200,630 \
  "file://$PWD/scripts/og-image.html" assets/img/og-image.png
```

(Or open `scripts/og-image.html` in a browser with the window at 1200×630 and take a screenshot.) LinkedIn caches previews: use the [Post Inspector](https://www.linkedin.com/post-inspector/) to refresh it.

## Update the CV

The CV is edited in Google Docs (`CV.vNN…`). When it is final, ask Claude Code to "update the CV": a local Claude Code skill (`update-cv`, kept outside the repository) exports the latest Doc as a PDF and installs it.

To do it by hand, download the PDF from Docs and run `python3 scripts/install_cv.py path/to/cv.pdf`. The script checks the PDF (valid, 2 pages, has the name), replaces `DavideLamagnaCV.pdf` (same name, so existing links keep working), keeps the old file as `DavideLamagnaCV.pdf.bak` and updates its `<lastmod>` date in `sitemap.xml`. Add `--dry-run` to validate only.

## Checks before merging

- `python3 scripts/sync.py --check` says "Up to date."
- The page looks right at phone width (360 px), in light mode and with the dark toggle on.
- Lighthouse (Chrome DevTools → Lighthouse) still scores 95+ in all four categories.
