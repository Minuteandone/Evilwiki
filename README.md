# Evilwiki Archive Viewer

A static GitHub Pages explorer for the published Evilwiki archive.

The viewer includes:

- archive overview and counts
- page browsing and filtering
- full revision bodies and history
- client-side diffs
- save/delete/revert/probe event browsing
- label/actor browsing
- metadata search
- on-demand full revision-text search
- dark mode and responsive layout

## GitHub Pages deployment

The repository intentionally keeps the multi-megabyte archive out of Git history. On every Pages deployment, `.github/workflows/pages.yml` assembles the browser assets, downloads the five machine-readable files from the public Collusion.wiki export, verifies the published SHA-256 checksums, rebuilds the static viewer data into 16 revision shards, runs integrity QA, and then publishes the resulting site.

Source export:

`https://collusion.wiki/explorer/download.html`

The workflow downloads:

- `pages.jsonl.gz`
- `revisions.jsonl.gz`
- `events.jsonl.gz`
- `labels.jsonl.gz`
- `manifest.json.gz`

The checksums in the workflow are for the **decompressed** files, matching the publisher's download page. The archive originally supplied for this viewer was independently checked against those same hashes before this repository was published.

## First-time Pages setup

If GitHub Pages has not yet been enabled for the repository, open **Settings → Pages** and set **Source** to **GitHub Actions**. After that, the included workflow handles deployments automatically on every push to `main`.

## Local build

Download the five source files above into `source-data/`, then run:

```bash
cat src/app.js.part.* > app.js
cat src/styles.css.part.* > styles.css
python3 tools/build_pages_data.py ../source-data --out ../data --shards 16
python3 tools/qa_static.py
python3 -m http.server 8000
```

Then open `http://localhost:8000/`.

No third-party Python or JavaScript packages are required for the viewer itself.
