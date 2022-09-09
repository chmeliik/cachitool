FROM quay.io/centos/centos:stream8

# builddeps
RUN dnf -y install \
        gcc \
        make \
        krb5-devel \
        cairo-devel \
        cairo-gobject-devel \
        gobject-introspection-devel \
        libffi-devel \
        openssl-devel \
        popt-devel

# python3.8
RUN dnf -y install python38 python38-pip python38-devel \
    && dnf clean all

COPY atomic-reactor/ /opt/atomic-reactor
WORKDIR /opt/atomic-reactor

ARG PIP_INDEX_URL

# can't build cryptography with rust
RUN export CRYPTOGRAPHY_DONT_BUILD_RUST=1 \
    && python3.8 -m pip install -U pip \
    && python3.8 -m pip install -r requirements-build.txt \
    && python3.8 -m pip install -r requirements.txt --no-build-isolation \
    && python3.8 setup.py install

CMD ["python3.8", "-m", "atomic_reactor.cli.main", "--help"]
