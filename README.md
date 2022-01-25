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
