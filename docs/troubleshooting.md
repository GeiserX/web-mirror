# Troubleshooting

## The build stops at the first step on an Apple Silicon Mac

```text
Step 1/11 : FROM selenium/standalone-edge:153.0
no matching manifest for linux/arm64/v8 in the manifest list entries: no match for platform in manifest: not found
```

The base image exists for amd64 only. Build and run for amd64, which Docker runs under emulation:

```bash
docker build --platform linux/amd64 -t web-mirror .
docker run --rm --platform linux/amd64 -v "$PWD/data:/data" web-mirror
```

Under emulation the build takes several minutes and the run is slower than on an amd64 machine.

## Chromium crashes at launch on an Apple Silicon Mac

```text
[pid=23][err] Received signal 11 SEGV_MAPERR 62636266653c12
[pid=23][err] Assertion failed: p_rcu_reader->depth != 0 (/qemu/include/qemu/rcu.h: rcu_read_unlock: 102)
playwright._impl._errors.TargetClosedError: BrowserType.launch: Target page, context or browser has been closed
```

Docker is emulating amd64 with QEMU, and Chromium does not run under it. Switch the emulation to Rosetta: in Colima, start the VM with `colima start --vm-type vz --vz-rosetta` (Rosetta must be installed: `softwareupdate --install-rosetta`); in Docker Desktop, turn on "Use Rosetta for x86_64/amd64 emulation on Apple Silicon" in Settings, General. The image does not need a rebuild.

## `./data` stays empty, or nginx fails with "not a directory"

```text
docker: Error response from daemon: ... error mounting "<your folder>/nginx/default.conf" to rootfs at "/etc/nginx/conf.d/default.conf": ... not a directory: Are you trying to mount a directory onto a file (or vice-versa)?
```

Docker runs in a virtual machine on a Mac, and the folder you ran the command from is not shared with it. The VM then mounts an empty folder of its own: the copy is written inside the VM, and nginx finds a folder where its config should be. Colima shares only your home folder unless told otherwise; run from a folder under your home, or add the folder with `colima start --mount <folder>:w`. Docker Desktop lists its shared folders in Settings, Resources, File sharing.

## `apt-get update` fails during the build with "invalid signature"

```text
W: GPG error: http://archive.ubuntu.com/ubuntu noble-backports InRelease: At least one invalid signature was encountered.
```

The usual cause is a full Docker disk. Check `docker system df` first: if the images and build cache fill the disk, free space with `docker image prune` or by removing images you no longer need, then build again.

## The run stops with a ConnectionError

```text
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='www.place.holder', port=443): Max retries exceeded with url: /es/sitemap.xml (Caused by NameResolutionError("HTTPSConnection(host='www.place.holder', port=443): Failed to resolve 'www.place.holder' ([Errno -2] Name or service not known)"))
```

`src/main2.py` still names the placeholder site, or line 27 names a host that does not resolve. The sitemap is fetched even when line 34 returns a fixed list, until a 200 response for it sits in `data/sitemap.sqlite`. Edit lines 27, 34, 71 and 72 ([Configuration](configuration.md#the-lines-to-edit)) and build again, or mount the edited file ([Usage](usage.md#use-the-published-image)).

## The copy opens without its styles or images

Expected: web-mirror saves the HTML of each page, not its stylesheets, scripts or images ([How it works](how-it-works.md#what-is-saved-and-what-is-not)). While your browser is online, images with a full URL still load from the live site.

## A saved video does not play

The saved copy of a page at `/video-src/` holds:

```html
<video controls="" src="//data//video-src//clip.mp4"></video>
```

The page's `<video src>` is rewritten to `//data/<path>/<file>`, which a browser reads as a URL on a host named `data`. The video file itself is saved in `data/<path>/`; open it from there, or from the folder listing nginx shows at `/<path>/`. A video page whose address ended in `/` is saved as `data/<path>/.html`, a hidden file the listing does not show; nginx serves it at `/<path>/.html`.

## The run stops with `KeyError: 'src'`

```text
    return self.attrs[key]
           ~~~~~~~~~~^^^^^
KeyError: 'src'
```

The page has a `<video>` whose file is named in a `<source>` element inside it, not in a `src` attribute. web-mirror reads only `<video src>`. Leave that page out of the list.

## Reporting a bug

Open an [issue](https://github.com/GeiserX/web-mirror/issues) with:

- the output of the run, from the first line to the error;
- lines 27, 34, 71 and 72 of your `src/main2.py`, with the site's address if you can share it;
- whether you built the image or mounted the file into `drumsergio/web-mirror:1.0.2`;
- `uname -m` and `docker version` of the machine that ran it.
