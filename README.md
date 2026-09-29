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

The copy lands in `./data`. To serve it, run `docker run --rm -p 8080:80 -v "$PWD/data:/usr/share/nginx/html:ro" -v "$PWD/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro" nginx:1.29-alpine` and open http://localhost:8080. The published image (`drumsergio/web-mirror:1.0.2`, amd64) carries the placeholder, so it only helps as a base for your own build.

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
