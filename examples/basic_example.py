import asyncio
import json

from kiota_abstractions.base_request_configuration import RequestConfiguration

from horreum import new_horreum_client
from horreum.horreum_client import HorreumClient
from horreum.raw_client.models.extractor import Extractor
from horreum.raw_client.models.run import Run
from horreum.raw_client.models.schema import Schema
from horreum.raw_client.models.test import Test
from horreum.raw_client.models.transformer import Transformer
from horreum.raw_client.api.run.test.test_request_builder import TestRequestBuilder

base_url = "http://localhost:8080"
username = "user"
password = "secret"

cleanup_data = True


async def create_schema(client: HorreumClient, data_path: str) -> int:
    print(f"creating schema from {data_path}")
    schema_data = json.load(open(data_path), object_hook=lambda d: Schema(**d))
    print(schema_data)

    schema_id = await client.raw_client.api.schema.post(schema_data)
    assert schema_id > 0
    return schema_id


async def create_schema_transformers(client: HorreumClient, schema_id: int, data_path: str,
                                     extractors_data_path: str) -> int:
    print(f"creating transformer from {data_path}")
    transformer_data = json.load(open(data_path), object_hook=lambda d: Transformer(**d))
    print(transformer_data)

    print(f"creating extractors from {extractors_data_path}")
    extractors_data = json.load(open(extractors_data_path),
                                object_hook=lambda d: Extractor(**d))
    print(extractors_data)

    transformer_data.extractors = extractors_data

    transformer_id = await client.raw_client.api.schema.by_id_id(schema_id).transformers.post(transformer_data)
    assert transformer_id > 0
    return transformer_id


async def create_test(client: HorreumClient, data_path: str) -> Test:
    print(f"creating test from {data_path}")

    test_data = json.load(open(data_path), object_hook=lambda d: Test(**d))
    print(test_data)

    test = await client.raw_client.api.test.post(test_data)
    assert test.id > 0
    return test


async def set_test_transformers(client: HorreumClient, test_id: int, transformers: list[int]):
    await client.raw_client.api.test.by_id(test_id).transformers.post(transformers)


async def upload_run(client: HorreumClient, test_id: int, run_path: str, run_data_path: str):
    print(f"uploading run from {run_path}")

    run = json.load(open(run_path), object_hook=lambda d: Run(**d))
    run_data = json.load(open(run_data_path))
    run.data = json.dumps(run_data)
    print(run)

    query_params = TestRequestBuilder.TestRequestBuilderPostQueryParameters(test=str(test_id))
    config = RequestConfiguration(query_parameters=query_params)
    await client.raw_client.api.run.test.post(run, config)


async def setup_roadrunner_test(client: HorreumClient):
    print("creating roadrunner test")

    acme_benchmark_schema_id = await create_schema(client, "./data/acme_benchmark_schema.json")
    acme_horreum_schema_id = await create_schema(client, "./data/acme_horreum_schema.json")

    acme_transformers_id = await create_schema_transformers(client, acme_benchmark_schema_id,
                                                            "./data/acme_transformer.json",
                                                            "./data/acme_transformer_extractors.json")

    roadrunner_test = await create_test(client, "./data/roadrunner_test.json")
    await set_test_transformers(client, roadrunner_test.id, [acme_transformers_id])

    await upload_run(client, roadrunner_test.id, "./data/roadrunner_run.json", "./data/roadrunner_run_data.json")


async def delete_all(client: HorreumClient):
    """ cleanup all Horreum data """

    print("cleaning up tests")
    get_tests = await client.raw_client.api.test.get()
    for t in get_tests.tests:
        await client.raw_client.api.test.by_id(t.id).delete()

    get_tests = await client.raw_client.api.test.get()
    assert get_tests.count == 0

    print("cleaning up schemas")
    get_schemas = await client.raw_client.api.schema.get()
    for s in get_schemas.schemas:
        await client.raw_client.api.schema.by_id_id(s.id).delete()

    get_schemas = await client.raw_client.api.schema.get()
    assert get_schemas.count == 0


async def example():
    client = await new_horreum_client(base_url, username, password)

    if cleanup_data:
        await delete_all(client)

    await setup_roadrunner_test(client)

    # check data is properly injected in the server
    get_schemas = await client.raw_client.api.schema.get()
    assert get_schemas.count == 2

    get_tests = await client.raw_client.api.test.get()
    assert get_tests.count == 1

    get_runs = await client.raw_client.api.run.list_.get()
    assert get_runs.total == 1


if __name__ == '__main__':
    asyncio.run(example())
