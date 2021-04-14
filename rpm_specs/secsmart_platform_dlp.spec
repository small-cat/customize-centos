Name: secsmart_platform_dlp
Version: 1.0
Release: 1
Summary: test for build rpm	

Group: Enterprise/Linux	
License: GPL	
URL: http://www.both.org	
Source0: secsmart_platform_dlp-%{version}.tar.gz 

BuildRequires: bash
Requires: bash	

%description
install all in one

%prep
%setup -q

%build

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p ${RPM_BUILD_ROOT}/data/all_in_one
install -m755 dlp.tar.gz ${RPM_BUILD_ROOT}/data/all_in_one

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-, root, root)
%attr(0744, root, root) /data/all_in_one/dlp.tar.gz

%post

%changelog

