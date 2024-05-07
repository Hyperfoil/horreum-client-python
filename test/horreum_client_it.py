import httpx
import pytest
from kiota_abstractions.api_error import APIError
from kiota_abstractions.authentication import BaseBearerTokenAuthenticationProvider
from kiota_abstractions.base_request_configuration import RequestConfiguration
from kiota_abstractions.headers_collection import HeadersCollection
from kiota_abstractions.method import Method
from kiota_abstractions.request_information import RequestInformation

from horreum import HorreumCredentials, ClientConfiguration
from horreum.horreum_client import new_horreum_client, HorreumClient
from horreum.raw_client.api.test.test_request_builder import TestRequestBuilder
from horreum.raw_client.models.protected_type_access import ProtectedType_access
from horreum.raw_client.models.test import Test

DEFAULT_CONNECTION_TIMEOUT: int = 30
DEFAULT_REQUEST_TIMEOUT: int = 100

USERNAME = "user"
PASSWORD = "secret"


@pytest.fixture()
async def anonymous_client_without_check() -> HorreumClient:
    print("Setting up anonymous client")
    return await new_horreum_client(base_url="http://localhost:8080")


@pytest.fixture()
async def anonymous_client() -> HorreumClient:
    print("Setting up anonymous client")
    client = await new_horreum_client(base_url="http://localhost:8080")
    try:
        await client.raw_client.api.config.version.get()
    except httpx.ConnectError:
        pytest.fail("Unable to fetch Horreum version, is Horreum running in the background?")
    return client


@pytest.fixture()
async def authenticated_client() -> HorreumClient:
    print("Setting up authenticated client")
    client = await new_horreum_client(base_url="http://localhost:8080",
                                      credentials=HorreumCredentials(username=USERNAME, password=PASSWORD))
    try:
        await client.raw_client.api.config.version.get()
    except httpx.ConnectError:
        pytest.fail("Unable to fetch Horreum version, is Horreum running in the background?")
    return client


@pytest.fixture()
async def custom_authenticated_client() -> HorreumClient:
    print("Setting up custom authenticated client")
    timeout = httpx.Timeout(DEFAULT_REQUEST_TIMEOUT, connect=DEFAULT_CONNECTION_TIMEOUT)
    client = await new_horreum_client(base_url="http://localhost:8080",
                                      credentials=HorreumCredentials(username=USERNAME, password=PASSWORD),
                                      client_config=ClientConfiguration(
                                          http_client=httpx.AsyncClient(timeout=timeout, http2=True, verify=False)))
    try:
        await client.raw_client.api.config.version.get()
    except httpx.ConnectError:
        pytest.fail("Unable to fetch Horreum version, is Horreum running in the background?")
    return client


@pytest.mark.asyncio
async def test_check_server_version(anonymous_client: HorreumClient):
    version = await anonymous_client.raw_client.api.config.version.get()
    assert version.version != ""
    assert version.start_timestamp != ""


@pytest.mark.asyncio
async def test_check_missing_token(anonymous_client: HorreumClient):
    req = RequestInformation(Method("GET"), "/api/")
    await anonymous_client.auth_provider.authenticate_request(req)
    assert len(req.headers.get(BaseBearerTokenAuthenticationProvider.AUTHORIZATION_HEADER)) == 0


@pytest.mark.asyncio
async def test_check_auth_token(authenticated_client: HorreumClient):
    req = RequestInformation(Method("GET"), "/api/")
    await authenticated_client.auth_provider.authenticate_request(req)
    assert len(req.headers.get(BaseBearerTokenAuthenticationProvider.AUTHORIZATION_HEADER)) == 1
    assert req.headers.get(BaseBearerTokenAuthenticationProvider.AUTHORIZATION_HEADER).pop().startswith("Bearer")


@pytest.mark.asyncio
async def test_missing_username_with_password():
    with pytest.raises(RuntimeError) as ex:
        await new_horreum_client(base_url="http://localhost:8080", credentials=HorreumCredentials(password=PASSWORD))
    assert str(ex.value) == "providing password without username, have you missed something?"


@pytest.mark.asyncio
async def test_check_no_tests(authenticated_client: HorreumClient):
    query_params = TestRequestBuilder.TestRequestBuilderGetQueryParameters(limit=1, page=0)
    config = RequestConfiguration(query_parameters=query_params, headers=HeadersCollection())
    assert (await authenticated_client.raw_client.api.test.get(config)).count == 0


@pytest.mark.asyncio
async def test_check_create_test(custom_authenticated_client: HorreumClient):
    # Create new test
    t = Test(name="TestName", description="Simple test", owner="dev-team", access=ProtectedType_access.PUBLIC)
    created = await custom_authenticated_client.raw_client.api.test.post(t)
    assert created is not None
    assert (await custom_authenticated_client.raw_client.api.test.get()).count == 1

    # TODO: we could automate setup/teardown process
    # Delete test
    await custom_authenticated_client.raw_client.api.test.by_id(created.id).delete()
    assert (await custom_authenticated_client.raw_client.api.test.get()).count == 0


@pytest.mark.asyncio
async def test_create_test_unauthorized(anonymous_client: HorreumClient):
    # Create new test
    t = Test(name="TestName", description="Simple test", owner="dev-team", access=ProtectedType_access.PUBLIC)
    with pytest.raises(APIError) as ex:
        await anonymous_client.raw_client.api.test.post(t)
    assert ex.value.response_status_code == 401
    assert ex.value.message == ("The server returned an unexpected status code and no error class is registered "
                                "for this code 401")

    assert (await anonymous_client.raw_client.api.test.get()).count == 0


@pytest.mark.asyncio
async def test_get_test_not_found(anonymous_client: HorreumClient):
    with pytest.raises(APIError) as ex:
        await anonymous_client.raw_client.api.test.by_id(999).get()
    assert ex.value.response_status_code == 404
    assert ex.value.message == ("The server returned an unexpected status code and no error class is registered "
                                "for this code 404")
