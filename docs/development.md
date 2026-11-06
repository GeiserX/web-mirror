# Development

## Tests

The tests stub Selenium, Playwright, undetected-chromedriver and `requests_cache`, so they run without a browser or a network:

```bash
pip install -r requirements-test.txt
pytest tests/ --cov=src
```

[`tests/test_web_mirror.py`](https://github.com/GeiserX/web-mirror/blob/main/tests/test_web_mirror.py) holds 68 tests covering all four scripts in `src/`: the sitemap reading, the video download, the output paths, the link rewriting and each script's entry point. [`codecov.yml`](https://github.com/GeiserX/web-mirror/blob/main/codecov.yml) sets a 90% coverage target for the project and for each pull request.

## Continuous integration

| Workflow | Runs on | What it does |
|---|---|---|
| [`tests.yml`](https://github.com/GeiserX/web-mirror/blob/main/.github/workflows/tests.yml) | every pull request, and pushes to `main` | the tests on Python 3.12, then the coverage upload to Codecov |
| [`docs.yml`](https://github.com/GeiserX/web-mirror/blob/main/.github/workflows/docs.yml) | every pull request, and pushes to `main` that touch `docs/`, `zensical.toml`, `nginx/default.conf`, the site check or the workflow | the strict build of this site and the site check; on `main`, the deploy to GitHub Pages |
| [`docker-publish.yml`](https://github.com/GeiserX/web-mirror/blob/main/.github/workflows/docker-publish.yml) | a `v*.*.*` tag, and pushes to `main` that touch the `Dockerfile`, `requirements.txt`, `src/` or the workflow | builds the linux/amd64 image and pushes it to [Docker Hub](https://hub.docker.com/r/drumsergio/web-mirror) |
| [`dockerhub-description.yml`](https://github.com/GeiserX/web-mirror/blob/main/.github/workflows/dockerhub-description.yml) | pushes to `main` that touch `README.md` | copies the README to the Docker Hub page |

## Releases

A release is a tag. Push `vX.Y.Z` on `main` and `docker-publish.yml` publishes the image as `X.Y.Z` and `vX.Y.Z`; a push to `main` that changes the image also moves `latest`. There is no version file and no changelog; the GitHub release notes say what changed.

## The docs

The site is built with [Zensical](https://zensical.org/) from `docs/` and `zensical.toml`:

```bash
pip install -r docs/requirements-docs.txt
python -m zensical serve                    # live preview at http://localhost:8000/web-mirror/
python -m zensical build --clean --strict   # what CI runs, then:
python -I .github/scripts/site-check.py site
```

The strict build fails on a broken link, a missing anchor or a missing snippet include. `site-check.py` fails on what the build lets through: a page in no nav entry, a nav entry for a missing file, a missing image and a link rooted at `/`.

A page is a lowercase file in `docs/` listed in the `nav` of [`zensical.toml`](https://github.com/GeiserX/web-mirror/blob/main/zensical.toml) and linked from the home page.

## Dependencies

Dependabot opens pull requests for new versions of the Python packages (`requirements.txt` and `docs/requirements-docs.txt`, major versions ignored), the `Dockerfile` base image and the workflow actions.

## Security

Report a vulnerability as the [security policy](https://github.com/GeiserX/web-mirror/blob/main/SECURITY.md) says, never in a public issue.
