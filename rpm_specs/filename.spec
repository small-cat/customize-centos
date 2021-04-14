Name: jdk1.8.0_221
Version: 0.1
Release: 1
Summary: test for build rpm	

Group: Enterprise/Linux	
License: GPL	
URL: http://www.both.org	
Source0: jdk1.8.0_221-%{version}.tar.gz 

BuildRequires: bash
Requires: bash	

%description
install all in one

%prep
%setup -q

%build

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p ${RPM_BUILD_ROOT}/data/jdk
install -m755 jdk1.8.0_221.tar.gz ${RPM_BUILD_ROOT}/data/jdk

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-, root, root)
%attr(0744, root, root) /data/jdk/jdk1.8.0_221.tar.gz

%post

%changelog

