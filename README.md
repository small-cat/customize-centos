# customize-centos
customize your centos operating system. cut off the rpms you don't want and pre install packages you need.

`rpm_specs` 目录里面的文件，用于制作对应的 `rpm` 包。将源代码或者 shell 脚本放在 `rpmbuild/SOURCES` 目录下，根据对应的版本号，打包成 `tar.gz` 文件，然后在 `rpmbuild/SPECS` 目录下，执行 `rpmbuild -ba XXXX.spec`，生成的 rpm 文件在 `rpmbuild/RPMS/` 目录下，使用 `rpm -i XXXX.rpm` 即可安装

`download` 目录，用于下载所需要的 rpm 包及其依赖，将这些 rpm 包全部放到 `ISO/Packages` 目录中，同时，在 `ISO/repodata/comps.xml` 文件中，添加这些新增的包名，比如

```
<packagereq type="mandatory">vim</packagereq>
```

这样，就将 vim 这个 rpm 的名称加入到了 ISO 镜像中，然后使用 `generate_iso.sh` 制作 ISO 镜像。
