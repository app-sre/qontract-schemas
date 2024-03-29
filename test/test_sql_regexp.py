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
    "explain analyze select a from table_a;",
    "SELECT a from table b where id ='3ec6f667-4083**';",
    """select a from table -- order by id
     order by id;""",
    "select\n  -- get things that appeared to be running on 2021-05-17\n  -- user/clount info\n  au.id as django_user_id,\n  ca.id as cloud_account_id,\n  aca.id as aws_cloud_account_id,\n  -- instance info\n  i.id as instance_id,\n  ai.id as aws_instance_id,\n  ai.ec2_instance_id as ec2_instance_id,\n  -- image info\n  mi.id as machine_image_id,\n  mi.name as machine_image_name,\n  mi.status as machine_image_status,\n  ami.id as aws_machine_image_id,\n  ami.ec2_ami_id as ec2_ami_id,\n  -- run info\n  r.id as run_id,\n  r.start_time as run_start_time\nfrom\n  auth_user au\n  join api_cloudaccount ca on au.id = ca.user_id\n  join api_awscloudaccount aca on aca.id = ca.object_id\n  join api_instance i on i.cloud_account_id = ca.id\n  join api_awsinstance ai on ai.id = i.object_id\n  join api_run r on r.instance_id = i.id\n  join api_machineimage mi on mi.id = r.machineimage_id\n  join api_awsmachineimage ami on ami.id = mi.object_id\nwhere\n  username = '6362142' -- the qe account used for longevity tests\n  username = '6362142'\n  AND r.start_time <= '2021-05-17 00:00:00'\n  AND coalesce(r.end_time, '2021-05-17 00:00:01') > '2021-05-17 00:00:00'\norder by\n  -- most recently started runs first\n  r.start_time desc;\n",
    "ANALYZE;",
    "analyze sometable;",
    "reindex index table;",
    "vacuum table;",
    "optimize table sometable;",
]

not_valid_sql_queries = [
    "select * from table_a;",
    "SELECT * FROM TABLE_A;",
    "select a from ( select * from table_b );",
    "select a from ( select /*comment*/* from table_b );",
    "explain analyze update table set a='b' where id=1;",
    "explain analyze insert table set a='b' where id=1;",
    "update table set a='b' where id=1;",
    "select /* comment */* from a;",
    "analyze; insert table set a='b';",
    "analyze table; insert table set a='b';",
    "reindex; insert table set a='b';",
    "analyze missingsemicolon",
    "analyze (select * from table);",
    "optimize table sometable; insert table set a='b'",
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
