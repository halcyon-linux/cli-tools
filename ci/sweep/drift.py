#!/usr/bin/env python3
"""ci/sweep/drift.py — print the registry packages whose spec Version is
newer than the latest SUCCEEDED Copr build (or that never built).

update.yml uses this to decide what to dispatch to copr-build.yml: it covers
the bumps the sweep just pushed AND earlier bumps whose build failed (a failed
bump leaves the spec ahead of Copr, and nothing else would ever retry it).
Only specs strictly NEWER than the published version count, so a spec that is
behind or equal never triggers a rebuild loop.

Output: one line, space-separated package names (empty when nothing drifted).
"""

from __future__ import annotations

import json
import os
import sys
import tomllib
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spec import SpecError, SpecFile  # noqa: E402
from vercmp import rpmvercmp  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGES_FILE = REPO_ROOT / "ci" / "packages.toml"
API = "https://copr.fedorainfracloud.org/api_3/package/list/"
OWNER = "aahsnr-work"
PROJECT = "cli-tools"


def published_versions() -> dict[str, str | None]:
    """package name -> version of its latest succeeded build (None = never)."""
    out: dict[str, str | None] = {}
    offset, limit = 0, 100
    while True:
        qs = urllib.parse.urlencode({
            "ownername": OWNER,
            "projectname": PROJECT,
            "with_latest_succeeded_build": "true",
            "limit": limit,
            "offset": offset,
        })
        req = urllib.request.Request(
            f"{API}?{qs}", headers={"User-Agent": "halcyon-packages-drift"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            items = json.load(resp)["items"]
        for item in items:
            ok = (item.get("builds") or {}).get("latest_succeeded")
            source = (ok or {}).get("source_package") or {}
            version = source.get("version")
            # "<version>-<release>": rpm versions never contain a dash
            out[item["name"]] = version.split("-")[0] if version else None
        if len(items) < limit:
            return out
        offset += limit


def main() -> None:
    with open(PACKAGES_FILE, "rb") as fh:
        names = sorted(tomllib.load(fh))
    published = published_versions()
    behind: list[str] = []
    for name in names:
        spec_path = REPO_ROOT / "pkgs" / name / f"{name}.spec"
        try:
            local = SpecFile(spec_path).get_version()
        except (SpecError, OSError) as exc:
            print(f"drift.py: {name}: {exc}", file=sys.stderr)
            continue
        remote = published.get(name)
        if remote is None or rpmvercmp(local, remote) > 0:
            behind.append(name)
    print(" ".join(behind))


if __name__ == "__main__":
    main()
