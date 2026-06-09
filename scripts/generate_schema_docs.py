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

    # Extract nested properties for objects
    nested_properties = None
    if prop_type == "object" and "properties" in definition and not definition.get("$schemaRef"):
        nested_required = definition.get("required", [])
        nested_properties = []
        for nested_name, nested_def in definition["properties"].items():
            nested_properties.append(_parse_property(nested_name, nested_def, nested_required))

    result = {
        "name": name,
        "type": prop_type,
        "required": name in required_fields,
        "description": definition.get("description"),
        "constraints": constraints if constraints else {},
        "schemaRef": definition.get("$schemaRef"),
        "propertyPath": f".{name}"
    }

    if nested_properties is not None:
        result["nestedProperties"] = nested_properties

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
