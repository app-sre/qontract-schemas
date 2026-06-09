import pytest
import os
from pathlib import Path
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

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
