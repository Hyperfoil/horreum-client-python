import asyncio

import httpx

from horreum import new_horreum_client, ClientConfiguration

DEFAULT_CONNECTION_TIMEOUT: int = 30
DEFAULT_REQUEST_TIMEOUT: int = 100

base_url = "http://localhost:8080"
username = "user"
password = "secret"

expected_server_version = "0.13.0"
expected_n_schemas = 2
expected_n_tests = 1
enable_assertions = False


async def example():
    timeout = httpx.Timeout(DEFAULT_REQUEST_TIMEOUT, connect=DEFAULT_CONNECTION_TIMEOUT)
    http_client = httpx.AsyncClient(timeout=timeout, http2=True, verify=False)
    client = await new_horreum_client(base_url, client_config=ClientConfiguration(http_client=http_client))

    server_version = await client.raw_client.api.config.version.get()
    print(server_version)
    if enable_assertions:
        assert server_version.version == expected_server_version

    get_schemas = await client.raw_client.api.schema.get()
    print(get_schemas.count)
    if enable_assertions:
        assert get_schemas.count == expected_n_schemas

    get_tests = await client.raw_client.api.test.get()
    print(get_tests.count)
    if enable_assertions:
        assert get_tests.count == expected_n_tests


if __name__ == '__main__':
    asyncio.run(example())
