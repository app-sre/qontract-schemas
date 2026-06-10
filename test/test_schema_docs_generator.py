import pytest
import os
from pathlib import Path
import sys


def _scripts_dir() -> Path:
    """Resolve scripts/ for repo checkout and Docker test image layouts."""
    here = Path(__file__).resolve().parent
    for candidate in (here / "scripts", here.parent / "scripts"):
        if candidate.is_dir():
            return candidate
    raise RuntimeError("scripts directory not found")


sys.path.insert(0, str(_scripts_dir()))

from generate_schema_docs import scan_schemas_directory, parse_schema_file


def test_scan_schemas_directory_finds_yaml_files(tmp_path):
    # Create test schema files
    (tmp_path / "app-sre").mkdir()
    (tmp_path / "app-sre" / "app-1.yml").write_text("test")
    (tmp_path / "aws").mkdir()
    (tmp_path / "aws" / "account-1.yml").write_text("test")
    (tmp_path / "common-1.json").write_text("test")

    result = scan_schemas_directory(str(tmp_path))

    assert len(result) == 3
    assert "app-sre/app-1.yml" in result
    assert "aws/account-1.yml" in result
    assert "common-1.json" in result


def test_scan_schemas_directory_ignores_non_schema_files(tmp_path):
    (tmp_path / "README.md").write_text("test")
    (tmp_path / "test.py").write_text("test")
    (tmp_path / "app-sre").mkdir()
    (tmp_path / "app-sre" / "app-1.yml").write_text("test")

    result = scan_schemas_directory(str(tmp_path))

    assert len(result) == 1
    assert "app-sre/app-1.yml" in result


def test_parse_schema_file_yaml(tmp_path):
    schema_content = """---
$schema: /metaschema-1.json
version: "1.0"
type: object

properties:
  name:
    type: string
    description: Application name
  age:
    type: number
    minimum: 0
    maximum: 150
  status:
    type: string
    enum:
    - active
    - inactive
    default: active

required:
- name
- status
"""
    schema_file = tmp_path / "test-1.yml"
    schema_file.write_text(schema_content)

    result = parse_schema_file(str(schema_file), "test-1.yml")

    assert result["path"] == "test-1.yml"
    assert result["version"] == "1.0"
    assert result["description"] is None
    assert len(result["properties"]) == 3

    # Check name property
    name_prop = next(p for p in result["properties"] if p["name"] == "name")
    assert name_prop["type"] == "string"
    assert name_prop["required"] is True
    assert name_prop["description"] == "Application name"

    # Check age property
    age_prop = next(p for p in result["properties"] if p["name"] == "age")
    assert age_prop["type"] == "number"
    assert age_prop["required"] is False
    assert age_prop["constraints"]["minimum"] == 0
    assert age_prop["constraints"]["maximum"] == 150

    # Check status property (enum)
    status_prop = next(p for p in result["properties"] if p["name"] == "status")
    assert status_prop["type"] == "enum"
    assert status_prop["required"] is True
    assert status_prop["constraints"]["enum"] == ["active", "inactive"]
    assert status_prop["constraints"]["default"] == "active"


def test_parse_one_of_required_sets(tmp_path):
    schema_content = """---
$schema: /metaschema-1.json
version: "1.0"
type: object
properties:
  access:
    type: array
    items:
      properties:
        namespace:
          type: string
        role:
          type: string
        cluster:
          type: string
        group:
          type: string
      oneOf:
      - required:
        - namespace
        - role
      - required:
        - cluster
        - group
required:
- access
"""
    schema_file = tmp_path / "role-1.yml"
    schema_file.write_text(schema_content)

    result = parse_schema_file(str(schema_file), "role-1.yml")
    access = next(p for p in result["properties"] if p["name"] == "access")
    items_props = access["nestedProperties"]
    assert len(items_props) == 4

    one_of = access.get("oneOf")
    assert one_of is not None
    assert one_of["kind"] == "required_sets"
    assert len(one_of["branches"]) == 2
    labels = {b["label"] for b in one_of["branches"]}
    assert "namespace + role" in labels
    assert "cluster + group" in labels


def test_parse_property_nested_object_without_type(tmp_path):
    schema_content = """---
$schema: /metaschema-1.json
version: "1.0"
type: object
properties:
  access:
    type: array
    items:
      properties:
        namespace:
          type: string
        role:
          type: string
      required:
      - namespace
required:
- access
"""
    schema_file = tmp_path / "role-1.yml"
    schema_file.write_text(schema_content)

    result = parse_schema_file(str(schema_file), "role-1.yml")
    access_prop = next(p for p in result["properties"] if p["name"] == "access")

    assert access_prop["type"] == "array[object]"
    assert access_prop["nestedCount"] == 2
    assert {p["name"] for p in access_prop["nestedProperties"]} == {"namespace", "role"}
    assert access_prop["nestedProperties"][0]["propertyPath"] == ".access[].namespace"


def test_parse_property_nested_object_inferred_type(tmp_path):
    schema_content = """---
$schema: /metaschema-1.json
version: "1.0"
type: object
properties:
  source:
    properties:
      provider:
        type: string
      url:
        type: string
    required:
    - provider
required:
- source
"""
    schema_file = tmp_path / "membership-provider-1.yml"
    schema_file.write_text(schema_content)

    result = parse_schema_file(str(schema_file), "membership-provider-1.yml")
    source_prop = next(p for p in result["properties"] if p["name"] == "source")

    assert source_prop["type"] == "object"
    assert source_prop["nestedCount"] == 2
    assert source_prop["nestedProperties"][0]["propertyPath"] == ".source.provider"


def test_parse_schema_one_of_permission_style(tmp_path):
    schema_content = """---
$schema: /metaschema-1.json
version: "1.0"
type: object
properties:
  labels:
    type: object
  name:
    type: string
  description:
    type: string
  service:
    type: string
  org:
    type: string
  team:
    type: string
  quayOrg:
    type: string
  skip:
    type: boolean
oneOf:
- properties:
    service:
      enum:
      - github-org-team
    org:
      type: string
    team:
      type: string
  required:
  - org
  - team
- properties:
    service:
      enum:
      - quay-membership
    quayOrg:
      type: string
    team:
      type: string
  required:
  - quayOrg
  - team
required:
- name
"""
    schema_file = tmp_path / "permission-1.yml"
    schema_file.write_text(schema_content)

    result = parse_schema_file(str(schema_file), "permission-1.yml")

    assert "schemaOneOf" in result
    assert result["schemaOneOf"]["kind"] == "variants"
    assert len(result["schemaOneOf"]["branches"]) == 2

    prop_names = {p["name"] for p in result["properties"]}
    assert "org" not in prop_names
    assert "quayOrg" not in prop_names
    assert "name" in prop_names
    assert "skip" in prop_names


def test_parse_one_of_ref_alternatives(tmp_path):
    schema_content = """---
$schema: /metaschema-1.json
version: "1.0"
type: object
properties:
  quayRepos:
    type: array
    items:
      oneOf:
      - $ref: /app-sre/app-quay-repos-1.yml
      - $ref: /common-1.json#/definitions/crossref
        $schemaRef: /app-sre/app-quay-repos-1.yml
required:
- quayRepos
"""
    schema_file = tmp_path / "app-1.yml"
    schema_file.write_text(schema_content)

    result = parse_schema_file(str(schema_file), "app-1.yml")
    quay = next(p for p in result["properties"] if p["name"] == "quayRepos")

    assert quay["oneOf"]["kind"] == "ref_alternatives"
    assert len(quay["oneOf"]["branches"]) == 2
    schema_refs = {b.get("schemaRef") for b in quay["oneOf"]["branches"]}
    assert "/app-sre/app-quay-repos-1.yml" in schema_refs


def test_parse_property_deeply_nested_paths(tmp_path):
    schema_content = """---
$schema: /metaschema-1.json
version: "1.0"
type: object
properties:
  codeComponents:
    type: array
    items:
      type: object
      properties:
        gitlabSync:
          type: object
          properties:
            sourceProject:
              type: object
              properties:
                name:
                  type: string
required:
- codeComponents
"""
    schema_file = tmp_path / "app-1.yml"
    schema_file.write_text(schema_content)

    result = parse_schema_file(str(schema_file), "app-1.yml")
    code_components = next(p for p in result["properties"] if p["name"] == "codeComponents")
    gitlab_sync = next(p for p in code_components["nestedProperties"] if p["name"] == "gitlabSync")
    source_project = next(p for p in gitlab_sync["nestedProperties"] if p["name"] == "sourceProject")
    name_prop = next(p for p in source_project["nestedProperties"] if p["name"] == "name")

    assert name_prop["propertyPath"] == ".codeComponents[].gitlabSync.sourceProject.name"


def test_parse_schema_file_json(tmp_path):
    schema_content = """{
  "$schema": "/metaschema-1.json",
  "version": "1.0",
  "type": "object",
  "properties": {
    "identifier": {
      "type": "string",
      "pattern": "^[a-z0-9-]+$"
    }
  },
  "required": ["identifier"]
}"""
    schema_file = tmp_path / "test-1.json"
    schema_file.write_text(schema_content)

    result = parse_schema_file(str(schema_file), "test-1.json")

    assert result["path"] == "test-1.json"
    assert len(result["properties"]) == 1

    id_prop = result["properties"][0]
    assert id_prop["name"] == "identifier"
    assert id_prop["type"] == "string"
    assert id_prop["required"] is True
    assert id_prop["constraints"]["pattern"] == "^[a-z0-9-]+$"


def test_extract_dependencies_simple_ref():
    from generate_schema_docs import extract_dependencies

    schema_data = {
        "properties": {
            "product": {
                "type": "object",
                "$schemaRef": "/app-sre/product-1.yml"
            }
        }
    }

    result = extract_dependencies(schema_data, "test-1.yml")

    assert len(result) == 1
    assert result[0]["propertyPath"] == ".product"
    assert result[0]["targetSchema"] == "app-sre/product-1.yml"
    assert result[0]["isArray"] is False
    assert result[0]["isNested"] is False


def test_extract_dependencies_array_ref():
    from generate_schema_docs import extract_dependencies

    schema_data = {
        "properties": {
            "dependencies": {
                "type": "array",
                "items": {
                    "$schemaRef": "/dependencies/dependency-1.yml"
                }
            }
        }
    }

    result = extract_dependencies(schema_data, "test-1.yml")

    assert len(result) == 1
    assert result[0]["propertyPath"] == ".dependencies[]"
    assert result[0]["targetSchema"] == "dependencies/dependency-1.yml"
    assert result[0]["isArray"] is True
    assert result[0]["isNested"] is False


def test_extract_dependencies_nested_ref():
    from generate_schema_docs import extract_dependencies

    schema_data = {
        "properties": {
            "codeComponents": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "gitlabHousekeeping": {
                            "type": "object",
                            "properties": {
                                "labels_allowed": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "role": {
                                                "$schemaRef": "/access/role-1.yml"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    result = extract_dependencies(schema_data, "test-1.yml")

    assert len(result) == 1
    assert result[0]["propertyPath"] == ".codeComponents[].gitlabHousekeeping.labels_allowed[].role"
    assert result[0]["targetSchema"] == "access/role-1.yml"
    assert result[0]["isArray"] is True
    assert result[0]["isNested"] is True


def test_build_categories():
    from generate_schema_docs import build_categories

    schemas = {
        "app-sre/app-1.yml": {"path": "app-sre/app-1.yml"},
        "app-sre/product-1.yml": {"path": "app-sre/product-1.yml"},
        "aws/account-1.yml": {"path": "aws/account-1.yml"},
        "common-1.json": {"path": "common-1.json"},
    }

    result = build_categories(schemas)

    assert len(result) == 3

    # Check app-sre category
    app_sre = next(c for c in result if c["name"] == "app-sre")
    assert len(app_sre["schemas"]) == 2
    assert "app-1.yml" in app_sre["schemas"]
    assert "product-1.yml" in app_sre["schemas"]

    # Check aws category
    aws = next(c for c in result if c["name"] == "aws")
    assert len(aws["schemas"]) == 1
    assert "account-1.yml" in aws["schemas"]

    # Check root category (common-1.json)
    root = next(c for c in result if c["name"] == ".")
    assert len(root["schemas"]) == 1
    assert "common-1.json" in root["schemas"]


def test_build_reverse_dependencies():
    from generate_schema_docs import build_reverse_dependencies

    schemas = {
        "app-sre/app-1.yml": {
            "dependencies": [
                {"targetSchema": "app-sre/product-1.yml", "propertyPath": ".product"},
                {"targetSchema": "app-sre/escalation-policy-1.yml", "propertyPath": ".escalationPolicy"}
            ]
        },
        "app-sre/product-1.yml": {
            "dependencies": []
        },
        "app-sre/escalation-policy-1.yml": {
            "dependencies": []
        }
    }

    result = build_reverse_dependencies(schemas)

    # product-1.yml should be referenced by app-1.yml
    assert "app-sre/product-1.yml" in result
    assert len(result["app-sre/product-1.yml"]) == 1
    assert result["app-sre/product-1.yml"][0]["schema"] == "app-sre/app-1.yml"
    assert result["app-sre/product-1.yml"][0]["propertyPath"] == ".product"

    # escalation-policy-1.yml should be referenced by app-1.yml
    assert "app-sre/escalation-policy-1.yml" in result
    assert len(result["app-sre/escalation-policy-1.yml"]) == 1
    assert result["app-sre/escalation-policy-1.yml"][0]["schema"] == "app-sre/app-1.yml"

    # app-1.yml should have no reverse dependencies
    assert "app-sre/app-1.yml" not in result


def test_generate_schema_docs_integration(tmp_path):
    import json
    from generate_schema_docs import generate_schema_docs

    # Create test schemas directory
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()

    # Create app-sre category
    (schemas_dir / "app-sre").mkdir()
    (schemas_dir / "app-sre" / "app-1.yml").write_text("""---
$schema: /metaschema-1.json
version: "1.0"
type: object
properties:
  name:
    type: string
    description: App name
  product:
    $schemaRef: /app-sre/product-1.yml
required:
- name
""")

    (schemas_dir / "app-sre" / "product-1.yml").write_text("""---
$schema: /metaschema-1.json
version: "1.0"
type: object
properties:
  name:
    type: string
required:
- name
""")

    # Create output directory
    output_dir = tmp_path / "docs"
    output_dir.mkdir()

    # Run generator
    generate_schema_docs(str(schemas_dir), str(output_dir))

    # Verify schemas.json was created
    assert (output_dir / "schemas.json").exists()

    # Load and validate output
    with open(output_dir / "schemas.json") as f:
        data = json.load(f)

    # Check categories
    assert "categories" in data
    assert len(data["categories"]) == 1
    assert data["categories"][0]["name"] == "app-sre"
    assert len(data["categories"][0]["schemas"]) == 2

    # Check schemas
    assert "schemas" in data
    assert "app-sre/app-1.yml" in data["schemas"]
    assert "app-sre/product-1.yml" in data["schemas"]

    # Check dependencies
    app_schema = data["schemas"]["app-sre/app-1.yml"]
    assert len(app_schema["dependencies"]) == 1
    assert app_schema["dependencies"][0]["targetSchema"] == "app-sre/product-1.yml"

    # Check reverse dependencies
    product_schema = data["schemas"]["app-sre/product-1.yml"]
    assert len(product_schema["referencedBy"]) == 1
    assert product_schema["referencedBy"][0]["schema"] == "app-sre/app-1.yml"
