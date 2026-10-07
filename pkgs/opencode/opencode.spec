# opencode v2 (the major rewrite) — packaged after the approach of
# ferdiu/opencode-sandbox-copr, on the v2 npm artifacts:
#
# The binary is a bun-compiled executable that DISPATCHES ON basename(argv[0]):
# named "opencode" it runs the opencode CLI, but Fedora's default post-install
# optimization steps (brp-strip, strip-comment-note, lto, python-hardlink,
# linkdupes) are documented to break bun-compiled binaries — a mangled
# payload presents as the RAW BUN CLI (the 2.0.20/2.0.23 VM regression: the
# RPM-installed --version printed the bun banner while the unstripped
# curl-installer copy of the same code printed "opencode v2.0.24"). So:
#   - every brp optimization that touches the file is disabled below
#   - the binaries live OFF PATH under %{_libexecdir}/opencode/
#   - /usr/bin/opencode is wired via update-alternatives
#     (plain = priority 100, x64-baseline = 90 — VMs and older CPUs need the
#     baseline build; upstream publishes both on npm)
# Sources are the SAME npm tarballs the v2 installer
# (`curl -fsSL https://opencode.ai/v2/install | bash`) extracts
# package/bin/opencode from — one per variant, version swept from
# https://opencode.ai/update/api/latest/cli/npm via ci/sweep/custom.py.
%global debug_package %{nil}
%define __strip /bin/true
%define __brp_strip /bin/true
%define __brp_strip_comment_note /bin/true
%define __brp_strip_lto /bin/true
%define __brp_python_hardlink /bin/true
%define __brp_linkdupes /bin/true

Name:           opencode
Version:        2.0.24
Release:        1%{?dist}
Summary:        AI coding agent for the terminal
License:        MIT
URL:            https://opencode.ai
Source0:        https://registry.npmjs.org/@opencode%2Fcli-linux-x64/-/cli-linux-x64-%{version}.tgz
Source1:        https://registry.npmjs.org/@opencode%2Fcli-linux-x64-baseline/-/cli-linux-x64-baseline-%{version}.tgz
# prebuilt foreign binary: no debug sources to collect
%define debug_package %{nil}
%global _build_id_links none

ExclusiveArch: x86_64
%description
AI coding agent built for the terminal, from the upstream v2 release binary
(bun-compiled, fully self-contained — no Bun or Node.js runtime required).

%prep
%setup -q -c -T
# each variant tarball unpacks as package/bin/opencode
mkdir plain baseline
tar -xzf %{SOURCE0} -C plain
tar -xzf %{SOURCE1} -C baseline
mv plain/package/bin/opencode opencode-plain
mv baseline/package/bin/opencode opencode-baseline
# fail loudly if a variant is missing rather than shipping a broken RPM
test -e opencode-plain || { echo "ERROR: opencode-plain not found after unpack"; exit 1; }
test -e opencode-baseline || { echo "ERROR: opencode-baseline not found after unpack"; exit 1; }

%install
install -Dm0755 opencode-plain    %{buildroot}%{_libexecdir}/opencode/opencode
install -Dm0755 opencode-baseline %{buildroot}%{_libexecdir}/opencode/opencode-baseline
# /usr/bin/opencode is created by update-alternatives in %post — never a
# packaged file, so nothing on PATH can shadow or be shadowed
install -d %{buildroot}%{_bindir}

%check
# the same guard that caught the mangled-binary regression: the binary must
# identify as opencode, never fall back to the raw bun CLI
%{buildroot}%{_libexecdir}/opencode/opencode --version | grep -q '^opencode v'
%{buildroot}%{_libexecdir}/opencode/opencode-baseline --version | grep -q '^opencode v'

%post
# priorities: plain = 100 (default), x64-baseline = 90 (ferdiu's scheme)
update-alternatives --install %{_bindir}/opencode opencode \
    %{_libexecdir}/opencode/opencode 100 >/dev/null 2>&1 || :
update-alternatives --install %{_bindir}/opencode opencode \
    %{_libexecdir}/opencode/opencode-baseline 90 >/dev/null 2>&1 || :
update-alternatives --set opencode %{_libexecdir}/opencode/opencode >/dev/null 2>&1 || :

%postun
if [ "$1" -eq 0 ]; then
  update-alternatives --remove opencode %{_libexecdir}/opencode/opencode >/dev/null 2>&1 || :
  update-alternatives --remove opencode %{_libexecdir}/opencode/opencode-baseline >/dev/null 2>&1 || :
fi

%files
%dir %{_libexecdir}/opencode
%{_libexecdir}/opencode/opencode
%{_libexecdir}/opencode/opencode-baseline

%changelog
* Tue Oct 07 2026 ahsan <aahsnr041@proton.me> - 2.0.24-1
- borrow ferdiu/opencode-sandbox-copr's packaging for v2: disable every brp
  step that mangles bun-compiled binaries, install both npm variants (plain +
  x64-baseline) off PATH under %%{_libexecdir}, expose /usr/bin/opencode via
  update-alternatives — the raw-copy-into-/usr/bin spec shipped a binary
  that presented as the raw bun CLI on the rebased image
- sweep switched to the v2 npm artifacts; no baseline GitHub assets exist on
  the v1-only release feed
* Tue Sep 22 2026 halcyon-autobuild - 2.0.14-5
- follow the v2 line (major rewrite): the version now sweeps
  opencode.ai/update/api/latest/cli/npm and the binary comes from the
  @opencode/cli-linux-x64 npm package (the old v1 GitHub-release zip asset
  no longer tracks the current version)
* Tue Sep 22 2026 halcyon-autobuild - 1.18.31-4
- follow the current release artifact: opencode-linux-x64.tar.gz (the
  opencode-linux-x64.zip asset of the 0.12.0 era is gone upstream) and
  un-tar in %prep instead of unzip; latest release is 1.18.31
- drop %%license (the archive contains only the opencode binary) and the
  unused curl/unzip BuildRequires
* Mon Sep 21 2026 halcyon-autobuild - 0.12.0-3
- take the release zip from the source directory instead of curl in %prep
  (Copr builds have no network; the source method script ships the file)
* Mon Sep 21 2026 halcyon-autobuild - 0.12.0-2
- fix upstream repo: sst/opencode was renamed to anomalyco/opencode
- fix release asset name: opencode-linux-x64.zip, not opencode-linux-x86_64.zip
- add missing BuildRequires: curl, unzip (used in %prep but never declared)
