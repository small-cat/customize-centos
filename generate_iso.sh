#!/bin/bash

# enter repodata
cd ISO/repodata
rm -f *.bz2 *.gz
rm -f repomd.xml
mv *.xml comps.xml
cd ..

# enter ISO
isoname="CentOS7-secsmart-platform-`date "+%Y%m%d"`.iso"

createrepo -g repodata/comps.xml ./
genisoimage -joliet-long -V CentOS7 -o ${isoname} -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -R -J -v -cache-inodes -T -eltorito-alt-boot -e images/efiboot.img -no-emul-boot ./
implantisomd5 ${isoname}

mv ${isoname} ../
