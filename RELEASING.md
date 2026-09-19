<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Releasing structured-address-fix-mcp

This document defines **what merits a release** and **how to cut one**,
so versions are deliberate rather than ad-hoc.

## Versioning scheme

structured-address-fix-mcp versions independently of the core library.
It declares a floor on
[`structured-address-fix`](https://github.com/sebastienrousseau/structured-address-fix)
(`>=0.0.3,<1` today) and raises that floor in the release that first
needs a newer core API. Versions are monotonic `0.0.x` until the tool
surface is frozen; the maintainer decides each bump.

## What merits a release

Cut a new version when there is user-visible change to ship - bug fixes,
security or dependency patches, new tools / resources / prompts, a new
transport, or documentation that ships in the package.

Do **not** cut a release that contains only a version-number bump with
no functional, security, or documentation change.

## Pre-flight checklist

A release is ready only when **all** of the following hold on `main`:

1. `make check` is green (ruff + black + mypy + 100% line and branch
   coverage + examples), and `interrogate` and `bandit` pass as CI runs
   them.
2. Every Dependabot / CodeQL / bandit alert is resolved or has a
   documented, expiring suppression.
3. `CHANGELOG.md` has a dated section for the new version describing the
   change set (this is the single source of truth for the release).
4. The version is identical in `pyproject.toml`,
   `structured_address_fix_mcp/__init__.py`, `glama.json` and
   `server.json` (including every `packages[].version`), and
   `CHANGELOG.md` carries the heading. `scripts/verify_versions.py`
   enforces this and the `versions.yml` workflow runs it on every PR.
   The Glama directory and the MCP registry read those two manifests; a
   release that forgets them shows an old version to every agent that
   browses for the server.
5. `poetry.lock` matches `pyproject.toml` (`poetry check --lock`; the
   CI `lockfile` job fails otherwise) and, if a dependency range moved,
   `requirements/*.txt` were regenerated with `make pip-compile`.

## Cutting the release

1. Bump the version in the four files above and add the `CHANGELOG.md`
   section in a single PR.
2. Merge the PR to `main` once CI is green.
3. Push a signed tag:

   ```bash
   git tag -s vX.Y.Z -m "structured-address-fix-mcp vX.Y.Z" <merge-commit>
   git push origin vX.Y.Z
   ```

4. The tag triggers two workflows:
   - `release.yml` builds with `poetry build`, runs `twine check`,
     attaches SLSA Build L3 provenance, publishes to PyPI through OIDC
     trusted publishing with PEP 740 attestations, signs every
     distribution with keyless cosign, creates the GitHub release with
     generated notes, then attaches CycloneDX, SPDX and pip-licenses
     SBOMs.
   - `publish-mcp.yml` stamps the tag's version into `server.json`,
     waits for PyPI to surface the release, and publishes the server to
     the MCP registry.

## After releasing

- Confirm the version is live on
  [PyPI](https://pypi.org/project/structured-address-fix-mcp/) and the
  GitHub release is published (not draft) with the `.sig`, `.pem` and
  SBOM assets.
- Verify a clean install: `pip install structured-address-fix-mcp==X.Y.Z`.
- Confirm the MCP registry and Glama listings show the new version.
- The `Dockerfile` builds a local image
  (`docker build -t structured-address-fix-mcp .`); no workflow publishes
  it to a registry.

## Optional CI integrations

- **PyPI trusted publisher** (`release.yml`): configured at
  <https://pypi.org/manage/account/publishing/>. The publisher claim
  set is `repo:sebastienrousseau/structured-address-fix-mcp:environment:pypi`
  with `workflow_ref` pointing at `.github/workflows/release.yml`.
- **MCP registry** (`publish-mcp.yml`): authenticates with the
  workflow's OIDC identity; ownership is proven by the `mcp-name:` marker
  in the README once PyPI lists the version.
