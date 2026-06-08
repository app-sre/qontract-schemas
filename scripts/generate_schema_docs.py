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
