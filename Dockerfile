FROM centos:7
MAINTAINER Christian Eichelmann "christian@crapworks.de"

ENV CEPH_VERSION mimic

# Install Ceph
RUN rpm --import 'https://download.ceph.com/keys/release.asc'
RUN rpm -Uvh http://download.ceph.com/rpm-${CEPH_VERSION}/el7/noarch/ceph-release-1-1.el7.noarch.rpm
RUN yum install -y epel-release && yum clean all
RUN yum install -y ceph python27 python-pip && yum clean all

COPY . /cephdash
WORKDIR /cephdash
RUN pip install -r requirements.txt

ENTRYPOINT ["/cephdash/contrib/docker/entrypoint.sh"]
CMD ["ceph-dash.py"]
