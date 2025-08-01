FROM registry.access.redhat.com/ubi9/ubi-minimal:9.6-1754000177@sha256:0d7cfb0704f6d389942150a01a20cb182dc8ca872004ebf19010e2b622818926 as prod

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
