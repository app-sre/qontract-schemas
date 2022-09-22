# qontract-schemas

A repository containing schemas required for app-interface and qontract-reconcile.

## Background

- Schema validation is based on [json-schema](http://json-schema.org/).
- The custom validation engine is located at [qcontract-validator](https://github.com/app-sre/qontract-validator).
- The schema data is located at [app-interface](https://gitlab.cee.redhat.com/service/app-interface)

## Local Development

To locally bundle and validate ONLY the schema you can run

```
make bundle-and-validate-schema
```

However, usually you want to validate a schema change against real existing data in app-interface.
During the development process it is encouraged to rely on test data in [app-sre/app-interface](https://github.com/app-sre/app-interface) instead.
See [qcontract-server](https://github.com/app-sre/qontract-server) on how to bundle schema and app-interface data.

## About the schemas definition

### Crossrefs

Sub schema definitions and validations are made with the `common-1.json/crossdef` json definition. This section explains some considerations of this approach along with practical examples.

**IMPORTANT:** A `crossref` is not a common json schema cross reference, it just defines a `string` to point to the sub-schema definition file.

#### common-1.json

```json
    "crossref": {
      "type": "object",
      "properties": {
        "$ref": {
          "type": "string",
          "format": "uri-reference"
        }
      },
      "required": [
        "$ref"
      ]
```

With this definition, a json validation will succeed if the `$ref` attribute of a crossref is a string with a uri-reference, but it won't validate that the schema of the destination file is the required one.
`Qontract-validator` is used to validate the schemas and data within app-interface. `crossrefs` schemas validation is implemented with a `$schemaRef` attribute that should be placed in
the attribute definition along with the crossref.
e,g:

```json
  aws_groups:
    type: array
    items:
      "$ref": "/common-1.json#/definitions/crossref"
      "$schemaRef": "/aws/group-1.yml"
```

With the `$schemaRef` attribute, qontract-validator is able to validate that the destination file matches the required schema. **IMPORTANT** `$schemaRef` can be a string pointing to a schema file
or a inline fragment of a json schema definition. If it's a string, `qontract-validator` validates the destination file `$schema` attribute has the correct schema. If it's a json schema snippet, it validates
the data with a json validator (Draft-06).

### Examples:

#### Multiple allowed schemas for a crossref

What if we want to define a crossref with multiple allowed types? (datafiles case in role-1#self_service)

```json
  datafiles:
    type: array
    items:
      "$ref": "/common-1.json#/definitions/crossref"
      "$schemaRef":
        type: object
        properties:
          '$schema':
            type: string
            enum:
              - "/app-sre/saas-file-2.yml"
              - "/openshift/namespace-1.yml"
```

```yaml
datafiles:
- $ref: /services/test-saas-deployment-pipelines/cicd/deploy.yml
- $ref: /services/test-saas-deployment-pipelines/namespaces/stage.yml
```

With this definition, `qontract-validator` will validate that the `$schema` attribute of every entry in the list is defined within the enum.
