FROM registry.access.redhat.com/ubi10/ubi-minimal:10.2-1781509346@sha256:76c113359a458e3f04057762b5bd4a9837a6987520434dea158c728280116713 AS prod

WORKDIR /schemas

COPY schemas schemas
COPY graphql-schemas graphql-schemas
COPY LICENSE /licenses/LICENSE

FROM registry.access.redhat.com/ubi10/python-314-minimal:10.2-1781585736@sha256:90d72f9275f8f4e7869c42b9a1e25d5cf458c970e15dd3ed072f38a7f07dabd6 AS test

WORKDIR /schemas

USER 0
RUN microdnf -y install make && microdnf -y clean all
USER 1001

COPY --from=ghcr.io/astral-sh/uv:0.11.23@sha256:d0a0a753ab981624b49c97abc98821c1c09f4ca69d1ef5cee69c501be3d88479 /uv /bin/uv

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
