# claude-code: vendor rewrap of Anthropic's own dnf RPM — the house rule
# allows a rewrap when upstream itself ships an RPM, and this is the reference
# case: the payload is exactly /usr/bin/claude (a bun-compiled, fully
# self-contained executable) plus a copyright file, with glibc as the only
# dependency. The binary is the same tool family as opencode/kilo: the
# default post-install optimizations (strip and friends) corrupt its embedded
# payload, and a corrupted binary runs as the bare bun CLI — see
# opencode.spec. Disable every post-install step. The version tracks the
# official latest channel, the same URL the sweep reads (ci/sweep/custom.py),
# so what we package is exactly what the channel serves.
%define debug_package %{nil}
%global _build_id_links none
%global __os_install_post %{nil}
%define __strip /bin/true

Name:           claude-code
Version:        2.1.311
Release:        1%{?dist}
Summary:        Agentic coding tool that lives in the terminal
# proprietary: Anthropic PBC, all rights reserved — the legal agreements ship
# as the copyright file; no SPDX identifier exists
License:        LicenseRef-Anthropic-Commercial
URL:            https://code.claude.com/docs/en/setup
Source0:        https://downloads.claude.ai/claude-code/rpm/latest/Packages/claude-code-%{version}-1.x86_64.rpm
ExclusiveArch:  x86_64

BuildRequires:  cpio

%description
Claude Code is Anthropic's agentic coding tool that lives in the terminal.
Repackaged from Anthropic's own signed dnf RPM (latest channel); package
manager installs do not auto-update on their own — the halcyon sweep is the
updater.

%prep
%setup -q -c -T
# the source is an RPM, not an archive rpmbuild can unpack: extract the
# payload with rpm2cpio
rpm2cpio %{SOURCE0} | cpio -idmu --quiet
test -x usr/bin/claude || { echo "ERROR: payload missing after extraction"; exit 1; }

%build
# prebuilt upstream payload

%install
install -Dm0755 usr/bin/claude %{buildroot}%{_bindir}/claude
install -Dm0644 usr/share/doc/claude-code/copyright %{buildroot}%{_licensedir}/%{name}/copyright

%check
# a corrupted payload runs the bare bun CLI, which prints bun's own version
# and never this package's — fail the build instead of shipping it
out="$(%{buildroot}%{_bindir}/claude --version 2>&1 || true)"
echo "$out"
echo "$out" | grep -qF '%{version}'

%files
%license %{_licensedir}/%{name}/copyright
%{_bindir}/claude

%changelog
* Mon Oct 26 2026 ahsan <aahsnr041@proton.me> - 2.1.310-1
- initial packaging: vendor rewrap of Anthropic's official dnf RPM (latest
  channel); bun payload — post-install steps fully disabled per the
  opencode/kilo precedent
