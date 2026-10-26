"""The custom version feeds: one custom_<name>(spec, pkg_dir) per registry
entry that sets `feed = "custom"` in ci/packages.toml (dashes in the name
become underscores). Each rewrites the spec through SpecFile; raising
feeds.FeedError (or SpecError) marks the package's sweep as failed without
stopping the others.
"""

from __future__ import annotations

import gzip
import re
from pathlib import Path

import feeds
from spec import SpecFile


def custom_bun(spec: SpecFile, pkg_dir: Path) -> None:
    # the main-branch LATEST file is not reliable (it read 1.3.14 while the
    # spec was already at 1.4.3, so the sweep would have downgraded it); the
    # GitHub release tag (bun-vX.Y.Z) is what the Source URL is built from
    tag = feeds.github_release_tag("oven-sh/bun")
    spec.set_version(re.sub(r"^(?:bun-)?v?", "", tag))


def custom_gnuplot(spec: SpecFile, pkg_dir: Path) -> None:
    # gnuplot publishes on SourceForge, not GitHub; the linux filename of
    # best_release.json carries the version.
    data = feeds.fetch_json("https://sourceforge.net/projects/gnuplot/best_release.json")
    filename = data["platform_releases"]["linux"]["filename"]
    spec.set_version(feeds.find_group(r"gnuplot-([0-9.]+)\.tar\.gz$", filename))


def custom_glow(spec: SpecFile, pkg_dir: Path) -> None:
    # glow builds from a Fedora-made vendor tarball (go-vendor-tools), so the
    # version tracked is Fedora rawhide's, not upstream's: take its Version,
    # the lookaside sha512 of that version's vendor tarball, and its
    # go-vendor-tools.toml (the licence-check pins must match the vendor tree)
    base = "https://src.fedoraproject.org/rpms/glow/raw/rawhide/f/"
    fspec = feeds.fetch_text(base + "glow.spec")
    version = feeds.find_group(r"(?m)^Version:[ \t]*(\S+)", fspec)
    sources = feeds.fetch_text(base + "sources")
    tarball = f"glow-{version}-vendor.tar.bz2"
    sha512 = feeds.find_group(
        r"(?m)^SHA512 \(" + re.escape(tarball) + r"\) = ([0-9a-f]{128})",
        sources)
    toml = feeds.fetch_text(base + "go-vendor-tools.toml")
    spec.set_version(version)
    spec.set_source(
        1,
        "https://src.fedoraproject.org/repo/pkgs/glow/"
        "glow-%{version}-vendor.tar.bz2/sha512/" + sha512
        + "/glow-%{version}-vendor.tar.bz2",
    )
    (pkg_dir / "go-vendor-tools.toml").write_text(toml)


def custom_kilo(spec: SpecFile, pkg_dir: Path) -> None:
    # the GitHub tag space is polluted by jetbrains/* tags; the npm dist-tag
    # is the channel the CLI's own updater follows
    data = feeds.fetch_json("https://registry.npmjs.org/@kilocode/cli/latest")
    spec.set_version(data["version"])


def custom_marksman(spec: SpecFile, pkg_dir: Path) -> None:
    # the raw date tag goes into %markstag for the source URLs; the version is
    # the tag with dashes converted to dots (RPM versions cannot carry dashes)
    tag = feeds.github_release_tag("artempyanykh/marksman")
    spec.set_global("markstag", tag)
    spec.set_version(tag.replace("-", "."))


def custom_opencode(spec: SpecFile, pkg_dir: Path) -> None:
    # the v2 line ships through opencode.ai's own update API, not GitHub
    # releases; the npm scope carrying the cli-linux-x64 tarball is resolved
    # from the same endpoint and Source0 is rewritten when the scope moves.
    meta = feeds.fetch_text("https://opencode.ai/update/api/latest/cli/npm")
    spec.set_version(feeds.find_group(r'"version":"([^"]+)"', meta))
    scope = "@opencode"
    m = re.search(r'"package":"([^"]*)/cli"', meta)
    if m:
        scope = m.group(1)
    if scope != "@opencode":
        spec.set_source(
            0,
            "https://registry.npmjs.org/" + scope
            + "%2Fcli-linux-x64/-/cli-linux-x64-%{version}.tgz",
        )
        spec.set_source(
            1,
            "https://registry.npmjs.org/" + scope
            + "%2Fcli-linux-x64-baseline/-/cli-linux-x64-baseline-%{version}.tgz",
        )


def custom_claude_code(spec: SpecFile, pkg_dir: Path) -> None:
    # the official dnf channel is both the artifact source and the version
    # authority: npm may publish ahead of downloads.claude.ai, the repodata
    # cannot lie about what the channel serves. The channel keeps a long
    # tail of old versions — rank every entry with rpmvercmp.
    channel = "https://downloads.claude.ai/claude-code/rpm/latest/"
    repomd = feeds.fetch_text(channel + "repodata/repomd.xml")
    href = feeds.find_group(
        r'href="(repodata/[^"]*-primary\.xml\.gz)"', repomd)
    primary = gzip.decompress(feeds.fetch_bytes(channel + href)).decode()
    versions = set()
    for entry in primary.split("<package"):
        if "<name>claude-code</name>" not in entry:
            continue
        versions.add(feeds.find_group(r'ver="([^"]+)"', entry))
    if not versions:
        raise feeds.FeedError("claude-code missing from the rpm channel")
    from vercmp import rpmvercmp

    best = ""
    for version in versions:
        if not best or rpmvercmp(version, best) > 0:
            best = version
    spec.set_version(best)


def custom_atuin(spec: SpecFile, pkg_dir: Path) -> None:
    # the spec builds from the crates.io .crate, and crates.io does not
    # always serve the version a GitHub release names: 18.24.2 was
    # unpublished upstream (API 404, static URL 403) while the GH tag stayed
    # up, pinning the spec to a version the registry refuses to serve —
    # every rebuild 403'd at spectool. Track the newest version crates.io
    # lists as not yanked; deleted versions drop out of the list entirely.
    data = feeds.fetch_json("https://crates.io/api/v1/crates/atuin/versions")
    from vercmp import rpmvercmp

    best = ""
    for v in data["versions"]:
        if v["yanked"]:
            continue
        num = v["num"]
        if not best or rpmvercmp(num, best) > 0:
            best = num
    if not best:
        raise feeds.FeedError("atuin: no servable version on crates.io")
    spec.set_version(best)
