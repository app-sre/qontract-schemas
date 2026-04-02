FROM registry.access.redhat.com/ubi9/ubi-minimal:9.7-1773939694@sha256:83006d535923fcf1345067873524a3980316f51794f01d8655be55d6e9387183 AS prod

WORKDIR /schemas

COPY schemas schemas
COPY graphql-schemas graphql-schemas
COPY LICENSE /licenses/LICENSE

FROM registry.access.redhat.com/ubi9/python-312-minimal:9.7-1775009368@sha256:3493394baa7957cc203c13f22ef1af7f7a59c132196f042f57fde30a9658356c AS test

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
