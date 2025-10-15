FROM registry.access.redhat.com/ubi9/ubi-minimal:9.6-1760515502@sha256:34880b64c07f28f64d95737f82f891516de9a3b43583f39970f7bf8e4cfa48b7 AS prod

WORKDIR /schemas

COPY schemas schemas
COPY graphql-schemas graphql-schemas
COPY LICENSE /licenses/LICENSE

FROM prod AS test

RUN microdnf upgrade -y && \
    microdnf install -y python3.11 && \
    microdnf clean all && \
    update-alternatives --install /usr/bin/python3 python /usr/bin/python3.11 1 && \
    ln -snf /usr/bin/python3.11 /usr/bin/python && \
    python3 -m ensurepip

RUN python3 -m pip install --no-cache-dir --upgrade pip tox

COPY tox.ini test .yamllint /schemas/

CMD ["tox"]
