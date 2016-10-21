%{!?scl_name_base:%global scl_name_base rh-thermostat}
%{!?scl_name_version:%global scl_name_version 16}

%{!?scl:%global scl %{scl_name_base}%{scl_name_version}}
%scl_package %scl

%if 0%{?rhel}

%if 0%{?rhel} <= 6
  # EL 6
  %global custom_release 60
%else
  # EL 7
  %global custom_release 70
%endif

%else

%global custom_release 1

%endif

# do not produce empty debuginfo package
%global debug_package %{nil}

Name:       %{scl_name}
Version:    2.3
# Release should be higher than el6 builds. Use convention
# 60.X where X is an increasing int. 60 for EL-6. We use
# 70.X for EL-7. For some reason we cannot rely on the
# dist tag.
Release:    %{custom_release}.5%{?dist}
Summary:    Package that installs %{scl}

License:    GPLv2+
Source0:    README
Source1:    LICENSE

# Required for java macro expansion
BuildRequires:    rh-java-common-javapackages-tools
BuildRequires:    rh-mongodb32-scldevel
BuildRequires:    rh-java-common-scldevel-common
BuildRequires:    rh-maven33-scldevel
BuildRequires:    help2man

# This needs to require all packages shipped with the
# collection. The leaf package is thermostat-webapp
# which should pull in thermostat plus all deps, such
# as mongo-java-driver and mongodb from the mongodb collection.
Requires:         %{name}-thermostat-webapp
Requires:         %{name}-runtime >= %{version}-%{release}

%description
This is the main package for the %{scl} Software Collection.

%package runtime
Summary:    Package that handles %{scl} Software Collection.
# Thermostat depends on the mongodb collection
%{?scl_mongodb:
Requires:   %{scl_mongodb}}
%{!?scl_mongodb:
Requires:   mongodb
Requires:   mongodb-server}
%{?scl_java_common:
Requires:   %{?scl_prefix_java_common}runtime}

%description runtime
Package shipping essential scripts to work with the %{scl} Software Collection.

%package build
Requires:   %{name}-scldevel = %{version}-%{release}
Summary:    Build support tools for the %{scl} Software Collection.

%description build
Package shipping essential configuration marcros/files in order to be able
to build %{scl} Software Collection.

%package scldevel
Summary:    Package shipping development files for %{scl}.
Group:      Applications/File
Requires:   %{?scl_prefix_java_common}javapackages-tools
Requires:   %{name}-runtime = %{version}-%{release}
Requires:   %{?scl_prefix_java_common}scldevel-common
Requires:   %{?scl_prefix_mongodb}scldevel
Requires:   %{?scl_prefix_maven}scldevel

%description scldevel
Development files for %{scl} (useful e.g. for hierarchical collection
building with transitive dependencies).

%prep
%setup -c -T
#===================#
# SCL enable script #
#===================#
cat <<EOF >enable
# The thermostat1 collection depends on the mongodb collection
# for the mongo-java-driver and on the rh-java-commmon collection
# for shared dependencies. We need to source the enable script
# in order for xmvn builds to work.
. scl_source enable %{?scl_mongodb} %{?scl_java_common}

# Generic variables
export PATH="%{_bindir}:\${PATH:-/bin:/usr/bin}"
export MANPATH="%{_mandir}:\${MANPATH}"

# Needed by Java Packages Tools to locate java.conf
export JAVACONFDIRS="%{_sysconfdir}/java:\${JAVACONFDIRS:-/etc/java}"

# Required by XMvn to locate its configuration file(s)
export XDG_CONFIG_DIRS="%{_sysconfdir}/xdg:\${XDG_CONFIG_DIRS:-/etc/xdg}"

# Not really needed by anything for now, but kept for consistency with
# XDG_CONFIG_DIRS.
export XDG_DATA_DIRS="%{_datadir}:\${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
EOF

#===========#
# java.conf #
#===========#
cat <<EOF >java.conf
# Java configuration file for %{scl} software collection.
JAVA_LIBDIR=%{_javadir}
JNI_LIBDIR=%{_jnidir}
JVM_ROOT=%{_jvmdir}
EOF

#=============#
# XMvn config #
#=============#
cat <<EOF >configuration.xml
<!-- XMvn configuration file for %{scl} software collection -->
<configuration>
  <resolverSettings>
    <metadataRepositories>
      <repository>/opt/rh/%{scl}/root/usr/share/maven-metadata</repository>
    </metadataRepositories>
    <prefixes>
      <prefix>/opt/rh/%{scl}/root</prefix>
    </prefixes>
  </resolverSettings>
  <installerSettings>
    <metadataDir>opt/rh/%{scl}/root/usr/share/maven-metadata</metadataDir>
  </installerSettings>
  <repositories>
    <repository>
      <id>resolve-%{scl}</id>
      <type>compound</type>
      <properties>
        <prefix>opt/rh/%{scl}/root</prefix>
        <namespace>%{scl}</namespace>
      </properties>
      <configuration>
        <repositories>
          <repository>base-resolve</repository>
        </repositories>
      </configuration>
    </repository>
    <repository>
      <id>resolve</id>
      <type>compound</type>
      <configuration>
        <repositories>
        <!-- The %{scl} collection resolves from:
                    1. local repository
                    2. %{scl}
                    3. java-common
                    4. mongodb
                    5. maven
               collections. -->
          <repository>resolve-local</repository>
          <repository>resolve-%{scl}</repository>
          <repository>resolve-java-common</repository>
          <repository>resolve-%{scl_mongodb}</repository>
          <repository>resolve-%{scl_maven}</repository>
        </repositories>
      </configuration>
    </repository>
    <repository>
      <id>install</id>
      <type>compound</type>
      <properties>
        <prefix>opt/rh/%{scl}/root</prefix>
        <namespace>%{scl}</namespace>
      </properties>
      <configuration>
        <repositories>
          <repository>base-install</repository>
        </repositories>
      </configuration>
    </repository>
  </repositories>
</configuration>
EOF

#=====================#
# Javapackages config #
#=====================#
cat <<EOF >javapackages-config.json
{
    "maven.req": {
	"always_generate": [
	    "%{scl}-runtime"
	],
	"java_requires": {
	    "package_name": "java",
	    "always_generate": true,
	    "skip": false
	},
	"java_devel_requires": {
	    "package_name": "java-devel",
	    "always_generate": false,
	    "skip": false
	}
    },
    "javadoc.req": {
	"always_generate": [
	    "%{scl}-runtime"
	]
    }
}
EOF


#=====================#
# README and man page #
#=====================#
# This section generates README file from a template and creates man page
# from that file, expanding RPM macros in the template file.
cat >README <<'EOF'
%{expand:%(cat %{SOURCE0})}
EOF

# copy the license file so %%files section sees it
cp %{SOURCE1} .

# scldevel macros
cat << EOF > macros.%{scl_name_base}-scldevel
%%scl_rh_thermostat %{scl}
%%scl_prefix_rh_thermostat %{scl_prefix}
EOF


%build
# generate a helper script that will be used by help2man
cat >h2m_helper <<'EOF'
#!/bin/bash
[ "$1" == "--version" ] && echo "%{scl_name} %{version} Software Collection" || cat README
EOF
chmod a+x h2m_helper

# generate the man page
help2man -N --section 7 ./h2m_helper -o %{scl_name}.7


%install
(%scl_install)

install -d -m 755 %{buildroot}%{_scl_scripts}
install -p -m 755 enable %{buildroot}%{_scl_scripts}/

install -d -m 755 %{buildroot}%{_sysconfdir}/java
install -p -m 644 java.conf %{buildroot}%{_sysconfdir}/java/
install -p -m 644 javapackages-config.json %{buildroot}%{_sysconfdir}/java/

install -d -m 755 %{buildroot}%{_sysconfdir}/xdg/xmvn
install -p -m 644 configuration.xml %{buildroot}%{_sysconfdir}/xdg/xmvn/


# Create java/maven/icons directories so that they'll get properly owned.
mkdir -p %{buildroot}%{_javadir}
mkdir -p %{buildroot}%{_jnidir}
mkdir -p %{buildroot}%{_javadocdir}
mkdir -p %{buildroot}%{_mavenpomdir}
mkdir -p %{buildroot}%{_datadir}/maven-effective-poms
mkdir -p %{buildroot}%{_datadir}/maven-metadata
mkdir -p %{buildroot}%{_mavendepmapfragdir}
mkdir -p %{buildroot}%{_datadir}/licenses
mkdir -p %{buildroot}%{_libdir}
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/scalable/apps

# install generated man page
mkdir -p %{buildroot}%{_mandir}/man7/
install -m 644 %{scl_name}.7 %{buildroot}%{_mandir}/man7/%{scl_name}.7

# scldevel macro
install -p -m 644 macros.%{scl_name_base}-scldevel %{buildroot}%{_root_sysconfdir}/rpm/

# Empty package (no file content).  The sole purpose of this package
# is collecting its dependencies so that the whole SCL can be
# installed by installing %{name}.
%files

%files runtime
%{scl_files}
%doc README
%doc LICENSE
%dir %{_sysconfdir}/java
%dir %{_javadir}
%dir %{_jnidir}
%dir %{_javadocdir}
%dir %{_mavenpomdir}
%dir %{_datadir}/maven-effective-poms
%dir %{_datadir}/maven-metadata
%dir %{_mavendepmapfragdir}
%dir %{_datadir}/licenses
%dir %{_libdir}
%{_sysconfdir}/java/java.conf
%{_sysconfdir}/java/javapackages-config.json
%{_sysconfdir}/xdg/xmvn/configuration.xml
%{_mandir}/man7/%{scl_name}.*

%files build
%{_root_sysconfdir}/rpm/macros.%{scl}-config

%files scldevel
%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel


%changelog
* Fri Jun 24 2016 Severin Gehwolf <sgehwolf@redhat.com> - 2.3-5
- Also done runtime require rh-java-common-scldevel, but
  rather rh-java-common-scldevel-common.

* Thu Jun 23 2016 Severin Gehwolf <sgehwolf@redhat.com> - 2.3-4
- Don't require rh-java-common-scldevel, but
  rh-java-common-scldevel-common which does not drag in
  maven30.

* Thu Jun 23 2016 Severin Gehwolf <sgehwolf@redhat.com> - 2.3-3
- Really fix the scldevel macros.

* Thu Jun 23 2016 Severin Gehwolf <sgehwolf@redhat.com> - 2.3-2
- Fix scldevel macro.

* Tue Jun 21 2016 Severin Gehwolf <sgehwolf@redhat.com> - 2.3-1
- Initial package
