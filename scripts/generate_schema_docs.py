#!/usr/bin/env python3
"""Generate static documentation site from qontract schemas."""

import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import anymarkup


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


def parse_schema_file(file_path: str, relative_path: str) -> Optional[Dict[str, Any]]:
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
    version = str(schema.get("version", "unknown"))
    description = schema.get("description")
    required_fields = schema.get("required", [])

    # Parse properties
    properties = []
    schema_properties = schema.get("properties", {})

    for prop_name, prop_def in schema_properties.items():
        properties.append(_parse_property(prop_name, prop_def, required_fields))

    result = {
        "path": relative_path,
        "version": version,
        "description": description,
        "properties": properties,
        "dependencies": [],  # Populated later
        "referencedBy": []   # Populated later
    }

    schema_one_of = _parse_schema_one_of(schema, properties)
    if schema_one_of:
        exclusive = set()
        for branch in schema.get("oneOf", []):
            if isinstance(branch, dict):
                exclusive |= _branch_property_names(branch)
        properties = [
            p for p in properties
            if p["name"] not in exclusive or p["name"] in schema_one_of["commonPropertyNames"]
        ]
        result["schemaOneOf"] = schema_one_of
        result["properties"] = properties

    return result


def _is_required_only_branch(branch: Dict[str, Any]) -> bool:
    """Return True when a oneOf branch only specifies required fields."""
    if not isinstance(branch, dict):
        return False
    return set(branch.keys()).issubset({"required"}) and "required" in branch


def _is_ref_branch(branch: Dict[str, Any]) -> bool:
    """Return True when a oneOf branch is a schema reference alternative."""
    if not isinstance(branch, dict) or branch.get("properties"):
        return False
    if branch.get("$schemaRef"):
        return True
    ref = branch.get("$ref")
    if isinstance(ref, str) and ref.startswith("/") and ref.endswith(".yml"):
        return True
    return False


def _branch_discriminator(branch: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Detect a single-value enum/const discriminator on a oneOf branch."""
    props = branch.get("properties") or {}
    for field, definition in props.items():
        if not isinstance(definition, dict):
            continue
        enum_vals = definition.get("enum")
        if isinstance(enum_vals, list) and len(enum_vals) == 1:
            return {"field": field, "value": str(enum_vals[0])}
        if "const" in definition:
            return {"field": field, "value": str(definition["const"])}
    return None


def _branch_label(branch: Dict[str, Any], kind: str, index: int = 0) -> str:
    """Generate a human-readable label for a oneOf branch."""
    if kind == "variants":
        discriminator = _branch_discriminator(branch)
        if discriminator:
            return f"{discriminator['field']}: {discriminator['value']}"
    if kind == "required_sets":
        required = branch.get("required") or []
        if required:
            return " + ".join(required)
    required = branch.get("required") or []
    if required:
        return " + ".join(required)
    return f"Option {index + 1}"


def _detect_discriminator(
    branches: List[Dict[str, Any]],
    properties: Optional[Dict[str, Any]],
) -> Optional[str]:
    """Detect a discriminator property from const/enum values across branches."""
    if not properties or not branches:
        return None

    for prop_name in properties:
        values = set()
        all_have_const = True
        for branch in branches:
            branch_properties = branch.get("properties", {})
            if prop_name not in branch_properties:
                all_have_const = False
                break
            prop_def = branch_properties[prop_name]
            if "const" in prop_def:
                values.add(prop_def["const"])
            elif "enum" in prop_def and len(prop_def["enum"]) == 1:
                values.add(prop_def["enum"][0])
            else:
                all_have_const = False
                break
        if all_have_const and len(values) == len(branches):
            return prop_name

    return None


def _classify_one_of(
    branches: List[Dict[str, Any]],
    properties: Optional[Dict[str, Any]],
) -> str:
    """Classify the kind of oneOf constraint."""
    if all(_is_required_only_branch(branch) for branch in branches):
        return "required_sets"
    ref_count = sum(1 for branch in branches if _is_ref_branch(branch))
    if ref_count == len(branches):
        return "ref_alternatives"
    return "variants"


def _parse_one_of_branch(
    branch: Dict[str, Any],
    property_path: str,
    kind: str,
    properties: Optional[Dict[str, Any]],
    index: int = 0,
) -> Dict[str, Any]:
    """Parse a single oneOf branch into a normalized structure."""
    result: Dict[str, Any] = {
        "label": _branch_label(branch, kind, index),
        "discriminator": _branch_discriminator(branch) if kind == "variants" else None,
    }
    if kind in ("required_sets", "variants"):
        result["required"] = branch.get("required") or []
    schema_ref = branch.get("$schemaRef")
    if not schema_ref and isinstance(branch.get("$ref"), str):
        ref = branch["$ref"]
        if ref.startswith("/") and ref.endswith(".yml"):
            schema_ref = ref
    result["schemaRef"] = schema_ref
    result["inline"] = bool(branch.get("properties") and not branch.get("$schemaRef"))
    if branch.get("properties") and not branch.get("$schemaRef"):
        nested_required = branch.get("required") or []
        result["properties"] = [
            _parse_property(name, definition, nested_required, property_path)
            for name, definition in branch["properties"].items()
        ]
    else:
        result["properties"] = None
    return result


def _parse_one_of(definition: Dict[str, Any], property_path: str) -> Optional[Dict[str, Any]]:
    """Parse oneOf constraints from a schema definition."""
    one_of = definition.get("oneOf")
    if not one_of or not isinstance(one_of, list):
        return None

    properties = definition.get("properties")
    kind = _classify_one_of(one_of, properties)
    branches = [
        _parse_one_of_branch(branch, property_path, kind, properties, index)
        for index, branch in enumerate(one_of)
    ]

    return {
        "kind": kind,
        "branches": branches,
        "propertyPath": property_path,
    }


def _branch_property_names(branch: Dict[str, Any]) -> set:
    """Return property names defined on a oneOf branch."""
    return set((branch.get("properties") or {}).keys())


def _parse_schema_one_of(
    raw_schema: Dict[str, Any],
    properties: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Parse schema-root oneOf into variant metadata and property splits."""
    branches_raw = raw_schema.get("oneOf")
    if not isinstance(branches_raw, list) or not branches_raw:
        return None

    schema_properties = raw_schema.get("properties")
    branches = [
        _parse_one_of_branch(branch, "", "variants", schema_properties, index)
        for index, branch in enumerate(branches_raw)
        if isinstance(branch, dict)
    ]
    if not branches:
        return None

    exclusive = set()
    for branch in branches_raw:
        if isinstance(branch, dict):
            exclusive |= _branch_property_names(branch)

    common_names: List[str] = []
    shared_optional_names: List[str] = []
    root_required = raw_schema.get("required") or []

    for prop in properties:
        name = prop["name"]
        if name not in exclusive:
            continue
        if name in root_required:
            common_names.append(name)

    for prop in properties:
        name = prop["name"]
        if name in exclusive and name not in common_names:
            shared_optional_names.append(name)

    return {
        "kind": "variants",
        "branches": branches,
        "commonPropertyNames": common_names,
        "sharedOptionalPropertyNames": shared_optional_names,
    }


def _resolve_property_type(definition: Dict[str, Any]) -> str:
    """Resolve the display type for a schema property definition."""
    if "$schemaRef" in definition:
        return "object (ref)"
    if "enum" in definition:
        return "enum"
    if "type" in definition:
        return definition["type"]
    if "properties" in definition:
        return "object"
    return "unknown"


def _parse_property(
    name: str,
    definition: Dict[str, Any],
    required_fields: List[str],
    path_prefix: str = "",
) -> Dict[str, Any]:
    """Parse a single property definition."""
    property_path = f"{path_prefix}.{name}" if path_prefix else f".{name}"
    prop_type = _resolve_property_type(definition)

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

    # Extract nested properties for inline objects and array item objects
    nested_properties = None
    nested_from_array = False
    items_one_of = None

    if not definition.get("$schemaRef") and "properties" in definition:
        nested_required = definition.get("required", [])
        nested_properties = []
        for nested_name, nested_def in definition["properties"].items():
            nested_properties.append(
                _parse_property(nested_name, nested_def, nested_required, property_path)
            )
    elif prop_type == "array" and "items" in definition:
        items_def = definition["items"]
        item_path = f"{property_path}[]"
        if isinstance(items_def, dict) and not items_def.get("$schemaRef") and "properties" in items_def:
            nested_required = items_def.get("required", [])
            nested_properties = []
            for nested_name, nested_def in items_def["properties"].items():
                nested_properties.append(
                    _parse_property(nested_name, nested_def, nested_required, item_path)
                )
            nested_from_array = True
            if "oneOf" in items_def:
                items_one_of = _parse_one_of(items_def, item_path)
        elif isinstance(items_def, dict) and "oneOf" in items_def:
            items_one_of = _parse_one_of(items_def, item_path)

    display_type = prop_type
    if nested_from_array and nested_properties:
        display_type = "array[object]"

    result = {
        "name": name,
        "type": display_type,
        "required": name in required_fields,
        "description": definition.get("description"),
        "constraints": constraints if constraints else {},
        "schemaRef": definition.get("$schemaRef"),
        "propertyPath": property_path,
    }

    if nested_properties is not None:
        result["nestedProperties"] = nested_properties
        result["nestedCount"] = len(nested_properties)

    one_of = _parse_one_of(definition, property_path)
    if one_of:
        result["oneOf"] = one_of
    elif items_one_of:
        result["oneOf"] = items_one_of

    return result


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

    def walk_properties(props: Dict[str, Any], path_prefix: str = "", in_array: bool = False):
        """Recursively walk properties to find $schemaRef."""
        for prop_name, prop_def in props.items():
            current_path = f"{path_prefix}.{prop_name}"

            # Skip if prop_def is not a dict
            if not isinstance(prop_def, dict):
                continue

            # Check if this property is a reference
            if "$schemaRef" in prop_def:
                target = prop_def["$schemaRef"]
                # Only process if target is a string
                if isinstance(target, str):
                    # Normalize path: remove leading slash
                    if target.startswith("/"):
                        target = target[1:]

                    # Calculate nesting level (count dots in path)
                    nesting_level = current_path.count(".")

                    dependencies.append({
                        "propertyPath": current_path,
                        "targetSchema": target,
                        "isArray": in_array,
                        "isNested": nesting_level >= 3
                    })

            # Recurse into nested objects
            if prop_def.get("type") == "object" and "properties" in prop_def:
                walk_properties(prop_def["properties"], current_path, in_array)

            # Recurse into array items
            if prop_def.get("type") == "array" and "items" in prop_def:
                items = prop_def["items"]
                if isinstance(items, dict):
                    # Check if items itself is a reference
                    if "$schemaRef" in items:
                        target = items["$schemaRef"]
                        # Only process if target is a string
                        if isinstance(target, str):
                            if target.startswith("/"):
                                target = target[1:]

                            nesting_level = current_path.count(".")

                            dependencies.append({
                                "propertyPath": current_path + "[]",
                                "targetSchema": target,
                                "isArray": True,
                                "isNested": nesting_level >= 3
                            })
                    # Or recurse into object properties within array items
                    elif items.get("type") == "object" and "properties" in items:
                        walk_properties(items["properties"], current_path + "[]", True)

    walk_properties(properties)

    return dependencies


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

    # 2. Parse each schema and keep raw schemas for dependency extraction
    schemas = {}
    raw_schemas = {}
    skipped = []

    for relative_path in schema_files:
        full_path = os.path.join(schemas_dir, relative_path)

        # Parse raw schema first
        try:
            raw_schema = anymarkup.parse_file(full_path)
            raw_schemas[relative_path] = raw_schema
        except Exception as e:
            print(f"Warning: Failed to parse {relative_path}: {e}")
            skipped.append(relative_path)
            continue

        # Then parse into normalized format
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

    # 3. Extract dependencies for each schema from raw schemas
    for schema_path, raw_schema in raw_schemas.items():
        if schema_path in schemas:
            dependencies = extract_dependencies(raw_schema, schema_path)
            schemas[schema_path]["dependencies"] = dependencies

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
