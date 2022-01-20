import os
from typing import Any, Dict
import anymarkup
from jsonschema import RefResolver, Draft6Validator


def load_schemas(work_dir: str = "schemas") -> Dict[str, Any]:
    """ Function to load all schema files.
    It works like qontract-bundler, it stores all the schema files in a dictionary.
    The keys are the schema uris, and the values the schema specs.
    The same structure is used as a store paramenter in the jsonschema RefResolver.
    """
    schemas = {}
    for root, dirs, files in os.walk(work_dir, topdown=False):
        for name in files:
            file_path = os.path.join(root, name)
            data = anymarkup.parse_file(file_path)
            rel_path = file_path[len(work_dir):]
            schemas[rel_path] = data
    return schemas


def get_schema_object_validator(schema_ref: str) -> Draft6Validator:
    """ Function to get a Draft6Validator object for an object.
    It gets the schema definition from the store loaded in load_schemas and it
    has a resolver with a store pointing to the same structure.
    """
    store = load_schemas()
    resolver = RefResolver('', '', store=store)

    return Draft6Validator(
        store[schema_ref],
        resolver=resolver
    )
