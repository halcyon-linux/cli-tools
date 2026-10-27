# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Overview

RPM package repo for the **halcyon CLI toolchain**, one of six halcyon group
repos (base-pkgs, cli-tools, applications, fonts, texlive-packages, linux-p03),
each with its own GitHub repo under
[halcyon-linux](https://github.com/orgs/halcyon-linux/repositories) and its own
Copr project under `aahsnr-work`. Packages build on Fedora Copr
([aahsnr-work/cli-tools](https://copr.fedorainfracloud.org/coprs/aahsnr-work/cli-tools/);
chroots fedora-44-x86_64 and fedora-45-x86_64) from CI. The repo holds only
specs, the registry, the version sweeper and workflows. Copr owns the build
farm, GPG signing and hosting. Fedora 44 is the target; the fc45 chroot exists
so breakage surfaces one release early.

Consumers install with `dnf copr enable aahsnr-work/cli-tools fedora-44`.

## Layout

- `pkgs/<pkg>/<pkg>.spec`: one spec per package
- `ci/packages.toml`: the registry (build selection + sweep feed config)
- `ci/matrix.py`: validates the registry, computes the build plan
- `ci/sweep/`: version sweeper (`sweep.py`, `feeds.py`, `custom.py`, `drift.py`, `spec.py`, `vercmp.py`)
- `templates/*.spec.tmpl`: starting points for new specs
- `repo/cli-tools.repo`: consumer drop-in used by repoclosure
- `.github/`: workflows (`copr-build.yml`, `update.yml`, ...)

## Ignored files

Never read, open, grep, summarize or add these to context, in the main session
or in any subagent, unless the user explicitly names the file for the task at
hand. Read access is also blocked by `permissions.deny` in
`.claude/settings.json`; keep the two lists in sync. Code, the registry (`ci/packages.toml`) and the workflows are
the source of truth.

- `TODO.md`, `notes/` and any other markdown file not named in this list
  (`README.md` is for humans; don't treat it as a spec for your behavior)
- `AGENTS.md` (removed; do not recreate)
- Local artefacts, also listed in `.gitignore`: `_srpms/`, `tmp/`, `.mimosa/`,
  `.obsidian/`, `TaskNotes/`, `.cache/`, `.zcode/`, `.zcodeignore`,
  `__pycache__/`, `*.tar.gz`, `*.tar.bz2`, `*.rpm`, `*.zst`

## Commands

There is no test suite; verification means the Copr build going green.

```bash
# registry consistency + build plan (what CI's validate job runs)
python3 ci/matrix.py --list
python3 ci/matrix.py --list --since <sha>   # what a push would rebuild

# submit ONE package to Copr (run inside the CI image or a fedora:44 container)
spectool -g -C _srpms/<pkg> pkgs/<pkg>/<pkg>.spec
rpmbuild -bs --define "_sourcedir $PWD/_srpms/<pkg>" \
         --define "_srcrpmdir $PWD/_srpms" \
         --define "_specdir $PWD/pkgs/<pkg>" pkgs/<pkg>/<pkg>.spec
copr-cli build --nowait cli-tools _srpms/<pkg>-*.src.rpm

# version sweep (update.yml)
GITHUB_TOKEN=$(gh auth token) python3 ci/sweep/sweep.py [--pkg <name>]

# local mock buildroot identical to Copr's
copr-cli mock-config aahsnr-work/cli-tools fedora-44-x86_64 > /tmp/copr.cfg
mock -r /tmp/copr.cfg <srpm>
```

## Registry and build rules

- **A package without a `ci/packages.toml` entry is never built.** Adding a
  package takes two files: `pkgs/<pkg>/<pkg>.spec` (from `templates/*.spec.tmpl`)
  and the registry entry (`batch` + `[pkg.updates]` feed).
- **Batches are dependency levels.** A package's `batch` must be >= 1 + the
  highest batch of anything it BuildRequires. Packages in one batch build in
  parallel and must not depend on each other. `ci/matrix.py` enforces this.
- **A push to `main` rebuilds changed packages plus every higher batch**,
  submitted wave by wave. Cascades are gated on the `CASCADE_ENABLED` repo
  variable (`false` stops them; `workflow_dispatch` bypasses it). PRs run
  validation only.
- `copr-build.yml` carries exactly the submitN/waitN pairs for populated
  batches, chained in ascending order. A package in an existing batch needs no
  workflow change. A package at a new batch level needs its pair added first
  (copy the previous populated pair, renumber, chain after it).
- Touching `ci/**` or `.github/builder/**` rebuilds every package
  (`INFRA_PREFIXES` in `ci/matrix.py`).
- **Version bumps are automatic** (`update.yml`: daily plus after every
  cascade). `ci/sweep/sweep.py` reads each `[pkg.updates]` table
  (`feed = "github-release" | "github-tag" | "custom"` + `repo`) and edits
  specs in place. Release resets only on a real version change, files are
  written only on content change, and downgrades are refused. `ci/sweep/drift.py`
  dispatches builds only for packages ahead of Copr. Custom feeds live in
  `ci/sweep/custom.py`. Bumps commit straight to main unless the `UPDATE_MODE`
  repo variable is `pr`.
- **CI auth**: the `COPR_CLICONF` secret drives every copr-cli step. A wave of
  401s means the Copr API token expired: regenerate at
  <https://copr.fedorainfracloud.org/api/>, re-set the secret, re-run.

## Spec conventions (terra-style, differ from Fedora defaults)

- Full URLs in `Source*` entries; the submit job's `spectool -g` fetches them
  before `rpmbuild -bs`. Keep downloads out of `%prep`.
- Explicit `Release: N%{?dist}` plus a written `%changelog`. No
  rpmautospec/`%autorelease`.
- **Never mention macros textually in comments**; rpm expands macros inside
  comments too.
- Build-time repos outside Fedora/Terra go in the Copr chroot's repo list
  (`copr-cli edit-chroot aahsnr-work/cli-tools/fedora-44-x86_64 --repos ...`),
  not the spec. Configured: Terra 44 and the `lionheartp/Hyprland`
  lowest-priority bootstrap.
- No debug packages: every spec carries the debug_package nil define.
- **Vendor rewraps** are allowed only when upstream ships an RPM or a
  self-contained release archive; anything else is a source build. A foreign
  binary tree needs the full nil set (debug_package nil, `_build_id_links none`,
  `__os_install_post` nil). Do not remove those defines.
- Never use forgeautosetup/forgemeta without defining the forgemeta state; the
  archive dir name derives wrong. Use plain `%autosetup -n <archive-dir>`.
- Validate a spec against the UPSTREAM tarball, not from memory; release
  layouts drift.
- `install -t DIR SRC` keeps SRC's basename, so `%files` must claim the name as
  installed. Prefer `install -Dm644 SRC %{buildroot}%{dir}/NAME`.

### Rust packages

Built from source with an inline online-cargo prep (`cargo-rpm-macros` from
Fedora plus the config block each spec carries in its prep stage; `starship` is
the reference).

- Spell out the static.crates.io URL in `Source:`; don't use the crates.io URL
  macro (sources are fetched before buildroot macros exist).
- Use `-- --locked` on the cargo install macro.
- Undefine the shebang mangler (vendored crate sources trip the debugsource scan).
- Set `rustflags_debuginfo 0`.
- `SCCACHE_DIR=/sccache` works on Copr; the cache is ephemeral per build.
