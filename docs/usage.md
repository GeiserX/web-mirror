# Usage

Every run does the same thing: it saves each page in the list and exits. What you change between runs is the list, in `src/main2.py` ([Configuration](configuration.md)).

## Where each page lands

The copy is written to the folder you mount at `/data`, one folder per URL path.

| Page | Saved as |
|---|---|
| `https://example.com/` | `data/index.html` |
| `https://example.com/articles/topic/` or `https://example.com/articles/topic` | `data/articles/topic/index.html` |
| `https://example.com/videos/clip`, a page with a `<video>` | `data/videos/clip.html`, and the video in `data/videos/clip/` |
| `https://example.com/videos/clip/`, a page with a `<video>`, address ending in `/` | `data/videos/clip/.html` (a hidden file), and the video next to it |
| the sitemap and video download cache | `data/sitemap.sqlite` |

A video page also prints the path of the video it saved, under its log line. The container runs as root, so on a Linux host the files belong to root.

## Serve the copy offline

nginx with the shipped config serves the folder on port 8080:

```bash
docker run --rm -p 8080:80 \
  -v "$PWD/data:/usr/share/nginx/html:ro" \
  -v "$PWD/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro" \
  nginx:1.29-alpine
```

Open <http://localhost:8080>. The config, [`nginx/default.conf`](https://github.com/GeiserX/web-mirror/blob/main/nginx/default.conf):

```nginx
--8<-- "nginx/default.conf"
```

`autoindex on` means a folder with no `index.html` shows a list of its files. A video page is a file, not a folder: open `/videos/clip.html` (or `/videos/clip/.html` for an address that ended in `/`); `/videos/clip/` lists the video file and hides the `.html` one.

## Run it again

A second run renders every page again and overwrites its file. Pages that left the list stay on disk until you delete them.

The sitemap and the video downloads go through a `requests` cache in `data/sitemap.sqlite` that never expires, so a second run in sitemap mode reads the sitemap it saved the first time. Delete `data/sitemap.sqlite` to fetch it again.

## Use the published image

`drumsergio/web-mirror:1.0.2` on Docker Hub is the same image with the placeholder site. Instead of building, mount your edited `src/main2.py` over the one inside it:

```bash
docker run --rm \
  -v "$PWD/src/main2.py:/app/src/main2.py:ro" \
  -v "$PWD/data:/data" \
  drumsergio/web-mirror:1.0.2
```

On an arm64 host add `--platform linux/amd64`; the image exists for amd64 only.

## Docker Compose

`docker-compose.yaml` in the repo runs the published image with a Windows drive (`G:/`) as `/data`, and carries the nginx service commented out. Change the left side of each volume to your folder and add the `main2.py` mount above, or the run saves the placeholder site.
