import pytest
import anymarkup
from typing import Any, Dict
from jsonschema.exceptions import ValidationError

from utils import get_schema_object_validator

valid_sql_queries = [
    "select a from table_a;",
    "select analyze from table b;",
    "SELECT A FROM TABLE_A;",
    "select a from table /* let's order by Id */ order by id;",
    "select a /* comment */ from table /* comment 2 */ a;",
    "select a from ( select a,b from table_b );",
    "explain select a from table_a;",
    "explain analyze select a from table_a;"
]

not_valid_sql_queries = [
    "select * from table_a;",
    "SELECT * FROM TABLE_A;",
    "select a from table -- order by id order by id;",
    "select a from ( select * from table_b );",
    "select a from ( select /*comment*/* from table_b );",
    "explain analyze update table set a='b' where id=1;",
    "explain analyze insert table set a='b' where id=1;",
    "update table set a='b' where id=1;",
    "select /* comment */* from a;"
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

@pytest.fixture(scope='module')
def sql_validator(schemas):
    """ Gets the schema validator for the sql-query objects"""
    validator = get_schema_object_validator(
        schemas,
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
