FROM registry.access.redhat.com/ubi10/ubi-minimal:10.2-1788940913@sha256:26dc3089ab24491c1ba01ab92a7d502d181425b6021e362a07484daee696a3aa AS prod

WORKDIR /schemas

COPY schemas schemas
COPY graphql-schemas graphql-schemas
COPY LICENSE /licenses/LICENSE

FROM registry.access.redhat.com/ubi10/python-314-minimal:10.2-1789015071@sha256:1f0d7848ed6c8f9e051ff14675ffcc8c98eaf2a66fc7a473d20ba8a4efefc408 AS test

WORKDIR /schemas

USER 0
RUN microdnf -y install make && microdnf -y clean all
USER 1001

COPY --from=ghcr.io/astral-sh/uv:0.12.10@sha256:2bb3ebca0a796a155094a27773d290c4b074572e6107f171d88d086682fd2500 /uv /bin/uv

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
