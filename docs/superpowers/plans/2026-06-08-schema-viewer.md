# Schema Visualization Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a static web-based schema visualization tool with Python generator and vanilla JavaScript viewer

**Architecture:** Python script parses all schemas into a single JSON bundle. Static HTML/CSS/JS single-page app loads the JSON and renders an interactive viewer with sidebar navigation, properties table, and dependency tree.

**Tech Stack:** Python 3.14 (anymarkup, PyYAML, jsonschema), Vanilla JavaScript (ES6+), HTML5, CSS3, GitHub Pages

---

## File Structure

**New files to create:**
- `scripts/generate_schema_docs.py` - Main generator script
- `scripts/templates/index.html` - Static HTML viewer template
- `scripts/templates/styles.css` - Viewer CSS styles  
- `test/test_schema_docs_generator.py` - Generator unit tests
- `.github/workflows/deploy-docs.yml` - CI/CD workflow

**Files to modify:**
- `Makefile` - Add `generate-docs` target

**Generated output** (created by script, not manually):
- `docs/schemas.json` - All parsed schema data
- `docs/index.html` - Copied from template
- `docs/styles.css` - Copied from template

---

## Task 1: Python Generator Core - Schema Scanner and Parser

**Files:**
- Create: `scripts/generate_schema_docs.py`
- Test: `test/test_schema_docs_generator.py`

- [ ] **Step 1: Write failing test for schema scanner**

Create `test/test_schema_docs_generator.py`:

```python
import pytest
import os
from pathlib import Path
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_schema_docs import scan_schemas_directory


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest test/test_schema_docs_generator.py::test_scan_schemas_directory_finds_yaml_files -v`

Expected: `ModuleNotFoundError: No module named 'generate_schema_docs'`

- [ ] **Step 3: Create script with schema scanner implementation**

Create `scripts/generate_schema_docs.py`:

```python
#!/usr/bin/env python3
"""Generate static documentation site from qontract schemas."""

import os
from pathlib import Path
from typing import List


def scan_schemas_directory(base_dir: str) -> List[str]:
    """
    Recursively scan directory for schema files (.yml, .json).
    
    Returns:
        List of schema file paths relative to base_dir
    """
    schema_files = []
    base_path = Path(base_dir)
    
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(('.yml', '.json')):
                full_path = Path(root) / file
                relative_path = full_path.relative_to(base_path)
                schema_files.append(str(relative_path))
    
    return sorted(schema_files)


if __name__ == "__main__":
    # Entry point for CLI execution
    pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest test/test_schema_docs_generator.py::test_scan_schemas_directory_finds_yaml_files -v`

Expected: PASS

Run: `uv run pytest test/test_schema_docs_generator.py::test_scan_schemas_directory_ignores_non_schema_files -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_schema_docs.py test/test_schema_docs_generator.py
git commit -m "feat: add schema file scanner

- Recursively scan schemas/ directory for .yml and .json files
- Return sorted list of relative paths
- Ignore non-schema files

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Python Generator - Schema Parser

**Files:**
- Modify: `scripts/generate_schema_docs.py`
- Modify: `test/test_schema_docs_generator.py`

- [ ] **Step 1: Write failing test for schema parser**

Add to `test/test_schema_docs_generator.py`:

```python
from generate_schema_docs import parse_schema_file


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest test/test_schema_docs_generator.py::test_parse_schema_file_yaml -v`

Expected: `AttributeError: module 'generate_schema_docs' has no attribute 'parse_schema_file'`

- [ ] **Step 3: Implement schema parser**

Add to `scripts/generate_schema_docs.py`:

```python
import anymarkup
from typing import Dict, List, Any, Optional


def parse_schema_file(file_path: str, relative_path: str) -> Dict[str, Any]:
    """
    Parse a schema file (YAML or JSON) and extract structured data.
    
    Args:
        file_path: Absolute path to schema file
        relative_path: Relative path for display/lookup
        
    Returns:
        Normalized schema dict with properties, constraints, etc.
    """
    try:
        schema = anymarkup.parse_file(file_path)
    except Exception as e:
        print(f"Warning: Failed to parse {relative_path}: {e}")
        return None
    
    # Extract basic metadata
    version = schema.get("version", "unknown")
    description = schema.get("description")
    required_fields = schema.get("required", [])
    
    # Parse properties
    properties = []
    schema_properties = schema.get("properties", {})
    
    for prop_name, prop_def in schema_properties.items():
        properties.append(_parse_property(prop_name, prop_def, required_fields))
    
    return {
        "path": relative_path,
        "version": version,
        "description": description,
        "properties": properties,
        "dependencies": [],  # Populated later
        "referencedBy": []   # Populated later
    }


def _parse_property(name: str, definition: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """Parse a single property definition."""
    prop_type = definition.get("type", "unknown")
    
    # Detect enum type
    if "enum" in definition:
        prop_type = "enum"
    
    # Detect reference type
    if "$schemaRef" in definition:
        prop_type = "object (ref)"
    
    # Extract constraints
    constraints = {}
    constraint_fields = [
        "pattern", "format", "minimum", "maximum", "minLength", "maxLength",
        "default", "enum", "minItems", "maxItems"
    ]
    for field in constraint_fields:
        if field in definition:
            constraints[field] = definition[field]
    
    # Track $ref if present
    if "$ref" in definition:
        constraints["ref"] = definition["$ref"]
    
    return {
        "name": name,
        "type": prop_type,
        "required": name in required_fields,
        "description": definition.get("description"),
        "constraints": constraints if constraints else {},
        "schemaRef": definition.get("$schemaRef"),
        "propertyPath": f".{name}"
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest test/test_schema_docs_generator.py::test_parse_schema_file_yaml -v`

Expected: PASS

Run: `uv run pytest test/test_schema_docs_generator.py::test_parse_schema_file_json -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_schema_docs.py test/test_schema_docs_generator.py
git commit -m "feat: add schema file parser

- Parse YAML and JSON schema files using anymarkup
- Extract properties with types, descriptions, constraints
- Detect enums, references, and required fields
- Handle missing fields gracefully

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Python Generator - Dependency Extraction

**Files:**
- Modify: `scripts/generate_schema_docs.py`
- Modify: `test/test_schema_docs_generator.py`

- [ ] **Step 1: Write failing test for dependency extraction**

Add to `test/test_schema_docs_generator.py`:

```python
from generate_schema_docs import extract_dependencies


def test_extract_dependencies_simple_ref():
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest test/test_schema_docs_generator.py::test_extract_dependencies_simple_ref -v`

Expected: `AttributeError: module 'generate_schema_docs' has no attribute 'extract_dependencies'`

- [ ] **Step 3: Implement dependency extraction**

Add to `scripts/generate_schema_docs.py`:

```python
def extract_dependencies(schema_data: Dict[str, Any], schema_path: str) -> List[Dict[str, Any]]:
    """
    Extract all $schemaRef dependencies from a schema.
    
    Args:
        schema_data: Parsed schema dict
        schema_path: Path of this schema (for self-ref detection)
        
    Returns:
        List of dependency dicts with propertyPath and targetSchema
    """
    dependencies = []
    properties = schema_data.get("properties", {})
    
    def walk_properties(props: Dict[str, Any], path_prefix: str = "", is_array: bool = False):
        """Recursively walk properties to find $schemaRef."""
        for prop_name, prop_def in props.items():
            current_path = f"{path_prefix}.{prop_name}"
            
            # Check if this property is a reference
            if "$schemaRef" in prop_def:
                target = prop_def["$schemaRef"]
                # Normalize path: remove leading slash
                if target.startswith("/"):
                    target = target[1:]
                
                # Calculate nesting level (count dots in path)
                nesting_level = current_path.count(".")
                
                dependencies.append({
                    "propertyPath": current_path + ("[]" if is_array else ""),
                    "targetSchema": target,
                    "isArray": is_array,
                    "isNested": nesting_level >= 3
                })
            
            # Recurse into nested objects
            if prop_def.get("type") == "object" and "properties" in prop_def:
                walk_properties(prop_def["properties"], current_path, is_array)
            
            # Recurse into array items
            if prop_def.get("type") == "array" and "items" in prop_def:
                items = prop_def["items"]
                if isinstance(items, dict):
                    # Check if items itself is a reference
                    if "$schemaRef" in items:
                        target = items["$schemaRef"]
                        if target.startswith("/"):
                            target = target[1:]
                        
                        nesting_level = current_path.count(".")
                        
                        dependencies.append({
                            "propertyPath": current_path + "[]",
                            "targetSchema": target,
                            "isArray": True,
                            "isNested": nesting_level >= 3
                        })
                    # Or recurse into object properties
                    elif items.get("type") == "object" and "properties" in items:
                        walk_properties(items["properties"], current_path + "[]", True)
    
    walk_properties(properties)
    
    return dependencies
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest test/test_schema_docs_generator.py::test_extract_dependencies_simple_ref -v`

Expected: PASS

Run: `uv run pytest test/test_schema_docs_generator.py::test_extract_dependencies_array_ref -v`

Expected: PASS

Run: `uv run pytest test/test_schema_docs_generator.py::test_extract_dependencies_nested_ref -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_schema_docs.py test/test_schema_docs_generator.py
git commit -m "feat: add dependency extraction

- Recursively walk schema properties to find $schemaRef
- Track property path with array notation []
- Detect nested dependencies (3+ levels)
- Mark array vs single references

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Python Generator - Category Builder and Reverse Dependencies

**Files:**
- Modify: `scripts/generate_schema_docs.py`
- Modify: `test/test_schema_docs_generator.py`

- [ ] **Step 1: Write failing test for category builder**

Add to `test/test_schema_docs_generator.py`:

```python
from generate_schema_docs import build_categories, build_reverse_dependencies


def test_build_categories():
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest test/test_schema_docs_generator.py::test_build_categories -v`

Expected: `AttributeError: module 'generate_schema_docs' has no attribute 'build_categories'`

- [ ] **Step 3: Implement category builder and reverse dependencies**

Add to `scripts/generate_schema_docs.py`:

```python
def build_categories(schemas: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Group schemas by directory (first path segment).
    
    Args:
        schemas: Dict of schema_path -> schema_data
        
    Returns:
        List of category dicts with name and schema list
    """
    categories_dict = {}
    
    for schema_path in schemas.keys():
        # Extract category (directory name)
        if "/" in schema_path:
            category = schema_path.split("/")[0]
            schema_name = schema_path.split("/", 1)[1]
        else:
            # Root level file (e.g., common-1.json)
            category = "."
            schema_name = schema_path
        
        if category not in categories_dict:
            categories_dict[category] = []
        
        categories_dict[category].append(schema_name)
    
    # Convert to list and sort
    categories = []
    for name, schema_list in sorted(categories_dict.items()):
        categories.append({
            "name": name,
            "schemas": sorted(schema_list)
        })
    
    return categories


def build_reverse_dependencies(schemas: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Build reverse dependency map (what references each schema).
    
    Args:
        schemas: Dict of schema_path -> schema_data
        
    Returns:
        Dict of target_schema -> list of {schema, propertyPath}
    """
    reverse_deps = {}
    
    for schema_path, schema_data in schemas.items():
        dependencies = schema_data.get("dependencies", [])
        
        for dep in dependencies:
            target = dep["targetSchema"]
            
            if target not in reverse_deps:
                reverse_deps[target] = []
            
            reverse_deps[target].append({
                "schema": schema_path,
                "propertyPath": dep["propertyPath"]
            })
    
    return reverse_deps
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest test/test_schema_docs_generator.py::test_build_categories -v`

Expected: PASS

Run: `uv run pytest test/test_schema_docs_generator.py::test_build_reverse_dependencies -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_schema_docs.py test/test_schema_docs_generator.py
git commit -m "feat: add category builder and reverse dependencies

- Group schemas by directory for sidebar navigation
- Build reverse dependency map to show what references each schema
- Sort categories and schemas alphabetically

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Python Generator - Main Orchestration and JSON Output

**Files:**
- Modify: `scripts/generate_schema_docs.py`
- Modify: `test/test_schema_docs_generator.py`

- [ ] **Step 1: Write integration test for full generation**

Add to `test/test_schema_docs_generator.py`:

```python
import json
from generate_schema_docs import generate_schema_docs


def test_generate_schema_docs_integration(tmp_path):
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest test/test_schema_docs_generator.py::test_generate_schema_docs_integration -v`

Expected: `AttributeError: module 'generate_schema_docs' has no attribute 'generate_schema_docs'`

- [ ] **Step 3: Implement main orchestration function**

Add to `scripts/generate_schema_docs.py`:

```python
import json
import shutil


def generate_schema_docs(schemas_dir: str = "schemas", output_dir: str = "docs"):
    """
    Main function to generate schema documentation.
    
    Args:
        schemas_dir: Path to schemas directory
        output_dir: Path to output directory for generated files
    """
    print(f"Scanning schemas in {schemas_dir}...")
    
    # 1. Scan schemas directory
    schema_files = scan_schemas_directory(schemas_dir)
    print(f"Found {len(schema_files)} schema files")
    
    # 2. Parse each schema
    schemas = {}
    skipped = []
    
    for relative_path in schema_files:
        full_path = os.path.join(schemas_dir, relative_path)
        schema_data = parse_schema_file(full_path, relative_path)
        
        if schema_data is None:
            skipped.append(relative_path)
            continue
        
        schemas[relative_path] = schema_data
    
    if skipped:
        print(f"Warning: Skipped {len(skipped)} invalid schema files:")
        for path in skipped:
            print(f"  - {path}")
    
    print(f"Successfully parsed {len(schemas)} schemas")
    
    # 3. Extract dependencies for each schema
    for schema_path, schema_data in schemas.items():
        dependencies = extract_dependencies(schema_data, schema_path)
        schema_data["dependencies"] = dependencies
    
    # 4. Build reverse dependencies
    reverse_deps = build_reverse_dependencies(schemas)
    for schema_path, refs in reverse_deps.items():
        if schema_path in schemas:
            schemas[schema_path]["referencedBy"] = refs
    
    # 5. Build categories
    categories = build_categories(schemas)
    
    # 6. Create output structure
    output = {
        "categories": categories,
        "schemas": schemas
    }
    
    # 7. Write JSON output
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "schemas.json")
    
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"Generated {output_file}")
    print(f"  - {len(categories)} categories")
    print(f"  - {len(schemas)} schemas")
    
    # 8. Copy static assets (templates will be created in next task)
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    if os.path.exists(templates_dir):
        for asset in ["index.html", "styles.css"]:
            src = os.path.join(templates_dir, asset)
            dst = os.path.join(output_dir, asset)
            if os.path.exists(src):
                shutil.copy(src, dst)
                print(f"Copied {asset}")


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate schema documentation")
    parser.add_argument("--schemas-dir", default="schemas", help="Schemas directory")
    parser.add_argument("--output-dir", default="docs", help="Output directory")
    
    args = parser.parse_args()
    
    generate_schema_docs(args.schemas_dir, args.output_dir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest test/test_schema_docs_generator.py::test_generate_schema_docs_integration -v`

Expected: PASS

- [ ] **Step 5: Test CLI execution**

Run: `uv run python scripts/generate_schema_docs.py --help`

Expected: Shows help message with --schemas-dir and --output-dir options

- [ ] **Step 6: Commit**

```bash
git add scripts/generate_schema_docs.py test/test_schema_docs_generator.py
git commit -m "feat: add main orchestration and JSON output

- Implement generate_schema_docs() to coordinate all steps
- Add CLI entry point with argparse
- Write schemas.json with categories and schemas
- Report progress and skipped files
- Copy static assets from templates/

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 6: Static HTML Viewer - Base Structure

**Files:**
- Create: `scripts/templates/index.html`

- [ ] **Step 1: Create HTML template with base structure**

Create `scripts/templates/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Qontract Schema Viewer</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <noscript>
        <div class="noscript-message">
            This tool requires JavaScript. Please enable it or view schemas directly on
            <a href="https://github.com/app-sre/qontract-schemas">GitHub</a>.
        </div>
    </noscript>

    <!-- Header -->
    <header class="header">
        <h1 class="header-title">Qontract Schema Viewer</h1>
        <div class="search-container">
            <input type="text" id="searchInput" class="search-input" placeholder="Search schemas, properties...">
            <button id="searchClear" class="search-clear" style="display: none;">×</button>
        </div>
    </header>

    <!-- Main layout -->
    <div class="layout">
        <!-- Sidebar -->
        <aside class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <span class="sidebar-title">Schemas</span>
            </div>
            <div class="sidebar-content" id="sidebarContent">
                <!-- Categories will be rendered here -->
            </div>
        </aside>

        <!-- Main panel -->
        <main class="main-panel" id="mainPanel">
            <div class="welcome-message">
                <h2>Welcome to Qontract Schema Viewer</h2>
                <p>Select a schema from the sidebar to view its details.</p>
            </div>
        </main>
    </div>

    <!-- Error display -->
    <div id="errorDisplay" class="error-display" style="display: none;">
        <h2>Error Loading Schema Data</h2>
        <p id="errorMessage"></p>
        <p>Please regenerate the documentation using <code>make generate-docs</code></p>
    </div>

    <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Verify HTML structure**

Open the file and visually inspect:
- Proper DOCTYPE and meta tags
- Header with title and search
- Layout with sidebar and main panel
- Error display for loading failures
- Script tag for app.js (will be embedded inline later)

- [ ] **Step 3: Commit**

```bash
git add scripts/templates/index.html
git commit -m "feat: add HTML viewer base structure

- Header with title and search bar
- Sidebar for category/schema navigation
- Main panel for schema details
- Error display for load failures
- Noscript fallback message

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 7: Static CSS - Complete Stylesheet

**Files:**
- Create: `scripts/templates/styles.css`

- [ ] **Step 1: Create complete CSS stylesheet**

Create `scripts/templates/styles.css`:

```css
/* Reset and base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    --primary: #007bff;
    --success: #28a745;
    --warning: #ffc107;
    --danger: #dc3545;
    --bg-light: #f8f9fa;
    --bg-secondary: #e9ecef;
    --border: #dee2e6;
    --text-muted: #6c757d;
    --text-dark: #2c3e50;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.6;
    color: var(--text-dark);
    background: #ffffff;
}

code, .monospace {
    font-family: Consolas, Monaco, 'Courier New', monospace;
}

/* Noscript message */
.noscript-message {
    padding: 2rem;
    text-align: center;
    background: var(--warning);
    color: #000;
}

/* Header */
.header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 60px;
    background: var(--text-dark);
    color: white;
    padding: 0 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 2px solid #34495e;
    z-index: 100;
}

.header-title {
    font-size: 1.2rem;
    font-weight: 600;
    margin: 0;
}

.search-container {
    position: relative;
    width: 350px;
}

.search-input {
    width: 100%;
    padding: 0.5rem 2rem 0.5rem 0.75rem;
    border: 1px solid #4a5f7f;
    border-radius: 4px;
    background: #34495e;
    color: white;
    font-size: 0.9rem;
}

.search-input::placeholder {
    color: #95a5a6;
}

.search-input:focus {
    outline: none;
    border-color: var(--primary);
}

.search-clear {
    position: absolute;
    right: 0.5rem;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    color: white;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0 0.25rem;
}

.search-clear:hover {
    color: var(--danger);
}

/* Layout */
.layout {
    display: flex;
    margin-top: 60px;
    height: calc(100vh - 60px);
}

/* Sidebar */
.sidebar {
    width: 280px;
    background: var(--bg-light);
    border-right: 1px solid var(--border);
    overflow-y: auto;
    flex-shrink: 0;
}

.sidebar-header {
    padding: 1rem;
    border-bottom: 1px solid var(--border);
}

.sidebar-title {
    font-size: 0.75rem;
    font-weight: bold;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.sidebar-content {
    padding: 0.5rem 0;
}

/* Category */
.category {
    margin-bottom: 0.5rem;
}

.category-header {
    display: flex;
    align-items: center;
    padding: 0.5rem 1rem;
    background: var(--bg-secondary);
    cursor: pointer;
    user-select: none;
}

.category-header:hover {
    background: #dde0e3;
}

.category-toggle {
    margin-right: 0.5rem;
    font-size: 0.8rem;
    transition: transform 0.2s;
}

.category-toggle.expanded {
    transform: rotate(90deg);
}

.category-name {
    font-weight: 600;
    flex: 1;
}

.category-count {
    color: var(--text-muted);
    font-size: 0.85rem;
}

.category-schemas {
    display: none;
    padding-left: 1.5rem;
    border-left: 1px solid var(--border);
    margin-left: 1rem;
}

.category-schemas.expanded {
    display: block;
}

.schema-item {
    padding: 0.4rem 0.75rem;
    cursor: pointer;
    border-radius: 3px;
    margin: 2px 0;
}

.schema-item:hover {
    background: var(--bg-secondary);
}

.schema-item.active {
    background: var(--primary);
    color: white;
    font-weight: 500;
}

.schema-item.hidden {
    display: none;
}

/* Main panel */
.main-panel {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem;
}

.welcome-message {
    text-align: center;
    padding: 4rem 2rem;
    color: var(--text-muted);
}

/* Schema header */
.schema-header {
    border-bottom: 2px solid var(--primary);
    padding-bottom: 0.75rem;
    margin-bottom: 1.5rem;
}

.schema-header h2 {
    margin: 0;
    color: var(--text-dark);
}

.schema-meta {
    margin-top: 0.5rem;
    color: var(--text-muted);
    font-size: 0.9rem;
}

.schema-path-badge {
    background: #e7f3ff;
    padding: 0.25rem 0.5rem;
    border-radius: 3px;
    font-family: monospace;
    font-size: 0.85rem;
    margin-right: 1rem;
}

/* Tabs */
.tabs {
    display: flex;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
    gap: 0.5rem;
}

.tab {
    padding: 0.75rem 1rem;
    cursor: pointer;
    border-bottom: 3px solid transparent;
    color: var(--text-muted);
    user-select: none;
}

.tab:hover {
    color: var(--text-dark);
}

.tab.active {
    border-bottom-color: var(--primary);
    color: var(--text-dark);
    font-weight: 600;
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

/* Properties table */
.properties-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
}

.properties-table thead {
    background: var(--bg-light);
    border-bottom: 2px solid var(--border);
}

.properties-table th {
    padding: 0.75rem;
    text-align: left;
    font-weight: 600;
}

.properties-table tbody tr {
    border-bottom: 1px solid var(--border);
}

.properties-table tbody tr.ref-property {
    background: #fffbf0;
}

.properties-table tbody tr:hover {
    background: var(--bg-light);
}

.properties-table td {
    padding: 0.75rem;
    vertical-align: top;
}

.prop-name {
    font-family: monospace;
    font-weight: 600;
}

.type-badge {
    display: inline-block;
    padding: 0.2rem 0.5rem;
    border-radius: 3px;
    font-size: 0.85rem;
    font-weight: 500;
}

.type-string { background: #e9ecef; }
.type-number { background: #d1ecf1; }
.type-boolean { background: #e7d4f8; }
.type-enum { background: #fff3cd; }
.type-ref { background: #d4edff; }
.type-array { background: #d4edda; }
.type-object { background: #f8d7da; }

.prop-description {
    color: var(--text-muted);
}

.prop-description.empty {
    color: #bbb;
    font-style: italic;
}

.prop-required {
    text-align: center;
    color: var(--success);
    font-weight: bold;
}

.schema-link {
    color: var(--primary);
    text-decoration: none;
    font-weight: 500;
}

.schema-link:hover {
    text-decoration: underline;
}

.schema-ref-type {
    font-family: monospace;
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-top: 0.3rem;
    display: block;
}

/* Dependencies */
.dependency-stats {
    background: var(--bg-light);
    padding: 1.5rem;
    border-radius: 4px;
    margin-bottom: 1.5rem;
    display: flex;
    gap: 2rem;
}

.stat {
    text-align: center;
}

.stat-value {
    font-size: 1.8rem;
    font-weight: bold;
    color: var(--primary);
}

.stat-label {
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-top: 0.25rem;
}

.dependency-tree {
    font-family: monospace;
    font-size: 0.9rem;
    line-height: 1.8;
}

.tree-root {
    font-weight: bold;
    margin-bottom: 1rem;
    color: var(--text-dark);
}

.tree-item {
    margin-bottom: 1rem;
    padding-left: 2rem;
    border-left: 2px solid var(--border);
}

.tree-branch {
    color: var(--danger);
    margin-right: 0.5rem;
}

.tree-path {
    background: #e7f3ff;
    padding: 0.2rem 0.4rem;
    border-radius: 3px;
}

.tree-target {
    margin-left: 2rem;
    margin-top: 0.3rem;
}

.dep-badge {
    display: inline-block;
    padding: 0.1rem 0.4rem;
    border-radius: 3px;
    font-size: 0.75rem;
    margin-left: 0.5rem;
    font-weight: 600;
}

.badge-self-ref {
    background: var(--warning);
    color: #000;
}

.badge-array {
    background: var(--bg-secondary);
    color: var(--text-dark);
}

.badge-nested {
    background: var(--bg-secondary);
    color: var(--text-dark);
}

.badge-missing {
    background: var(--danger);
    color: white;
}

.reverse-deps {
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 2px solid var(--border);
}

.reverse-deps h3 {
    font-size: 1rem;
    margin-bottom: 1rem;
    color: var(--text-dark);
}

.reverse-dep-item {
    font-family: monospace;
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-bottom: 0.3rem;
}

/* Error display */
.error-display {
    padding: 2rem;
    text-align: center;
    background: var(--bg-light);
    margin: 2rem;
    border-radius: 4px;
    border: 2px solid var(--danger);
}

.error-display h2 {
    color: var(--danger);
    margin-bottom: 1rem;
}

/* Mobile responsive */
@media (max-width: 768px) {
    .header {
        flex-direction: column;
        height: auto;
        padding: 1rem;
    }

    .search-container {
        width: 100%;
        margin-top: 0.5rem;
    }

    .layout {
        flex-direction: column;
    }

    .sidebar {
        width: 100%;
        max-height: 300px;
    }

    .main-panel {
        height: auto;
    }
}
```

- [ ] **Step 2: Verify CSS organization**

Review the stylesheet:
- Color variables defined in :root
- All spec'd components styled
- Responsive breakpoint at 768px
- No hardcoded colors (uses CSS variables)

- [ ] **Step 3: Commit**

```bash
git add scripts/templates/styles.css
git commit -m "feat: add complete CSS stylesheet

- Color system with CSS variables
- Header, sidebar, main panel layouts
- Category and schema item styles
- Properties table with type badges
- Dependency tree visualization
- Responsive design for mobile
- Error display styles

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 8: JavaScript Viewer - Data Loading and State Management

**Files:**
- Modify: `scripts/templates/index.html` (embed JavaScript inline)

- [ ] **Step 1: Add JavaScript for data loading**

Replace `<script src="app.js"></script>` in `index.html` with:

```html
<script>
// State management
const state = {
    schemas: null,
    categories: null,
    currentSchema: null,
    activeTab: 'properties',
    searchQuery: ''
};

// Initialize app
async function init() {
    try {
        const response = await fetch('schemas.json');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        state.schemas = data.schemas;
        state.categories = data.categories;
        
        renderSidebar();
        setupEventListeners();
    } catch (error) {
        showError(`Failed to load schema data: ${error.message}`);
    }
}

// Show error message
function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('errorDisplay').style.display = 'block';
    document.querySelector('.layout').style.display = 'none';
}

// Render sidebar categories and schemas
function renderSidebar() {
    const container = document.getElementById('sidebarContent');
    container.innerHTML = '';
    
    state.categories.forEach(category => {
        const categoryEl = createCategoryElement(category);
        container.appendChild(categoryEl);
    });
}

// Create category element
function createCategoryElement(category) {
    const categoryDiv = document.createElement('div');
    categoryDiv.className = 'category';
    
    // Category header
    const headerDiv = document.createElement('div');
    headerDiv.className = 'category-header';
    headerDiv.innerHTML = `
        <span class="category-toggle">▶</span>
        <span class="category-name">${escapeHtml(category.name)}</span>
        <span class="category-count">(${category.schemas.length})</span>
    `;
    
    // Schemas list
    const schemasDiv = document.createElement('div');
    schemasDiv.className = 'category-schemas';
    
    category.schemas.forEach(schemaName => {
        const schemaPath = category.name === '.' ? schemaName : `${category.name}/${schemaName}`;
        const schemaItem = document.createElement('div');
        schemaItem.className = 'schema-item';
        schemaItem.textContent = schemaName;
        schemaItem.dataset.schemaPath = schemaPath;
        schemaItem.onclick = () => loadSchema(schemaPath);
        schemasDiv.appendChild(schemaItem);
    });
    
    // Toggle category
    headerDiv.onclick = () => {
        const toggle = headerDiv.querySelector('.category-toggle');
        const isExpanded = schemasDiv.classList.toggle('expanded');
        toggle.classList.toggle('expanded', isExpanded);
    };
    
    categoryDiv.appendChild(headerDiv);
    categoryDiv.appendChild(schemasDiv);
    
    return categoryDiv;
}

// Load and display schema
function loadSchema(schemaPath) {
    const schema = state.schemas[schemaPath];
    if (!schema) {
        console.error(`Schema not found: ${schemaPath}`);
        return;
    }
    
    state.currentSchema = schemaPath;
    
    // Update active state in sidebar
    document.querySelectorAll('.schema-item').forEach(item => {
        item.classList.toggle('active', item.dataset.schemaPath === schemaPath);
    });
    
    renderSchemaDetails(schema);
}

// Render schema details (main panel)
function renderSchemaDetails(schema) {
    const mainPanel = document.getElementById('mainPanel');
    
    mainPanel.innerHTML = `
        <div class="schema-header">
            <h2>${escapeHtml(schema.path.split('/').pop())}</h2>
            <div class="schema-meta">
                <span class="schema-path-badge">${escapeHtml(schema.path)}</span>
                <span>Version ${escapeHtml(schema.version)}</span>
            </div>
        </div>
        
        <div class="tabs">
            <div class="tab active" data-tab="properties">Properties</div>
            <div class="tab" data-tab="dependencies">Dependencies</div>
        </div>
        
        <div class="tab-content active" id="propertiesTab">
            ${renderPropertiesTab(schema)}
        </div>
        
        <div class="tab-content" id="dependenciesTab">
            ${renderDependenciesTab(schema)}
        </div>
    `;
    
    // Setup tab switching
    mainPanel.querySelectorAll('.tab').forEach(tab => {
        tab.onclick = () => switchTab(tab.dataset.tab);
    });
}

// Switch between tabs
function switchTab(tabName) {
    state.activeTab = tabName;
    
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });
    
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}Tab`);
    });
}

// Setup event listeners
function setupEventListeners() {
    const searchInput = document.getElementById('searchInput');
    const searchClear = document.getElementById('searchClear');
    
    // Search functionality (will implement in next task)
    searchInput.addEventListener('input', handleSearch);
    searchClear.onclick = () => {
        searchInput.value = '';
        handleSearch();
    };
}

// Handle search (placeholder)
function handleSearch() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    state.searchQuery = query;
    
    document.getElementById('searchClear').style.display = query ? 'block' : 'none';
    
    // Filter implementation will be added in next task
    console.log('Search:', query);
}

// Utility: Escape HTML
function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Start the app
document.addEventListener('DOMContentLoaded', init);
</script>
```

- [ ] **Step 2: Test data loading**

Run generator and open in browser:
```bash
uv run python scripts/generate_schema_docs.py
cd docs && python -m http.server 8000
```

Open http://localhost:8000 and verify:
- Categories render in sidebar
- Clicking category expands schema list
- Error display shows if schemas.json missing

- [ ] **Step 3: Commit**

```bash
git add scripts/templates/index.html
git commit -m "feat: add JavaScript data loading and sidebar rendering

- Fetch and parse schemas.json on page load
- Render categories with expand/collapse
- Show error message if loading fails
- Basic state management
- Schema selection (click handlers)

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 9: JavaScript Viewer - Properties Tab Rendering

**Files:**
- Modify: `scripts/templates/index.html`

- [ ] **Step 1: Add properties tab rendering function**

Add before the closing `</script>` tag in `index.html`:

```javascript
// Render properties tab
function renderPropertiesTab(schema) {
    if (!schema.properties || schema.properties.length === 0) {
        return '<p class="prop-description empty">No properties defined</p>';
    }
    
    let html = '<table class="properties-table"><thead><tr>';
    html += '<th style="width: 25%;">Property</th>';
    html += '<th style="width: 15%;">Type</th>';
    html += '<th style="width: 50%;">Description</th>';
    html += '<th style="width: 10%; text-align: center;">Required</th>';
    html += '</tr></thead><tbody>';
    
    schema.properties.forEach(prop => {
        const isRef = prop.type === 'object (ref)';
        const rowClass = isRef ? 'ref-property' : '';
        
        html += `<tr class="${rowClass}">`;
        
        // Property name
        html += `<td class="prop-name">${escapeHtml(prop.name)}</td>`;
        
        // Type badge
        html += '<td>';
        const typeClass = getTypeClass(prop.type);
        html += `<span class="type-badge ${typeClass}">${escapeHtml(prop.type)}</span>`;
        html += '</td>';
        
        // Description with ref link
        html += '<td>';
        if (isRef && prop.schemaRef) {
            html += `<a href="#" class="schema-link" onclick="loadSchema('${escapeHtml(prop.schemaRef)}'); return false;">`;
            html += `→ ${escapeHtml(prop.schemaRef)}`;
            html += '</a>';
            html += '<span class="schema-ref-type">$schemaRef</span>';
        } else if (prop.description) {
            html += `<span class="prop-description">${escapeHtml(prop.description)}</span>`;
        } else {
            html += '<span class="prop-description empty">(no description)</span>';
        }
        
        // Show constraints if present
        if (prop.constraints && Object.keys(prop.constraints).length > 0) {
            html += renderConstraints(prop.constraints);
        }
        
        html += '</td>';
        
        // Required
        html += '<td class="prop-required">';
        html += prop.required ? '✓' : '−';
        html += '</td>';
        
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    
    return html;
}

// Get CSS class for type badge
function getTypeClass(type) {
    const typeMap = {
        'string': 'type-string',
        'number': 'type-number',
        'integer': 'type-number',
        'boolean': 'type-boolean',
        'enum': 'type-enum',
        'object (ref)': 'type-ref',
        'array': 'type-array',
        'object': 'type-object'
    };
    
    return typeMap[type] || 'type-string';
}

// Render constraints
function renderConstraints(constraints) {
    let html = '<div style="margin-top: 0.5rem; font-size: 0.85rem; color: #666;">';
    
    // Enum values
    if (constraints.enum) {
        const values = constraints.enum.slice(0, 3).map(v => `<code>${escapeHtml(String(v))}</code>`).join(' | ');
        const more = constraints.enum.length > 3 ? ` ... (+${constraints.enum.length - 3})` : '';
        html += `<div>Values: ${values}${more}</div>`;
    }
    
    // Pattern
    if (constraints.pattern) {
        html += `<div>Pattern: <code>${escapeHtml(constraints.pattern)}</code></div>`;
    }
    
    // Format
    if (constraints.format) {
        html += `<div>Format: <code>${escapeHtml(constraints.format)}</code></div>`;
    }
    
    // Min/Max
    if (constraints.minimum !== undefined || constraints.maximum !== undefined) {
        const min = constraints.minimum !== undefined ? constraints.minimum : '−∞';
        const max = constraints.maximum !== undefined ? constraints.maximum : '∞';
        html += `<div>Range: ${min} to ${max}</div>`;
    }
    
    // Length constraints
    if (constraints.minLength !== undefined || constraints.maxLength !== undefined) {
        const min = constraints.minLength !== undefined ? constraints.minLength : 0;
        const max = constraints.maxLength !== undefined ? constraints.maxLength : '∞';
        html += `<div>Length: ${min} to ${max}</div>`;
    }
    
    // Default value
    if (constraints.default !== undefined) {
        html += `<div>Default: <code>${escapeHtml(String(constraints.default))}</code></div>`;
    }
    
    html += '</div>';
    
    return html;
}
```

- [ ] **Step 2: Test properties tab rendering**

Regenerate docs and test in browser:
```bash
uv run python scripts/generate_schema_docs.py
```

Open http://localhost:8000 and verify:
- Click a schema (e.g., app-sre/app-1.yml)
- Properties table displays with all columns
- Type badges have correct colors
- Reference properties show clickable links
- Constraints display below properties
- Required column shows ✓ or −

- [ ] **Step 3: Commit**

```bash
git add scripts/templates/index.html
git commit -m "feat: add properties tab rendering

- Render properties table with name, type, description, required
- Color-coded type badges
- Clickable schema reference links
- Display constraints (enum, pattern, format, min/max, default)
- Highlight reference properties with background color

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 10: JavaScript Viewer - Dependencies Tab Rendering

**Files:**
- Modify: `scripts/templates/index.html`

- [ ] **Step 1: Add dependencies tab rendering function**

Add before the closing `</script>` tag in `index.html`:

```javascript
// Render dependencies tab
function renderDependenciesTab(schema) {
    const deps = schema.dependencies || [];
    const reverseDeps = schema.referencedBy || [];
    
    let html = '';
    
    // Stats summary
    const uniqueSchemas = new Set(deps.map(d => d.targetSchema)).size;
    html += '<div class="dependency-stats">';
    html += '<div class="stat">';
    html += `<div class="stat-value">${uniqueSchemas}</div>`;
    html += '<div class="stat-label">Schemas Referenced</div>';
    html += '</div>';
    html += '<div class="stat">';
    html += `<div class="stat-value">${deps.length}</div>`;
    html += '<div class="stat-label">Reference Properties</div>';
    html += '</div>';
    html += '</div>';
    
    // Dependency tree
    if (deps.length > 0) {
        html += '<div class="dependency-tree">';
        html += `<div class="tree-root">📄 ${escapeHtml(schema.path)}</div>`;
        
        deps.forEach((dep, index) => {
            const isLast = index === deps.length - 1;
            const branch = isLast ? '└─' : '├─';
            
            html += '<div class="tree-item">';
            html += `<div><span class="tree-branch">${branch}</span>`;
            html += `<span class="tree-path">${escapeHtml(dep.propertyPath)}</span>`;
            html += '</div>';
            
            html += '<div class="tree-target">';
            html += `<a href="#" class="schema-link" onclick="loadSchema('${escapeHtml(dep.targetSchema)}'); return false;">`;
            html += `→ ${escapeHtml(dep.targetSchema)}`;
            html += '</a>';
            
            // Add badges
            const badges = [];
            
            // Self-reference check
            if (dep.targetSchema === schema.path) {
                badges.push('<span class="dep-badge badge-self-ref">SELF-REF</span>');
            }
            
            // Array badge
            if (dep.isArray) {
                badges.push('<span class="dep-badge badge-array">ARRAY</span>');
            }
            
            // Nested badge
            if (dep.isNested) {
                badges.push('<span class="dep-badge badge-nested">NESTED</span>');
            }
            
            // Missing badge (check if target exists)
            if (!state.schemas[dep.targetSchema]) {
                badges.push('<span class="dep-badge badge-missing">MISSING</span>');
            }
            
            html += badges.join(' ');
            html += '</div>';
            html += '</div>';
        });
        
        html += '</div>';
    } else {
        html += '<p class="prop-description empty">No dependencies found</p>';
    }
    
    // Reverse dependencies
    if (reverseDeps.length > 0) {
        html += '<div class="reverse-deps">';
        html += '<h3>Referenced By (Reverse Dependencies)</h3>';
        
        reverseDeps.forEach(ref => {
            html += '<div class="reverse-dep-item">';
            html += '• ';
            html += `<a href="#" class="schema-link" onclick="loadSchema('${escapeHtml(ref.schema)}'); return false;">`;
            html += escapeHtml(ref.schema);
            html += '</a>';
            html += ` → ${escapeHtml(ref.propertyPath)}`;
            html += '</div>';
        });
        
        html += '</div>';
    }
    
    return html;
}
```

- [ ] **Step 2: Test dependencies tab rendering**

Regenerate and test:
```bash
uv run python scripts/generate_schema_docs.py
```

Open http://localhost:8000 and verify:
- Click a schema with dependencies (e.g., app-sre/app-1.yml)
- Click "Dependencies" tab
- Stats show correct counts
- Tree displays with proper branch characters (├─, └─)
- Property paths shown with blue background
- Badges display for SELF-REF, ARRAY, NESTED
- Reverse dependencies section shows if present
- Clicking schema links navigates correctly

- [ ] **Step 3: Commit**

```bash
git add scripts/templates/index.html
git commit -m "feat: add dependencies tab rendering

- Display dependency statistics summary
- Render tree view with property paths
- Show target schema links
- Add badges for self-ref, array, nested, missing
- Display reverse dependencies section
- Full navigation between referenced schemas

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 11: JavaScript Viewer - Search Functionality

**Files:**
- Modify: `scripts/templates/index.html`

- [ ] **Step 1: Implement search filtering**

Replace the `handleSearch` function in `index.html` with:

```javascript
// Handle search
function handleSearch() {
    const query = document.getElementById('searchInput').value.toLowerCase().trim();
    state.searchQuery = query;
    
    document.getElementById('searchClear').style.display = query ? 'block' : 'none';
    
    if (!query) {
        // Clear search - show all
        document.querySelectorAll('.schema-item').forEach(item => {
            item.classList.remove('hidden');
        });
        document.querySelectorAll('.category').forEach(cat => {
            cat.style.display = '';
        });
        return;
    }
    
    // Filter schemas in sidebar
    let visibleCount = 0;
    
    document.querySelectorAll('.category').forEach(categoryEl => {
        const schemasDiv = categoryEl.querySelector('.category-schemas');
        let categoryHasVisible = false;
        
        schemasDiv.querySelectorAll('.schema-item').forEach(schemaItem => {
            const schemaPath = schemaItem.dataset.schemaPath;
            const schemaName = schemaItem.textContent.toLowerCase();
            const schema = state.schemas[schemaPath];
            
            // Search in: schema name, path, property names, property descriptions
            let matches = false;
            
            // Check schema name and path
            if (schemaName.includes(query) || schemaPath.toLowerCase().includes(query)) {
                matches = true;
            }
            
            // Check properties
            if (!matches && schema && schema.properties) {
                matches = schema.properties.some(prop => {
                    return (
                        prop.name.toLowerCase().includes(query) ||
                        (prop.description && prop.description.toLowerCase().includes(query))
                    );
                });
            }
            
            if (matches) {
                schemaItem.classList.remove('hidden');
                categoryHasVisible = true;
                visibleCount++;
            } else {
                schemaItem.classList.add('hidden');
            }
        });
        
        // Hide category if no visible schemas
        if (categoryHasVisible) {
            categoryEl.style.display = '';
            // Auto-expand category on search
            schemasDiv.classList.add('expanded');
            categoryEl.querySelector('.category-toggle').classList.add('expanded');
        } else {
            categoryEl.style.display = 'none';
        }
    });
    
    // If current schema is filtered out, clear main panel
    if (state.currentSchema) {
        const currentItem = document.querySelector(`.schema-item[data-schema-path="${state.currentSchema}"]`);
        if (currentItem && currentItem.classList.contains('hidden')) {
            document.getElementById('mainPanel').innerHTML = `
                <div class="welcome-message">
                    <h2>No matching schemas</h2>
                    <p>Try a different search term.</p>
                </div>
            `;
            state.currentSchema = null;
        }
    }
}
```

- [ ] **Step 2: Add debouncing for search performance**

Add before the `handleSearch` function:

```javascript
// Debounce utility
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Create debounced search handler
const debouncedSearch = debounce(handleSearch, 200);
```

Then update the event listener setup:

```javascript
// In setupEventListeners function, replace:
searchInput.addEventListener('input', handleSearch);
// With:
searchInput.addEventListener('input', debouncedSearch);
```

- [ ] **Step 3: Test search functionality**

Regenerate and test:
```bash
uv run python scripts/generate_schema_docs.py
```

Open http://localhost:8000 and verify:
- Type "app" in search - shows matching schemas
- Type "escalation" - shows escalation-policy and properties named escalationPolicy
- Type "aws/" - shows all AWS schemas
- Clear button (×) appears when searching
- Click clear button - resets to show all schemas
- Search auto-expands matching categories
- Empty categories hidden during search

- [ ] **Step 4: Commit**

```bash
git add scripts/templates/index.html
git commit -m "feat: add search functionality

- Filter schemas by name, path, property names, descriptions
- Case-insensitive substring matching
- Auto-expand categories with matches
- Hide empty categories during search
- Debounce input for performance (200ms)
- Clear button to reset search

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 12: Makefile Integration

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Add generate-docs target to Makefile**

Add after the existing targets in `Makefile`:

```makefile
generate-docs: ## Generate schema documentation site
	@echo "Generating schema documentation..."
	@mkdir -p scripts/templates
	uv run python scripts/generate_schema_docs.py --schemas-dir schemas --output-dir docs
	@echo "Documentation generated in docs/"
	@echo "To view locally: cd docs && python -m http.server 8000"
```

- [ ] **Step 2: Test make target**

Run: `make generate-docs`

Expected: 
- Creates docs/ directory
- Generates schemas.json
- Copies index.html and styles.css
- Prints success message

- [ ] **Step 3: Verify output**

Run: `ls -la docs/`

Expected:
```
docs/
├── index.html
├── schemas.json
└── styles.css
```

- [ ] **Step 4: Add docs/ to .gitignore**

Run: `echo "/docs/" >> .gitignore`

- [ ] **Step 5: Commit**

```bash
git add Makefile .gitignore
git commit -m "feat: add generate-docs Makefile target

- Add make generate-docs command
- Generates static site in docs/ directory
- Add docs/ to .gitignore (will be generated by CI)

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 13: CI/CD GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/deploy-docs.yml`

- [ ] **Step 1: Create GitHub Actions workflow**

Create `.github/workflows/deploy-docs.yml`:

```yaml
name: Deploy Schema Docs

on:
  push:
    branches:
      - main
    paths:
      - 'schemas/**'
      - 'scripts/generate_schema_docs.py'
      - 'scripts/templates/**'
      - '.github/workflows/deploy-docs.yml'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      
      - name: Install uv
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          echo "$HOME/.cargo/bin" >> $GITHUB_PATH
      
      - name: Install dependencies
        run: uv sync
      
      - name: Generate documentation
        run: make generate-docs
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
          commit_message: 'docs: update schema documentation'
```

- [ ] **Step 2: Verify workflow file**

Check:
- Triggers on push to main when schemas or scripts change
- Has workflow_dispatch for manual runs
- Uses Python 3.14
- Installs uv and dependencies
- Runs make generate-docs
- Deploys to gh-pages branch

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/deploy-docs.yml
git commit -m "feat: add GitHub Actions workflow for docs deployment

- Trigger on schema or script changes
- Set up Python 3.14 and uv
- Generate docs with make generate-docs
- Deploy to GitHub Pages on gh-pages branch
- Support manual workflow dispatch

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 14: Documentation and README

**Files:**
- Create: `scripts/README.md`
- Modify: `README.md`

- [ ] **Step 1: Create scripts README**

Create `scripts/README.md`:

```markdown
# Schema Documentation Generator

This directory contains the schema documentation generator and templates.

## Files

- `generate_schema_docs.py` - Main generator script
- `templates/index.html` - HTML viewer template
- `templates/styles.css` - Stylesheet

## Usage

Generate documentation:

\`\`\`bash
make generate-docs
\`\`\`

Or run directly:

\`\`\`bash
uv run python scripts/generate_schema_docs.py --schemas-dir schemas --output-dir docs
\`\`\`

## Options

- `--schemas-dir` - Directory containing schema files (default: `schemas`)
- `--output-dir` - Output directory for generated files (default: `docs`)

## Output

Generates three files in the output directory:

- `schemas.json` - All parsed schema data
- `index.html` - Single-page viewer application
- `styles.css` - Styling

## Local Development

View the generated docs locally:

\`\`\`bash
cd docs
python -m http.server 8000
\`\`\`

Then open http://localhost:8000 in your browser.

## Testing

Run tests:

\`\`\`bash
uv run pytest test/test_schema_docs_generator.py -v
\`\`\`
```

- [ ] **Step 2: Update main README**

Add to the end of `README.md`:

```markdown

## Schema Documentation

This repository includes a web-based schema viewer for easy navigation and exploration.

### View Online

Visit the [Schema Documentation](https://app-sre.github.io/qontract-schemas/) (available after first deployment)

### Generate Locally

\`\`\`bash
make generate-docs
cd docs && python -m http.server 8000
\`\`\`

Then open http://localhost:8000

### Features

- Browse schemas by category
- View property types, descriptions, and constraints
- Visualize dependencies between schemas
- Search across schema names and properties
- Mobile-responsive interface

See `scripts/README.md` for more details.
```

- [ ] **Step 3: Commit**

```bash
git add scripts/README.md README.md
git commit -m "docs: add schema documentation generator README

- Usage instructions for generate-docs
- Local development guide
- Testing commands
- Update main README with viewer link

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 15: End-to-End Testing and Validation

**Files:**
- Test all components together

- [ ] **Step 1: Generate docs from actual schemas**

Run: `make generate-docs`

Expected:
- No errors during generation
- schemas.json created with all actual schemas
- Logs show schema count, categories

- [ ] **Step 2: Validate JSON output structure**

Run:
```bash
uv run python -c "
import json
with open('docs/schemas.json') as f:
    data = json.load(f)
    assert 'categories' in data
    assert 'schemas' in data
    assert len(data['categories']) > 0
    assert len(data['schemas']) > 0
    print(f\"✓ Valid JSON: {len(data['categories'])} categories, {len(data['schemas'])} schemas\")
"
```

Expected: `✓ Valid JSON: X categories, Y schemas`

- [ ] **Step 3: Test viewer in browser**

Run: `cd docs && python -m http.server 8000`

Open http://localhost:8000 and manually test:
- [ ] Sidebar shows all categories
- [ ] Categories expand/collapse correctly
- [ ] Click a schema loads it in main panel
- [ ] Properties tab shows all properties with correct types
- [ ] Reference links are clickable and navigate correctly
- [ ] Dependencies tab shows tree view
- [ ] Stats are accurate
- [ ] Badges display (SELF-REF, ARRAY, NESTED if applicable)
- [ ] Search filters schemas correctly
- [ ] Search matches property names
- [ ] Clear button resets search
- [ ] No console errors

- [ ] **Step 4: Run all tests**

Run: `uv run pytest test/test_schema_docs_generator.py -v`

Expected: All tests PASS

- [ ] **Step 5: Commit verification results**

```bash
git add -A
git commit -m "test: verify end-to-end schema documentation generation

- Generated docs from actual schemas successfully
- Validated JSON output structure
- Manual browser testing complete
- All unit tests passing

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 16: GitHub Pages Setup Instructions

**Files:**
- Create: `docs/superpowers/plans/DEPLOYMENT.md`

- [ ] **Step 1: Create deployment instructions**

Create `docs/superpowers/plans/DEPLOYMENT.md`:

```markdown
# Schema Documentation Deployment

## GitHub Pages Setup

### One-Time Configuration

1. Go to repository Settings → Pages
2. Under "Source", select:
   - Source: **Deploy from a branch**
   - Branch: **gh-pages**
   - Folder: **/ (root)**
3. Click "Save"

The workflow will automatically create the `gh-pages` branch on first run.

### Manual Trigger

To trigger deployment manually:

1. Go to Actions tab
2. Select "Deploy Schema Docs" workflow
3. Click "Run workflow"
4. Select branch: main
5. Click "Run workflow"

### Verify Deployment

After the workflow completes:

1. Go to Settings → Pages
2. Check the published URL (e.g., `https://app-sre.github.io/qontract-schemas/`)
3. Visit the URL to view the schema documentation

### Troubleshooting

**Workflow fails with permission error:**
- Go to Settings → Actions → General
- Under "Workflow permissions", select "Read and write permissions"
- Check "Allow GitHub Actions to create and approve pull requests"
- Click "Save"

**Page shows 404:**
- Verify gh-pages branch exists
- Check that docs/ directory contains index.html, schemas.json, styles.css
- Wait a few minutes for GitHub Pages to update

**Documentation is outdated:**
- Check if workflow ran successfully in Actions tab
- Manually trigger workflow if needed
- Verify the commit triggered the workflow (check paths filter)

## Local Development

### Preview Changes

Before committing schema or generator changes:

\`\`\`bash
make generate-docs
cd docs && python -m http.server 8000
\`\`\`

Open http://localhost:8000 to preview.

### Test Without Deploying

Create a feature branch to test changes without triggering deployment:

\`\`\`bash
git checkout -b test-schema-changes
# Make changes
make generate-docs
# Test locally
git commit -m "test: schema changes"
# Push to feature branch (won't trigger deployment)
git push origin test-schema-changes
\`\`\`

Only merging to `main` triggers deployment.
```

- [ ] **Step 2: Commit deployment guide**

```bash
git add docs/superpowers/plans/DEPLOYMENT.md
git commit -m "docs: add GitHub Pages deployment instructions

- One-time GitHub Pages setup steps
- Manual workflow trigger guide
- Troubleshooting common issues
- Local development workflow

Assisted-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

- [ ] **Step 3: Push to main and verify workflow**

Run:
```bash
git push origin main
```

Go to GitHub repository → Actions tab:
- Verify "Deploy Schema Docs" workflow starts
- Wait for completion (should be green)
- Check for gh-pages branch creation

- [ ] **Step 4: Complete GitHub Pages setup**

Follow the instructions in `DEPLOYMENT.md` to enable GitHub Pages.

---

## Plan Complete

Plan written and saved to `docs/superpowers/plans/2026-06-08-schema-viewer.md`.

**Total Tasks:** 16  
**Total Steps:** ~100 bite-sized steps

All tasks follow TDD principles where applicable, include exact file paths, complete code implementations, and frequent commits. The plan is ready for execution.
