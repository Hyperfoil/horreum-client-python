import asyncio
import json

import httpx
from kiota_abstractions.base_request_configuration import RequestConfiguration

from horreum import new_horreum_client, ClientConfiguration, AuthMethod, HorreumCredentials
from horreum.raw_client.api.run.test.test_request_builder import TestRequestBuilder
from horreum.raw_client.models.extractor import Extractor
from horreum.raw_client.models.run import Run
from horreum.raw_client.models.schema import Schema
from horreum.raw_client.models.test import Test
from horreum.raw_client.models.transformer import Transformer

DEFAULT_CONNECTION_TIMEOUT: int = 30
DEFAULT_REQUEST_TIMEOUT: int = 100

base_url = "http://localhost:8080"
# follow https://horreum.hyperfoil.io/docs/tasks/api-keys/#api-key-creation
api_key = "<REPLACE_WITH_API_KEY>"


async def example():
    timeout = httpx.Timeout(DEFAULT_REQUEST_TIMEOUT, connect=DEFAULT_CONNECTION_TIMEOUT)
    http_client = httpx.AsyncClient(timeout=timeout, http2=False, verify=False)
    client = await new_horreum_client(
        base_url,
        credentials=HorreumCredentials(
            apikey=api_key
        ),
        client_config=ClientConfiguration(
            http_client=http_client,
            auth_method=AuthMethod.API_KEY
        )
    )

    server_version = await client.raw_client.api.config.version.get()
    print(server_version)

    # create the schema
    schema_data = json.load(open("./data/acme_benchmark_schema.json"), object_hook=lambda d: Schema(**d))
    schema_id = await client.raw_client.api.schema.post(schema_data)

    # create transformers
    transformer_data = json.load(open("./data/acme_transformer.json"), object_hook=lambda d: Transformer(**d))
    extractors_data = json.load(open("./data/acme_transformer_extractors.json"),
                                object_hook=lambda d: Extractor(**d))
    transformer_data.extractors = extractors_data
    transformer_id = await client.raw_client.api.schema.by_id(schema_id).transformers.post(transformer_data)

    # create the test
    test_data = json.load(open("./data/roadrunner_test.json"), object_hook=lambda d: Test(**d))
    test = await client.raw_client.api.test.post(test_data)
    await client.raw_client.api.test.by_id(test.id).transformers.post([transformer_id])

    # upload the run
    run = json.load(open("./data/roadrunner_run.json"), object_hook=lambda d: Run(**d))
    run_data = json.load(open("./data/roadrunner_run_data.json"))
    run.data = json.dumps(run_data)
    query_params = TestRequestBuilder.TestRequestBuilderPostQueryParameters(test=str(test.id))
    config = RequestConfiguration(query_parameters=query_params)
    await client.raw_client.api.run.test.post(run, config)


if __name__ == '__main__':
    asyncio.run(example())
