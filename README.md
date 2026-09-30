<p align="center">
  <img src="https://raw.githubusercontent.com/GeiserX/web-mirror/main/docs/images/banner.svg" alt="web-mirror banner" width="900">
</p>

<h1 align="center">web-mirror</h1>

<p align="center">A Playwright script that saves the pages of one website as local HTML files, videos included, plus an nginx config to serve the copy offline.</p>

<p align="center">
  <a href="https://github.com/GeiserX/web-mirror/actions/workflows/tests.yml"><img src="https://img.shields.io/github/actions/workflow/status/GeiserX/web-mirror/tests.yml?style=flat-square&label=tests" alt="Tests"></a>
  <a href="https://github.com/GeiserX/web-mirror/blob/main/LICENSE"><img src="https://img.shields.io/github/license/GeiserX/web-mirror?style=flat-square" alt="License"></a>
  <a href="https://codecov.io/gh/GeiserX/web-mirror"><img src="https://img.shields.io/codecov/c/github/GeiserX/web-mirror?style=flat-square" alt="Coverage"></a>
</p>

The site and the page list are set in the code, not by a setting: `src/main2.py` ships with the placeholder domain `www.place.holder` and a one-page list (line 34), so you edit it before you build. It runs in Docker and writes the copy to `/data`.

<p align="center">
  <img src="https://raw.githubusercontent.com/GeiserX/web-mirror/main/docs/images/screenshots/run.png" alt="A run of web-mirror: the amd64 build on an Apple Silicon Mac, the one-line log of the page it saves from example.com, the two files it wrote, and nginx serving the copy" width="820">
</p>

## Features

- Renders each page in headless Chromium through Playwright, so pages built by JavaScript are captured.
- Saves each page as `index.html` in a folder named after its URL path (a page with a video as `<path>.html`).
- Downloads the `<video>` source of a page next to its HTML.
- Rewrites links to the mirrored site into local paths.
- Can read the page list from the site's `sitemap.xml` (swap line 34 for `return links`).
- Ships an nginx config (`nginx/default.conf`) that serves the copy with directory listings.

## Quick start

```bash
git clone https://github.com/GeiserX/web-mirror.git && cd web-mirror
# edit src/main2.py: replace www.place.holder with your site (lines 27, 34, 71, 72) and set the pages on line 34
docker build -t web-mirror . && docker run --rm -v "$PWD/data:/data" web-mirror
```

On an Apple Silicon Mac, add `--platform linux/amd64` to `docker build` and `docker run`, and let Docker emulate amd64 with Rosetta (Colima `--vz-rosetta`, or Docker Desktop's Rosetta setting): the base image exists for amd64 only, and Chromium crashes under QEMU.

The copy lands in `./data`. To serve it, run `docker run --rm -p 8080:80 -v "$PWD/data:/usr/share/nginx/html:ro" -v "$PWD/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro" nginx:1.29-alpine` and open http://localhost:8080. The published image (`drumsergio/web-mirror:1.0.2`, amd64) carries the placeholder, so it only helps as a base for your own build.

## Documentation

The full documentation is at [geiserx.github.io/web-mirror](https://geiserx.github.io/web-mirror/).

- [Getting started](https://geiserx.github.io/web-mirror/getting-started/): what you need, the four lines to edit, build, run, and what a finished run looks like
- [Configuration](https://geiserx.github.io/web-mirror/configuration/): every constant in `src/main2.py`, and how to save the whole sitemap
- [Usage](https://geiserx.github.io/web-mirror/usage/): where each page lands, serving the copy with nginx, running again, the published image without a build
- [How it works](https://geiserx.github.io/web-mirror/how-it-works/): what happens to each page, which links are rewritten, what is not saved
- [Troubleshooting](https://geiserx.github.io/web-mirror/troubleshooting/): the arm64 build error, the QEMU crash, a full Docker disk, the placeholder's ConnectionError, video pages
- [Development](https://geiserx.github.io/web-mirror/development/): tests, CI, releases and the docs build
- [Related projects](https://geiserx.github.io/web-mirror/related/): the other web-archiving tools

## Related projects

| Project | Description |
|---------|-------------|
| [Wayback-Archive](https://github.com/GeiserX/Wayback-Archive) | Download complete websites from the Wayback Machine with full asset preservation |
| [Wayback-Diff](https://github.com/GeiserX/Wayback-Diff) | Intelligent web page comparison tool with Wayback Machine support |
| [Way-CMS](https://github.com/GeiserX/Way-CMS) | Simple web CMS for editing HTML/CSS files downloaded from Wayback Archive |
| [media-download](https://github.com/GeiserX/media-download) | Download all media files from any web page into a folder schema |
| [n8n-nodes-way-cms](https://github.com/GeiserX/n8n-nodes-way-cms) (archived) | n8n community node for Way-CMS archived web content management |

## License

[GPL-3.0-or-later](https://github.com/GeiserX/web-mirror/blob/main/LICENSE)
