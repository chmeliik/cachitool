FROM quay.io/centos/centos:stream8

# builddeps
RUN dnf -y install \
        git \
        make \
        gcc-c++ \
        libpq-devel \
        libffi-devel \
        openssl-devel \
        libjpeg-devel \
        openldap-devel \
        postgresql-devel

# python
RUN dnf -y install python39 python39-devel python39-pip \
    && dnf clean all

COPY quay/ /opt/quay
WORKDIR /opt/quay

ARG PIP_INDEX_URL

RUN python3.9 -m pip install --upgrade setuptools pip && \
    python3.9 -m pip install wheel && \
    python3.9 -m pip install -r requirements.txt && \
    python3.9 -m pip freeze
