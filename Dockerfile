FROM registry.access.redhat.com/ubi9/ubi-minimal:9.5-1741850109@sha256:bafd57451de2daa71ed301b277d49bd120b474ed438367f087eac0b885a668dc as prod

WORKDIR /schemas

COPY schemas schemas
COPY graphql-schemas graphql-schemas
COPY LICENSE /licenses/LICENSE

FROM prod as test

RUN microdnf upgrade -y && \
    microdnf install -y \
        python3.11 && \
    microdnf clean all && \
    update-alternatives --install /usr/bin/python3 python /usr/bin/python3.11 1 && \
    ln -snf /usr/bin/python3.11 /usr/bin/python && \
    python3 -m ensurepip

RUN python3 -m pip install --no-cache-dir --upgrade pip tox

COPY tox.ini test /schemas/

CMD ["tox"]
