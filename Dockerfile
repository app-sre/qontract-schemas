FROM registry.access.redhat.com/ubi9/ubi-minimal:9.7-1776833838@sha256:7d4e47500f28ac3a2bff06c25eff9127ff21048538ae03ce240d57cf756acd00 AS prod

WORKDIR /schemas

COPY schemas schemas
COPY graphql-schemas graphql-schemas
COPY LICENSE /licenses/LICENSE

FROM registry.access.redhat.com/ubi9/python-312-minimal:9.7-1776864092@sha256:48b9c3b0c438e5248dd43b325930a1f0b28b7ef201d2c2b78fbf9f8704a686bd AS test

WORKDIR /schemas

USER 0
RUN microdnf -y install make && microdnf -y clean all
USER 1001

COPY --from=ghcr.io/astral-sh/uv:0.9.26@sha256:9a23023be68b2ed09750ae636228e903a54a05ea56ed03a934d00fe9fbeded4b /uv /bin/uv

ENV \
    # use venv from ubi image
    UV_PROJECT_ENVIRONMENT="/opt/app-root" \
    # compile bytecode for faster startup
    UV_COMPILE_BYTECODE="true" \
    # disable uv cache. it doesn't make sense in a container
    UV_NO_CACHE=true

COPY pyproject.toml uv.lock ./

# Update qontract-validator package to latest commit
USER 0
RUN uv lock --upgrade-package qontract-validator
USER 1001
RUN uv lock --locked && \
    uv sync --frozen

COPY --from=prod /schemas /schemas

COPY test .yamllint Makefile ./
RUN make _test
