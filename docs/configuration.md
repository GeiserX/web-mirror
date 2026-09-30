# Configuration

web-mirror has no command-line flags, no environment variables and no config file. Every setting is a constant in [`src/main2.py`](https://github.com/GeiserX/web-mirror/blob/main/src/main2.py), the file the image runs (`CMD ["python3", "-u", "src/main2.py"]` in the [Dockerfile](https://github.com/GeiserX/web-mirror/blob/main/Dockerfile)). Change the file, then rebuild the image or mount the file into the published one (see [Usage](usage.md#use-the-published-image)).

## The lines to edit

The site's address appears in three places, and the page list in a fourth. All four must name the same site, or the run fetches one site and rewrites links for another.

| Line | What it holds | Shipped value | Change it to |
|---|---|---|---|
| 27 | `web`, the site whose sitemap is read | `"https://www.place.holder/"` | your site, with the trailing slash |
| 34 | the list of pages to save | `["https://www.place.holder/VIDEO"]` | the full URLs of your pages, or `links` to use the sitemap (see below) |
| 71 | the prefix a link must start with to be rewritten | `"https://www.place.holder/"` | the same address as line 27 |
| 72 | the part removed from those links | `"https://www.place.holder"` | the same address, without the trailing slash |

For example, to save the front page and one article of `https://example.com`:

```python
    web = "https://example.com/"                                        # line 27
    return ["https://example.com/", "https://example.com/article/"]     # line 34
            if tag[attribute_name].startswith("https://example.com/"):  # line 71
                tag[attribute_name] = tag[attribute_name].replace("https://example.com", "")  # line 72
```

## Using the sitemap

Line 34 returns a fixed list, and line 35 holds the alternative, commented out. Replace line 34 with `return links` and the run saves every `<loc>` entry of the sitemap instead.

The sitemap is fetched from `web + language + "/sitemap.xml"` (line 29), which with the shipped `language = "es"` (line 13) is `https://<your site>/es/sitemap.xml`. For a sitemap at another path, edit line 29. The fetch runs even when line 34 returns a fixed list, so `web` must be a host that answers the first time; see [Troubleshooting](troubleshooting.md#the-run-stops-with-a-connectionerror). After that, a 200 response cached in `data/sitemap.sqlite` is reused without a network call, and deleting that file fetches the sitemap again ([Usage](usage.md#run-it-again)).

A sitemap index (a sitemap that lists other sitemaps) is not followed: its `<loc>` entries are the child sitemaps' URLs, and the run would save those XML files as pages.

## Other constants

| Line | Constant | Shipped value | What it does |
|---|---|---|---|
| 13 | `language` | `"es"` | the path segment before `sitemap.xml` (line 29) |
| 14 | `fulldir` | `"/data/"` | where the copy is written inside the container; mount a folder of yours there |
| 25 | `requests_cache.install_cache(...)` | `/data/sitemap.sqlite` | caches the sitemap and video downloads with no expiry; see [Usage](usage.md#run-it-again) |
| 51 | `time.sleep(3)` | 3 seconds | the wait after a page loads, before it is saved, so scripts can finish building it |
| 83 | the `User-Agent` header | Chrome 58 on Windows 10 | sent by Chromium with every page request; the sitemap and video downloads use the `requests` library's default |
| 86 | `p.chromium.launch()` | headless Chromium | the browser Playwright starts |

## Serving

[`nginx/default.conf`](https://github.com/GeiserX/web-mirror/blob/main/nginx/default.conf) is the nginx config for the copy. It has no settings of its own to change; [Usage](usage.md#serve-the-copy-offline) shows how to mount it.
