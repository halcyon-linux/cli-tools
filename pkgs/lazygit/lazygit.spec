Name:           lazygit
Version:	0.66.2
Release:        2%{?dist}
Summary:        Simple terminal UI for git commands
License:        MIT
URL:            https://github.com/jesseduffield/lazygit
Source0:        %{url}/releases/download/v%{version}/lazygit_%{version}_Linux_x86_64.tar.gz
Source1:        %{url}/raw/v%{version}/LICENSE
ExclusiveArch: x86_64
Requires:       git

%description
A simple terminal UI for git commands, built from the upstream release binary.
%prep
%setup -q -c -T -a 0
%define debug_package %{nil}
%global _build_id_links none
%global __os_install_post %{nil}
%install
# vendor tarballs ship no license text; the repo LICENSE rides along
install -Dpm0644 %{SOURCE1} %{buildroot}%{_licensedir}/%{name}/LICENSE
install -Dm0755 lazygit %{buildroot}%{_bindir}/lazygit
%files
%license LICENSE
%{_bindir}/lazygit
%changelog
* Tue Oct 27 2026 ahsan <aahsnr041@proton.me> - 0.66.2-2
- disable the post-install optimizations (full nil set for a foreign binary)
- add the missing runtime dependencies
* Sat Sep 19 2026 halcyon-autobuild - 0.65.1-1
- packaged from upstream release binary
