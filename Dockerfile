FROM registry.access.redhat.com/ubi9/ubi-minimal:9.6-1752587672@sha256:6d5a6576c83816edcc0da7ed62ba69df8f6ad3cbe659adde2891bfbec4dbf187 as prod

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
