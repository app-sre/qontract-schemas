FROM registry.access.redhat.com/ubi8/ubi-minimal:8.10

WORKDIR /schemas

COPY schemas schemas
COPY graphql-schemas graphql-schemas
