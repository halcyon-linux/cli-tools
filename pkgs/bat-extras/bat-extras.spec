Name:           bat-extras
Version:        2024.08.24
Release:        2%{?dist}
%define debug_package %{nil}
Summary:        Bash scripts that integrate bat with various command line tools
BuildArch:      noarch

License:        MIT
URL:            https://github.com/eth-p/bat-extras
Source0:        %{url}/archive/v%{version}/bat-extras-%{version}.tar.gz

BuildRequires:  bash
Requires:       bash
Requires:       bat

Recommends:     ripgrep
Recommends:     git

%description
Bash scripts that integrate bat with various command line tools:
batdiff, batgrep, batman, batpipe, batwatch and prettybat.

%prep
%autosetup

%build
# build.sh assembles the scripts (version comes from version.txt, not the
# build environment) and renders the doc/ markdown into man/ pages

%install
./build.sh --install --prefix=%{buildroot}%{_prefix} --no-verify
mkdir -p %{buildroot}%{_mandir}/man1
install -m644 -t %{buildroot}%{_mandir}/man1 man/*

%files
%license LICENSE.md
%{_bindir}/bat*
%{_bindir}/prettybat
%{_mandir}/man1/*

%changelog
* Tue Oct 27 2026 ahsan <aahsnr041@proton.me> - 2024.08.24-2
- add the missing runtime dependencies
* Mon Sep 28 2026 ahsan <aahsnr041@proton.me> - 2024.08.24-1
- initial package (ported from Terra's bat-extras spec)
