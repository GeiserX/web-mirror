---
hide:
  - navigation
---

# web-mirror { .wm-visually-hidden }

<p align="center">
  <img src="images/banner.svg" alt="web-mirror" width="100%">
</p>

<p align="center">
  <a href="https://hub.docker.com/r/drumsergio/web-mirror"><img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/drumsergio/web-mirror?style=flat-square&logo=docker"></a>
  <a href="https://github.com/GeiserX/web-mirror/stargazers"><img alt="GitHub Stars" src="https://img.shields.io/github/stars/GeiserX/web-mirror?style=flat-square&logo=github"></a>
  <a href="https://github.com/GeiserX/web-mirror/releases"><img alt="Release" src="https://img.shields.io/github/v/release/GeiserX/web-mirror?style=flat-square"></a>
  <a href="https://github.com/GeiserX/web-mirror/blob/main/LICENSE"><img alt="License: GPL-3.0-or-later" src="https://img.shields.io/github/license/GeiserX/web-mirror?style=flat-square"></a>
</p>

---

**web-mirror** saves the pages of one website as HTML files on your disk, and ships an nginx config to serve the copy offline. Each page is opened in headless Chromium through Playwright before it is saved, so a page that JavaScript builds is kept as a visitor sees it, where `wget --mirror` saves the page as the server sends it, before any script runs. A `<video>` on the page is downloaded next to it, and links to the site become local paths. It saves the HTML only: no stylesheets, scripts or images. The site and the page list are set in `src/main2.py`, not by a flag. Start with [Getting started](getting-started.md), then [Configuration](configuration.md) for the four lines to edit.

<div class="grid cards" markdown>

-   :material-docker: **[Getting started](getting-started.md)**

    ---

    Edit four lines, build the image, run it, and see the files it writes. On an Apple Silicon Mac, build for amd64 and run it under Rosetta.

-   :material-pencil-outline: **[Point it at your site](configuration.md)**

    ---

    The lines in `src/main2.py` that name the site and the pages, the sitemap switch, and the other constants.

-   :material-web: **[Serve the copy](usage.md#serve-the-copy-offline)**

    ---

    Where each page lands on disk, nginx with the shipped config, and running it again.

-   :material-cogs: **[How it works](how-it-works.md)**

    ---

    What happens to each page, which links are rewritten, and what is not saved.

</div>

## A run

![A terminal on an Apple Silicon Mac: docker build for linux/amd64 ends with Successfully tagged web-mirror:latest, docker run logs the one page it saves from example.com, find lists data/index.html and data/sitemap.sqlite, and curl through the nginx container returns the saved page's title, Example Domain](images/screenshots/run.png)

The run above is the [Getting started](getting-started.md) path against `https://example.com/`: one page in the list, one line of log per page, the copy in `./data`, then nginx serving it on port 8080.

## What it saves

- Each page in the list, as the browser holds it after the page loads and 3 more seconds pass, in a folder named after its URL path.
- The file of a `<video src>` on a page, next to that page's HTML.
- The site's own links, rewritten to paths from the root, so the copy links to itself.
- Optionally every page of the site's `sitemap.xml` instead of a fixed list ([Configuration](configuration.md#using-the-sitemap)).

## How it runs

- One Docker image, `drumsergio/web-mirror`, for linux/amd64 only; an Apple Silicon Mac runs it under Rosetta, not QEMU ([Troubleshooting](troubleshooting.md#chromium-crashes-at-launch-on-an-apple-silicon-mac)). It runs `src/main2.py` once and exits; the copy is written to `/data`, which you mount from your disk.
- The image carries the placeholder site `www.place.holder`, so you either build your own after editing the file or mount your edited file into it ([Usage](usage.md#use-the-published-image)).
- The container talks to the site you set; while a page renders, Chromium also loads whatever that page loads (its scripts, images and trackers). nginx then serves the files from your disk and fetches nothing.

## What it does not do

- It does not download stylesheets, scripts, images or fonts. Offline, a saved page shows its text without its styles or pictures.
- It does not crawl. Only the pages in the list, or in the sitemap, are saved.
- A saved video page does not play its video from the copy: the page's `src` is written as `//data/...`, which a browser reads as a host named `data`. The video file itself is saved. See [Troubleshooting](troubleshooting.md#a-saved-video-does-not-play).
- It has no command-line flags or environment variables.

## Getting help

- A build or a run fails: [Troubleshooting](troubleshooting.md) lists what has gone wrong and what to include in an issue.
- Something else: open an [issue](https://github.com/GeiserX/web-mirror/issues). A security problem goes through the [security policy](https://github.com/GeiserX/web-mirror/blob/main/SECURITY.md), never a public issue.
- Running the tests and releasing: [Development](development.md). The other web-archiving tools: [Related projects](related.md).

## License

web-mirror is released under the [GPL-3.0-or-later](https://github.com/GeiserX/web-mirror/blob/main/LICENSE) license. It is built on [Playwright](https://playwright.dev/python/) and [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/).
