# customize-centos
customize your centos operating system. cut off the rpms you don't want and pre install packages you need.

# tutorial

以虚拟机为例

## 挂载镜像

将iso镜像添加到虚拟机上，挂载后的设备为 `/dev/sr1`，将其挂载到 `/media` 目录中

```
mount /dev/sr1 /media
lsblk
```

## 安装制作发行版的工具

```text
yum -y install createrepo mkisofs isomd5sum rsync
```

## 同步光盘文件到制作ISO的目录

```text
#同步/media下的文件到/ISO路径下，除了Packages和repodata文件夹
/usr/bin/rsync -a --exclude=Packages/ --exclude=repodata/ /media/ /ISO/
# 在/ISO/文件夹下新建Packages和repodata文件夹
mkdir -p /ISO/{Packages,repodata}
```

## 拷贝 rpm

### 生成install.log

```text
rpm -qa >> /root/install.log
```

### 拷贝已安装rpm

```text
awk '{print $0}'  /root/install.log |xargs -i cp /media/Packages/{}.rpm /ISO/Packages/
```

## 配置yum下载指定软件包列表（`rpms_list.txt`）的所有依赖包

将需要安装的包及其以来写入 `rpms_list.txt`

```text
#!/bin/sh   
for line in `cat /root/rpms_list.txt`
    do
       echo "download file>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>and it's denpendies"$line
     yum install -y --downloadonly --downloaddir=/root/test/ $line
#或者先安装yum -y install yum-utils再yumdownloader $line
    done
#yum查找.so或者某个依赖在哪个rpm包中
yum provides {.so名或者依赖名字}
#拷贝包到指定目录
cp /root/test/* /ISO/Packages/
```

rpm 相关操作

```
yum list | grep XXX # 搜索
yum deplist XXX # 查看依赖
yum install --downloadonly --downloaddir=/packages XXX # 仅仅下载，不安装
yumdownloader --resolve --destdir /packages XXX # 下载
```

> 安装包的所有依赖必须齐全，否则安装系统时，会出错

## 修改 `isolinux.cfg` 文件

```text
label linux
menu label ^Install CentOS 7
kernel vmlinuz
#这样是不自动安装
append initrd=initrd.img inst.stage2=hd:LABEL=CentOS7 quiet
#这样配置会自动安装
append initrd=initrd.img inst.stage2=hd:LABEL=CentOS7 inst.ks=hd:LABEL=CentOS7:/isolinux/ks.cfg quiet
```

> inst.ks为ks.cfg文件位置；
> inst.stage2为安装介质位置，hd:LABEL为介质标签，例如CentOS7。这个和后续生成ISO镜像文件的命令genisoimage的参数-V有关。
> 最好是把所有hd:LABEL后面的值都替换为一个后面会用到的字符串，如CentOS7

## 修改自动化安装配置文件

第一次手动安装系统完成后，安装程序中的所有选择都会保存到名为 `anaconda-ks.cfg` 的文件中，该文件位于所安装系统的 `/root/` 目录下。然后可以复制这个文件，根据需要进行修改，并在以后的安装中使用得到的配置文件。

```text
cp /root/anaconda-ks.cfg /ISO/isolinux/ks.cfg
```

在%packages与%end中间加入需要自定义安装的包组

```text
#安装所需要的软件包，把自定义的安装包添加进去即可在安装系统时自定义的软件
%packages
@^web-server-environment
@base
@core
@java-platform
@python-web
@web-server
kexec-tools
@{自定义包组的groupid}
%end

#安装完系统后，需要做什么事情请写在%post里面
%post
# Get interface up
ifdown eth0
ifup eth0
/usr/bin/chfn -f 'demo' demo
umount /dev/sr0
[ -e /tmp/sepolicy-devel.temp ] && rm /tmp/sepolicy-devel.temp
echo "..."
echo "setting network for openvswitch"
scriptsUrl="/etc/sysconfig/network-scripts"
if [ -e $scriptsUrl/ifcfg-eth0 ]
  then
    # disable NetworkManager
    systemctl disable NetworkManager

    # copy device  eth0 configure to ovs-br0
    cp $scriptsUrl/ifcfg-eth0 $scriptsUrl/ifcfg-br0

  else
    echo "device eth0 configure isn't exist,please check it!"
fi

sleep 2
reboot
%end
```

自定义包组的 groupid 就是定义在 `/repodata/comps.xml` 文件中的 group

## 制作修改comps文件

进入`/ISO`目录，将`*-x86_64-comps.xml`文件拷贝到`/ISO/repodata`路径下，并重命名成comps.xml。

```text
cp /media/repodata/*-x86_64-comps.xml  /ISO/repodata/comps.xml
```

### 编辑comps文件

#### 添加定制rpm包

```text
<group>
    <id>{自定义包组的groupid}</id>
    <name>My Dependencies</name>
    <default>true</default>
    <uservisible>true</uservisible> # 这个值为true，在安装界面才能看到，否则不可见
    <packagelist>
        <packagereq type="default">python-webob</packagereq>
        ......
    </packagelist>
</group>
```

> 根据 `rpms_list.txt` 拼接packagereq

```text
#!/bin/sh
for line in `cat rpms_list.txt`
    do
        echo " <packagereq type=\"default\">"$line"</packagereq>" >> /root/package.txt
    done
```

#### 在指定的环境中添加定制的groupid

```text
<environment>
        <id>web-server-environment</id>
        <name>Basic Web Server</name>
        <description>Server for serving static and dynamic internet content. </description>
        <display_order>30</display_order>
        <grouplist>
          <groupid>base</groupid>
          <groupid>core</groupid>
          <groupid>web-server</groupid>
          <groupid>{自定义包组的groupid}</groupid>
        </grouplist>
    </environment>
```

如果不再指定环境中添加，也就是 environment 的节点中添加新定义的 groupid，在系统安装界面就会提示 group 未定义的错误。

## 生成新的 `repodata` 数据

切换到ISO/路径下，由comps.xml生成repodata包。注意当有新包加入，或者更新comps.xml文件，均需要重新生成repodata文件夹

```text
createrepo -g repodata/comps.xml ./
```

## 制作ISO镜像

注意参数中的-V，和上面的`isolinux.cfg`文件有关

```text
cd /ISO
genisoimage -joliet-long -V CentOS7 -o CentOS-7-2.iso -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -R -J -v -cache-inodes -T -eltorito-alt-boot -e images/efiboot.img -no-emul-boot /ISO
```

选项 `-V CentOS7` 就是上面提及的 `inst.stage2=hd:LABEL=CentOS7`，如果是带有空格的，那就加上双引号，比如 `-V "CentOS 7 x86_64"`

## 制作镜像MD5值

```text
implantisomd5 /ISO/CentOS-7-2.iso
```

生成的 iso 镜像文件就可以直接用于安装系统了

# 一体化安装镜像

一体化安装，需要将`all_in_one`整个产品包都集成到 iso 镜像文件中，在上述所说的镜像制作步骤中，iso镜像在安装过程中，根据 `repodata/comps.xml` 和 `ks.cfg` 中指定的 package，将 package 中的所有 rpm 包进行安装。`all_in_one` 就是借鉴这个思路，将产品制作成 rpm 包，然后在 `repodata/comps.xml` 进行配置说明，这样在新的镜像中，系统安装的时候，就会将所有的组件全部安装完成。

## `all_in_one` 制作 rpm

rpm 制作的文件，有大小限制，整个 `all_in_one` 有 8 个多 G 的大小，超出了 rpm 包制作的大小限制，这里对 `all_in_one` 进行了切割。同时，`all_in_one` 内部的安装脚本，都是基于 bash shell 环境的，在 iso 镜像安装过程中，执行 shell 脚本，执行环境不同，会造成脚本执行失败，安装失败，这里采用的方法，**是在系统安装完成之后，第一次登录时，进行自动安装。**详细说明如下

## 对 `all_in_one` 进行切割

`all_in_one` 的目录结构如下所示

```
all_in_one
	- JDK
	- install.sh
	- uninstall.sh
	- Web
	- AppPackages
		- audit
		- dataassetmnt
		- ddm
		- dlp
		- firewall
		- scmpx
		- sdm
		- tde
```

将 AppPackages 下的产品，单独打包成 `tar.gz`，然后在将整个产品目录打包成 `tar.gz`，这样就划分成了 9 个 `tar.gz` 包，分别对每一个包进行 rpm 包的制作

## rpm 包的制作

rpm 制作，需要 rpmbuild 工具，通过如下方式安装

```
yum install | grep rpm-build
```

如果 yum 源有问题，centos7 按照下面的方法配置 yum 源

```
# 备份
mv /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.backup
# 下载
wget -O /etc/yum.repos.d/CentOS-Base.repo https://mirrors.aliyun.com/repo/Centos-7.repo

yum clean
yum makecache # 生成缓存
```

rpm 制作，需要准备后缀为 spec 的配置文件，rpmbuild 按照这个文件，找到源代码以及生成指令进行 rpm 的生成。以 audit 的 rpm 的制作为例，配置文件为 `secsmart_platform_audit.spec`

```
Name: secsmart_platform_audit
Version: 1.0
Release: 1
Summary: test for build rpm	

Group: Enterprise/Linux	
License: GPL	
URL: http://www.both.org	
Source0: secsmart_platform_audit-%{version}.tar.gz 

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
install -m755 audit.tar.gz ${RPM_BUILD_ROOT}/data/all_in_one

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-, root, root)
%attr(0744, root, root) /data/all_in_one/audit.tar.gz

%post

%changelog

```

执行

```
rpmbuild -ba secsmart_platform_audit.spec
```

会在当前用户的家目录下，生成 rpmbuild 的目录，目录结构如下

```
BUILD  BUILDROOT  RPMS  SOURCES  SPECS  SRPMS
```

这是 rpmbuild 工具的工作目录，所有的 spec 配置文件都必须放在 SPECS 目录中，源文件，也就是 `audit.tar.gz` 文件都必须放在 SOURCES 目录中，制作完成的 rpm 文件会存放在 RPMS 目录中。

### SPEC 配置解析

- Name - 名称
- Version - 版本号
- Release - 与 Version 类似，上面这三个配置项，是必须有的，不能为空
- Summary - 可以为空，描述
- Group
- License
- URL - 按照官方文档说明填写
- Source0 - 这个表示的制作 rpm 的源文件，这个源文件的命名，必须带上版本号，所以，`audit.tar.gz` 会按照如下的方式命名

首先创建 `secsmart_platform_audit-1.0` 的文件夹，然后将 `audit.tar.gz`  移动到文件夹中，在将文件夹打包成`secsmart_platform_audit-1.0.tar.gz`，将这个文件放到 `rpmbuild/SOURCES` 中

- BuildRequires - bash
- Requires - bash，这两个表示的rpm包的依赖，我们自己制作的安装包，不需要依赖，唯一依赖的就是 bash，在shell 环境下执行安装脚本
- build - 如果是源代码，通过这个配置，对源代码进行编译
- install - 这个就是安装脚本

```
# 1. 在制作过程中，会将临时文件存放在这个目录中，首先清空目录
rm -rf $RPM_BUILD_ROOT # rpmbuild 

# 2. 创建目录，RPM_BUILD_ROOT 对应的就是 rpm 在安装的时候的 / 目录，也就是创建 /data/all_in_one 目录
mkdir -p ${RPM_BUILD_ROOT}/data/all_in_one

# 3. 将 audit.tar.gz 文件 install，也就是 copy 到 /data/all_in_one 目录中
install -m755 audit.tar.gz ${RPM_BUILD_ROOT}/data/all_in_one
```

- files - 安装后的文件

```
# 安装完成之后的文件及其属性，也就说，audit 的rpm 安装完成后，在 /data/all_in_one/ 目录中，存在一个 audit.tar.gz 的文件
%attr(0744, root, root) /data/all_in_one/audit.tar.gz
```

### rpmbuild 制作过程简述

按照上述的配置文件，rpmbuild 工具在制作 rpm 时，首先在 `rpmbuild/SOURCES` 文件中，找到 `secsmart_platform_audit-1.0.tar.gz` 这个文件，然后解压缩，进入 `secsmart_platform_audit-1.0`，找到 `audit.tar.gz` 文件，对这个文件进行一些检验，然后根据 install 的命令，制作成 `secsmart_platform_audit-1.0-1.x86_64.rpm` 文件。

对这个文件直接通过

```
rpm -i secsmart_platform_audit-1.0-1.x86_64.rpm
```

进行安装，就能在 `/data/all_in_one` 目录下看到 `audit.tar.gz` 文件，说明安装成功

## 安装脚本的制作

`all_in_one` 的 9 个 rpm 包制作完成之后，镜像安装完成结束时，所有的文件都会被安装到了 `/data/all_in_one` 之中，且全部都是经过 gzip 压缩打包的文件。这个时候，还需要对其进行还原和安装。因为系统安装完成，bash shell 的环境也都准备好，这时候执行 `all_in_one` 的安装脚本，是没有问题的。

`install_secsmart_platform.sh` 脚本如下

```
function install_jdk
{
	# install jdk
	if [ ! -d /data/jdk ]; then
		echo "can not find jdk in /data/jdk"
		exit -1
	fi
	cd /data/jdk
	jdk_file=$(ls)
	jdk_installdir="/usr/local/jdk"
	echo "install ${jdk_file} ..."
	mkdir -p ${jdk_installdir}
	if [ $? -ne 0 ]; then
		exit -1
	fi
	
	tar xzvf ${jdk_file} -C ${jdk_installdir}
	chmod a+x ${jdk_installdir}/jdk1.8.0_221/bin/ -R
	chmod a+x ${jdk_installdir}/jdk1.8.0_221/jre/bin/ -R
	
	echo "set jdk environment to /etc/profile"
	echo "export JAVA_HOME=${jdk_installdir}/jdk1.8.0_221" >> /etc/profile
	echo "export CLASSPATH=.:\${JAVA_HOME}/jre/lib/rt.jar:\${JAVA_HOME}/lib/dt.jar:\${JAVA_HOME}/lib/tools.jar" >> /etc/profile
	echo "export PATH=\${JAVA_HOME}/bin:\${PATH}" >> /etc/profile
	echo "jdk install success"
	
	echo
}
	
function install_mysql {
	sed -i '/install_secsmart_platform\.sh install mysql/d' /etc/profile
	if [ ! -d /data/mysql ]; then
		echo "can not find mysql in /data/mysql"
		exit -1
	fi
	
	cd /data/mysql
	mysql_file=$(ls)
	echo "install ${mysql_file} ..."
	
	tar xzvf ${mysql_file}
	cd mysql-community
	./install.sh
	echo "mysql install success" 
	
	echo
}

function install_all_in_one {
	sed -i '/install_secsmart_platform\.sh install all_in_one/d' /etc/profile
	echo "install secsmart platform ..."
	if [ ! -d /data/all_in_one ]; then
	  echo "can not find all in one in /data/all_in_one"
	  exit -1
	fi 
	
	cd /data/all_in_one
	# 1. all_in_one.tar.gz, contains install.sh, uninstall.sh, and WebApp
	if [ ! -f all_in_one.tar.gz ]; then
	  echo "can not find all_in_one.tar.gz"
	  exit -1
	fi
	
	# name is secsmart_platform
	tar xzvf all_in_one.tar.gz
	
	# 2. audit
	if [ ! -f audit.tar.gz ]; then
	  echo "can not find audit.tar.gz"
	  exit -1
	fi
	tar xzvf audit.tar.gz -C secsmart_platform/AppPackages/
	
	# 3. dataassetmnt
	if [ ! -f dataassetmnt.tar.gz ]; then
	  echo "can not find dataassetmnt.tar.gz"
	  exit -1
	fi 
	tar xzvf dataassetmnt.tar.gz -C secsmart_platform/AppPackages/
	
	# 4. ddm
	if [ ! -f ddm.tar.gz ]; then
	  echo "can not find ddm.tar.gz"
	  exit -1
	fi 
	tar xzvf ddm.tar.gz -C secsmart_platform/AppPackages/
	
	# 5. dlp
	if [ ! -f dlp.tar.gz ]; then
	  echo "can not find dlp.tar.gz"
	  exit -1
	fi
	tar xzvf dlp.tar.gz -C secsmart_platform/AppPackages/
	
	# 6. firewall
	if [ ! -f firewall.tar.gz ]; then
	  echo "can not find firewall.tar.gz"
	  exit -1
	fi
	tar xzvf firewall.tar.gz -C secsmart_platform/AppPackages/
	
	# 7. scmpx
	if [ ! -f scmpx.tar.gz ]; then
	  echo "can not find scmpx.tar.gz"
	  exit -1
	fi
	tar xzvf scmpx.tar.gz -C secsmart_platform/AppPackages/
	
	# 8. sdm
	if [ ! -f sdm.tar.gz ]; then
	  echo "can not find sdm.tar.gz"
	  exit -1
	fi
	tar xzvf sdm.tar.gz -C secsmart_platform/AppPackages/
	
	# 9. tde
	if [ ! -f tde.tar.gz ]; then
	  echo "can not find tde.tar.gz"
	  exit -1
	fi
	tar xzvf tde.tar.gz -C secsmart_platform/AppPackages/
	
	# install
	cd secsmart_platform 
	./install.sh
	echo 
	echo "secsmart platform installed success"
}

function uninstall_all
{
	// just uninstall secsmart platform
	cd /data/all_in_one/secsmart_platform
	./uninstall.sh
	echo "secsmart uninstall success"
}

function usage
{
	echo "$0 [install | uninstall]"
	exit 0
}

if [ $# -ne 2 ]; then
	usage
fi

case $1 in
	install)
		case $2 in
			jdk)
				install_jdk
				;;
			mysql)
				install_mysql
				;;
			all_in_one)
				install_all_in_one
				;;
			*)
				usage
				;;
		esac
		;;
	uninstall)
		echo "Uninstall Secsmart Platform ..."
		uninstall_all
		;;
	*)
		usage
		;;
esac

```

将这个脚本按照上述方式，制作成 `install_secsmart_platform-1.0-1.x86_64.rpm` ，安装完成，安装脚本文件会被安装到 `/usr/local/bin` 目录中

## 安装脚本执行，在系统第一次登录时进行

上面的安装脚本，在系统第一次登录的时候，执行并进行安装，上面仅说明了 `all_in_one`，同时安装的还有的 mysql，方式跟 `all_in_one` 相同。在 `ks.cfg` 中，有一个参数配置 `%post` ，这个就是允许系统在安装结束时，可以执行的动作。

系统安装结束时，如果没有出错，就是执行 `%post` 处的动作，这个时候，iso 镜像是没有挂在的，访问不到里面的数据，而且脚本执行不完全是在 shell 环境下，不能直接调用我们自己编写的安装脚本，这里的解决方法是在 `/etc/profile` 中配置安装脚本的执行，第一次登录时，就会执行安装脚本，同时将该执行命令从 `/etc/profile` 中删除，后面不会再继续执行

```
%post --log=/root/ks-post-jdk.log
#!/bin/sh
/usr/local/bin/install_secsmart_platform.sh install jdk
echo "/usr/local/bin/install_secsmart_platform.sh install mysql >> /root/secsmart_install.log" >> /etc/profile
echo "/usr/local/bin/install_secsmart_platform.sh install all_in_one >> /root/secsmart_install.log" >> /etc/profile
%end
```

在上面的安装脚本中，比如在 `function install_all_in_one` 函数的定义中，第一句便是

```
sed -i '/install_secsmart_platform\.sh install all_in_one/d' /etc/profile
```

将安装脚本执行命令从 `/etc/profile` 中删除。

这样就完成了 ISO 一体化安装。

