#!/usr/bin/env python3
"""Generate static documentation site from qontract schemas."""

import os
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

    return {
        "name": name,
        "type": prop_type,
        "required": name in required_fields,
        "description": definition.get("description"),
        "constraints": constraints if constraints else {},
        "schemaRef": definition.get("$schemaRef"),
        "propertyPath": f".{name}"
    }


if __name__ == "__main__":
    # Entry point for CLI execution
    pass
