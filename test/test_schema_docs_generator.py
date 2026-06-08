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
