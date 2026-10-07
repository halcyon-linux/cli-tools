# Fedora f45 dist-git glow.spec (src.fedoraproject.org/rpms/glow, branch
# f45 — identical to rawhide), adapted to this repo's build flow:
#   - Source1 carries the FULL Fedora lookaside URL (sha512 embedded) so
#     `spectool -g` can fetch it at SRPM-build time (Copr builds have no
#     network and the submit job has no lookaside integration)
#   - Source2 (go-vendor-tools.toml) is a local file shipped from pkgs/glow/
#   - explicit Release + changelog instead of %autorelease/%autochangelog
#     (no dist-git context in Copr)
# Bump procedure: take Fedora's matching new version AND its new vendor
# tarball — update Version, the Source1 hash and filename together.
%bcond check 1

%global gomodulesmode GO111MODULE=on

Name:           glow
Version:        3.0.0
Release:        1%{?dist}
ExclusiveArch:  %{golang_arches_future}
Summary:        Terminal based markdown reader
License:        Apache-2.0 AND BSD-3-Clause AND MIT AND OFL-1.1
URL:            https://github.com/charmbracelet/glow
Source0:        %{url}/archive/v%{version}/glow-%{version}.tar.gz
Source1:        https://src.fedoraproject.org/repo/pkgs/glow/glow-%{version}-vendor.tar.bz2/sha512/2e5ca31e5766c3f3664977e2f5f2dbbc333a743fbd113d6f6c930722aa6d2314de5e1cc54f1437ba56fa8edd025cf553653a4e4b8ccb698dd28142406eb5a98c/glow-%{version}-vendor.tar.bz2
Source2:        go-vendor-tools.toml

BuildRequires:  go-rpm-macros
BuildRequires:  go-vendor-tools
BuildRequires:  askalono-cli


%description
Glow is a terminal based markdown reader designed from the ground up to bring
out the beauty—and power—of the CLI.  Use it to discover markdown files, read
documentation directly on the command line.  Glow will find local markdown
files in subdirectories or a local Git repository.


%prep
%autosetup -p 1 -a 1


%build
export GO_LDFLAGS="-X main.Version=v%{version}"
%gobuild -o bin/glow .


%install
# licenses
%go_vendor_license_install -c %{S:2}

# command
install -D -p -m 0755 -t %{buildroot}%{_bindir} bin/glow

# man page
install -d -m 0755 %{buildroot}%{_mandir}/man1
./bin/glow man > %{buildroot}%{_mandir}/man1/glow.1

# shell completions
install -d -m 0755 %{buildroot}%{bash_completions_dir}
./bin/glow completion bash > %{buildroot}%{bash_completions_dir}/glow
install -d -m 0755 %{buildroot}%{zsh_completions_dir}
./bin/glow completion zsh > %{buildroot}%{zsh_completions_dir}/_glow
install -d -m 0755 %{buildroot}%{fish_completions_dir}
./bin/glow completion fish > %{buildroot}%{fish_completions_dir}/glow.fish


%check
# ensure that the version was embedded correctly
[[ "$(./bin/glow --version)" == "glow version v%{version}" ]] || exit 1

# license validation
%go_vendor_license_check -c %{S:2}

# upstream tests
%if %{with check}
%gocheck2
%endif


%files -f %{go_vendor_license_filelist}
%{_bindir}/glow
%{_mandir}/man1/glow.1*
%{bash_completions_dir}/glow
%{zsh_completions_dir}/_glow
%{fish_completions_dir}/glow.fish


%changelog
* Tue Oct 07 2026 ahsan <aahsnr041@proton.me> - 3.0.0-1
- import Fedora f45's glow.spec (source build via go-vendor-tools; the
  vendored-dependencies tarball comes from Fedora's lookaside) — was:
  glow only shipped in the bazzite base
