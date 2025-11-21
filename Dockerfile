FROM registry.access.redhat.com/ubi9/ubi-minimal:9.7-1763362218@sha256:61d5ad475048c2e655cd46d0a55dfeaec182cc3faa6348cb85989a7c9e196483 AS prod

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
