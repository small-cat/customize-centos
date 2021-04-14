#!/bin/bash

rpmname=$1

if [ $# -ne 1 ]; then
	echo "$0 [filename]"
	echo "for example:"
	echo "	$0 yum-utils"
	exit -1
fi

downloaddir="download_dir"
mkdir -p ${downloaddir}
yumdownloader --resolve --destdir=${downloaddir} ${rpmname}
