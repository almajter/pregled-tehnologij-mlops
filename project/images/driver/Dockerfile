FROM nvcr.io/nvidia/driver@sha256:52b984c00817b08dcf5a0ed50dbba7b9f4d779614bde486a3483a4fb61dea3e5
ARG KOJI=https://kojihub.stream.centos.org/kojifiles/packages/kernel/6.12.0/254.el10/x86_64
RUN for p in kernel kernel-core kernel-modules kernel-modules-core kernel-devel kernel-headers; do \
      curl -fLO --retry 5 $KOJI/$p-6.12.0-254.el10.x86_64.rpm || exit 1; \
    done \
 && dnf install -y --repofrompath=c10s-baseos,https://mirror.stream.centos.org/10-stream/BaseOS/x86_64/os/ \
      --repofrompath=c10s-appstream,https://mirror.stream.centos.org/10-stream/AppStream/x86_64/os/ \
      --setopt=c10s-baseos.gpgcheck=0 --setopt=c10s-appstream.gpgcheck=0 \
      --setopt=install_weak_deps=False \
      createrepo_c ./kernel-*.rpm \
 && rpm -e --nodeps --noscripts kernel kernel-core kernel-modules kernel-modules-core \
 && mkdir /opt/kernel && mv kernel-*.rpm /opt/kernel && createrepo_c /opt/kernel \
 && printf '[kernel]\nname=kernel\nbaseurl=file:///opt/kernel\ngpgcheck=0\n' > /etc/yum.repos.d/kernel.repo \
 && dnf clean all
