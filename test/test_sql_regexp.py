import pytest
import anymarkup
from typing import Any, Dict
from jsonschema.exceptions import ValidationError

from utils import get_schema_object_validator

valid_sql_queries = [
    "select a from table_a;",
    "SELECT A FROM TABLE_A;",
    "select a from table order by id;",
    "select a from table order by id;",
    "select a from ( select a,b from table_b );",
    "explain select a from table_a;"
]

not_valid_sql_queries = [
    "select * from table_a",
    "SELECT * FROM TABLE_A",
    "select a from ( select * from table_b )",
    "explain analyze select a from table b"
]

def new_query_spec(query: str) -> Dict[str, Any]:
    return {
        "$schema": "/app-interface/app-interface-sql-query-1.yml",
        "labels": {},
        "name": "query",
        "namespace": {
            "$ref": "namespace.yaml"
        },
        "identifier": "query",
        "output": "stdout",
        "query": query,
    }

@pytest.fixture(scope='session')
def sql_validator():
    """ Gets the schema validator for the sql-query objects"""
    validator = get_schema_object_validator(
        "/app-interface/app-interface-sql-query-1.yml"
    )
    return validator

@pytest.mark.parametrize("query", valid_sql_queries)
def test_valid_sql_queries(sql_validator, query):
    sql_validator.validate(new_query_spec(query))


@pytest.mark.parametrize("query", not_valid_sql_queries)
def test_not_valid_sql_queries_raise_validation_error(sql_validator, query):
    with pytest.raises(ValidationError):
        sql_validator.validate(new_query_spec(query))
