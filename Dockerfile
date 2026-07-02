FROM registry.access.redhat.com/ubi10/ubi-minimal:10.2-1782798957@sha256:b217fa65d8c21058887b18f005f587e47a17dd1281a5196ac88d01724a273dbd AS prod

WORKDIR /schemas

COPY schemas schemas
COPY graphql-schemas graphql-schemas
COPY LICENSE /licenses/LICENSE

FROM registry.access.redhat.com/ubi10/python-314-minimal:10.2-1782827458@sha256:92f2b9ef3d2fe255f5a2200f97bf4f14a95dc120bd19bcbc9f84a2f10e4af683 AS test

WORKDIR /schemas

USER 0
RUN microdnf -y install make && microdnf -y clean all
USER 1001

COPY --from=ghcr.io/astral-sh/uv:0.11.25@sha256:1e3808aa9023d0980e7c15b1fa7c1ac16ff35925780cf5c459858b2d693f01a9 /uv /bin/uv

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
