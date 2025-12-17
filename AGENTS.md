# AGENTS.md

This file provides guidance to AI agents when working with code in this repository.

## About This Repository

This repository contains two different types of schemas:

1. **schemas/** - JSON schemas for app-interface data validation. Schema validation is based on json-schema, with a custom validation engine at qcontract-validator. The schema data is located at app-interface.

2. **graphql-schemas/** - GraphQL schemas consumed by qontract-server for qontract-reconcile and other clients of qontract-server.

## Development Commands

### Schema Validation
- `make bundle-and-validate-schema` - Bundle and validate schemas locally (most common during development)
- `make bundle` - Use qontract-validator image to bundle schemas into data.json
- `make validate` - Validate schemas in bundled data.json file
- `make gql_validate` - Run qontract-server to reveal GraphQL schema issues

### Testing
- `make test` - Run all tests (pytest + yamllint)
- `uv run pytest -v` - Run just the tests
- `uv run yamllint .` - Run only linting (yamllint)

### Docker Operations
- `make test` - Build test image
- `make clean` - Clean up build artifacts

## Architecture Overview

### Schema Structure

#### JSON Schemas (schemas/)
Contains all JSON schema definitions for app-interface data validation, organized by domain:
- `access/` - User, role, permission schemas
- `app-sre/` - App-SRE specific schemas
- `aws/`, `gcp/` - Cloud provider schemas
- `openshift/` - OpenShift/Kubernetes schemas
- `dependencies/` - Dependency management schemas
- `vault-config/` - Vault configuration schemas
- **common-1.json** - Common schema definitions and patterns used across all schemas
- **metaschema-1.json** - Defines the structure requirements for qontract-schemas

#### GraphQL Schemas (graphql-schemas/)
Contains GraphQL schema definitions consumed by qontract-server for qontract-reconcile and other clients of qontract-server

### Key Schema Concepts

#### Crossrefs
Crossrefs use `$ref` for string references to other schema files and `$schemaRef` for validation:
```json
{
  "$ref": "/common-1.json#/definitions/crossref",
  "$schemaRef": "/aws/group-1.yml"
}
```

#### Common Patterns
- All schemas must reference `/metaschema-1.json`
- Use `common-1.json` definitions for identifiers, labels, annotations
- Schema files are preferably written in YAML format (`.yml`), though JSON (`.json`) is also accepted
- Required properties always include `$schema` and `labels`
- Properties should always have a description

### Validation Flow
1. qontract-validator uses schemas from this repo to validate against json-schema spec and custom crossref rules and creates a JSON bundle file.
2. qontract-server serves bundle file via GraphQL.

## File Conventions
- Schema files: Preferably YAML (`.yml`), though JSON (`.json`) is also accepted
- All YAML files must pass yamllint validation (see `.yamllint` config)
- Python test files follow pytest conventions
- Docker multi-stage build: `prod` target for schemas, `test` target includes Python testing environment
