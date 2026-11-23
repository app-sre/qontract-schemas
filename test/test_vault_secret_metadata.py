import pytest
from jsonschema import Draft6Validator, RefResolver
from utils import get_schema_object_validator


def get_common_def_validator(schemas, definition_name: str) -> Draft6Validator:
    resolver = RefResolver("/common-1.json", schemas["/common-1.json"], store=schemas)
    return Draft6Validator(
        {"$ref": f"/common-1.json#/definitions/{definition_name}"},
        resolver=resolver,
    )


@pytest.mark.parametrize(
    "resource,expected_valid",
    [
        # Existing VaultSecret without metadata remains valid
        (
            {
                "provider": "vault-secret",
                "path": "osd-sre/configuration-anomaly-detection/pd/prod",
                "version": 13,
            },
            True,
        ),
        # Partial metadata override is valid
        (
            {
                "provider": "vault-secret",
                "path": "osd-sre/configuration-anomaly-detection/pd/prod",
                "version": 13,
                "metadata": {
                    "rotationRing": "outer",
                    "credentialType": "saas-token",
                },
            },
            True,
        ),
        # Full metadata block is valid
        (
            {
                "provider": "vault-secret",
                "path": "rosa-sre/apps/prod/route53-creds",
                "version": 4,
                "metadata": {
                    "owner": "rosa-sre",
                    "rotationRing": "outer",
                    "credentialType": "aws-iam-key",
                    "producer": "erv2",
                    "pickupMode": "qontract-recycle",
                },
            },
            True,
        ),
        # Invalid enum value is rejected
        (
            {
                "provider": "vault-secret",
                "path": "rosa-sre/apps/prod/route53-creds",
                "version": 4,
                "metadata": {
                    "rotationRing": "p1",
                },
            },
            False,
        ),
        # Unknown metadata key is rejected (additionalProperties: false)
        (
            {
                "provider": "vault-secret",
                "path": "rosa-sre/apps/prod/route53-creds",
                "version": 4,
                "metadata": {
                    "rotationRing": "outer",
                    "unexpectedKey": "value",
                },
            },
            False,
        ),
    ],
)
def test_openshift_resource_vault_secret_metadata(schemas, resource, expected_valid):
    validator = get_schema_object_validator(
        schemas, "/openshift/openshift-resource-vault-secret-1.yml"
    )
    assert validator.is_valid(resource) is expected_valid


@pytest.mark.parametrize(
    "secret_ref,expected_valid",
    [
        # Existing vaultSecret reference without metadata remains valid
        (
            {
                "path": "app-sre-v2/creds/gcp/gcr-push",
                "field": "token",
                "version": 2,
            },
            True,
        ),
        # Control-plane vaultSecret reference with metadata is valid
        (
            {
                "path": "app-sre-v2/creds/gcp/gcr-push",
                "field": "token",
                "version": 2,
                "metadata": {
                    "owner": "app-sre",
                    "rotationRing": "outer",
                    "credentialType": "gcp-sa",
                    "producer": "manual",
                },
            },
            True,
        ),
        # Invalid producer enum is rejected
        (
            {
                "path": "app-sre-v2/creds/gcp/gcr-push",
                "field": "token",
                "metadata": {
                    "producer": "unknown-system",
                },
            },
            False,
        ),
        # Extra unexpected key is rejected
        (
            {
                "path": "app-sre-v2/creds/gcp/gcr-push",
                "field": "token",
                "metadata": {
                    "extra": "nope",
                },
            },
            False,
        ),
    ],
)
def test_common_vault_secret_metadata(schemas, secret_ref, expected_valid):
    validator = get_common_def_validator(schemas, "vaultSecret")
    assert validator.is_valid(secret_ref) is expected_valid
