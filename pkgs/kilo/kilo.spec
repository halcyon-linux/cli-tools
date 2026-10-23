# The release tarball is a multi-file tree, not a single binary: the main
# executable needs its sandbox helpers (bwrap + seccomp), the console web
# UI and the tree-sitter WASM grammars as siblings — all installed under
# /usr/lib/kilo with a wrapper that pins the grammar directory.
%define debug_package %{nil}
%global _build_id_links none
# kilo is a bun-compiled executable that picks its CLI by program name. The
# default post-install optimizations (strip and friends) corrupt its embedded
# payload, and a corrupted binary runs as the bare bun CLI instead — the same
# failure opencode.spec documents. Disable every post-install step.
%global __os_install_post %{nil}
%define __strip /bin/true

Name:           kilo
Version:        7.8.17
Release:        1%{?dist}
Summary:        The AI coding agent built for the terminal

License:        MIT AND LGPL-2.0-or-later
URL:            https://github.com/Kilo-Org/kilocode
Source0:        %{url}/releases/download/v%{version}/kilo-linux-x64.tar.gz
ExclusiveArch:  x86_64

Requires:       ripgrep

%description
Kilo is an AI coding agent for the terminal: it plans, edits and runs code
across a workspace, with sandboxed command execution (bundled bubblewrap),
a built-in web console and tree-sitter grammars for its code intelligence.

%prep
%autosetup -n %{name} -c

%build
# prebuilt upstream tree

%install
install -d %{buildroot}%{_libdir}/%{name} %{buildroot}%{_bindir}
install -pm0755 kilo %{buildroot}%{_libdir}/%{name}/kilo
install -pm0755 bwrap %{buildroot}%{_libdir}/%{name}/bwrap
install -pm0644 kilo-sandbox-mutation-worker.js %{buildroot}%{_libdir}/%{name}/
cp -a tree-sitter %{buildroot}%{_libdir}/%{name}/tree-sitter
# the wrapper pins the grammar dir; the sandbox helpers are resolved
# relative to the real binary
cat > %{buildroot}%{_bindir}/kilo <<'EOF'
#!/bin/sh
export KILO_TREE_SITTER_WASM_DIR=%{_libdir}/%{name}/tree-sitter
exec %{_libdir}/%{name}/kilo "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/kilo
install -d %{buildroot}%{_licensedir}/%{name}
cp -a licenses/. %{buildroot}%{_licensedir}/%{name}/

%check
# a corrupted payload runs the bare bun CLI, which prints bun's own version
# and never this package's — fail the build instead of shipping it
out="$(HOME=%{_builddir} %{buildroot}%{_libdir}/%{name}/kilo --version 2>&1 || true)"
echo "$out"
echo "$out" | grep -qF '%{version}'

%files
%license %{_licensedir}/%{name}/
%{_bindir}/kilo
%{_libdir}/%{name}/

%changelog
* Thu Oct 22 2026 ahsan <aahsnr041@proton.me> - 7.8.12-2
- disable the post-install optimizations that corrupted the bun-compiled
  binary (it ran as the bare bun CLI) and add a version check in the check stage
* Sat Sep 26 2026 halcyon-autoupdate <aahsnr041@proton.me> - 7.8.1-1
- initial packaging (release-tree wrapper per the kilo-bin AUR pattern;
  the GitHub release feed is polluted by jetbrains tags, so the sweep
  tracks the npm dist-tag)
