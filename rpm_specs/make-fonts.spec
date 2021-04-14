Name: font-simsun
Version: 0.1
Release: 1
Summary: install simsun

Group: Enterprise/Linux	
License: GPL	
URL: http://www.both.org	
Source0: simsun-%{version}.tar.gz 

BuildRequires: bash
Requires: bash	

%description
install font

%prep
%setup -q

%build

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p ${RPM_BUILD_ROOT}/usr/share/fonts/
install -m755 simsun.ttc ${RPM_BUILD_ROOT}/usr/share/fonts/

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-, root, root)
%attr(0744, root, root) /usr/share/fonts/simsun.ttc

%post

%changelog

