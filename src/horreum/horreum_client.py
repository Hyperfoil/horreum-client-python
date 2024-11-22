import base64
import logging
from importlib.metadata import version
from typing import Optional

import httpx
from kiota_abstractions.authentication import AuthenticationProvider, ApiKeyAuthenticationProvider, KeyLocation
from kiota_abstractions.authentication.access_token_provider import AccessTokenProvider
from kiota_abstractions.authentication.anonymous_authentication_provider import AnonymousAuthenticationProvider
from kiota_abstractions.authentication.base_bearer_token_authentication_provider import (
    BaseBearerTokenAuthenticationProvider)
from kiota_http.httpx_request_adapter import HttpxRequestAdapter
from kiota_http.kiota_client_factory import KiotaClientFactory

from .configs import HorreumCredentials, ClientConfiguration, AuthMethod
from .keycloak_access_provider import KeycloakAccessProvider
from .raw_client.horreum_raw_client import HorreumRawClient

DEFAULT_CONNECTION_TIMEOUT: int = 30
DEFAULT_REQUEST_TIMEOUT: int = 100

logger = logging.getLogger(__name__)


async def setup_auth_provider(base_url: str, username: str, password: str, http_client: httpx.AsyncClient = None,
                              verify: bool = True) -> AccessTokenProvider:
    # Use not authenticated client to fetch the auth mechanism
    auth_provider = AnonymousAuthenticationProvider()
    req_adapter = HttpxRequestAdapter(authentication_provider=auth_provider, http_client=http_client)
    req_adapter.base_url = base_url
    auth_client = HorreumRawClient(req_adapter)

    auth_config = await auth_client.api.config.keycloak.get()
    return KeycloakAccessProvider(auth_config, username, password, verify)


class HorreumClient:
    __base_url: str
    __credentials: Optional[HorreumCredentials]
    __client_config: Optional[ClientConfiguration]
    __http_client: httpx.AsyncClient

    # Raw client, this could be used to interact with the low-level api
    raw_client: HorreumRawClient
    # By default, set as anonymous authentication
    auth_provider: AuthenticationProvider = AnonymousAuthenticationProvider()

    def __init__(self, base_url: str, credentials: Optional[HorreumCredentials],
                 client_config: Optional[ClientConfiguration]):
        self.__base_url = base_url
        self.__credentials = credentials
        self.__client_config = client_config
        self.__auth_verify = client_config.auth_verify if client_config is not None else True

        if client_config and client_config.http_client and client_config.use_default_middlewares:
            self.__http_client = KiotaClientFactory.create_with_default_middleware(client=client_config.http_client,
                                                                                   options=client_config.options)
        else:
            self.__http_client = client_config.http_client if client_config else None

    async def setup(self):
        """
        Set up the authentication provider, based on the Horreum configuration, and the low-level horreum api client
        """

        if self.__credentials:
            if self.__credentials.apikey is not None and (
                    self.__client_config is None or self.__client_config.auth_method == AuthMethod.API_KEY):
                # API key authentication
                self.auth_provider = ApiKeyAuthenticationProvider(KeyLocation.Header, self.__credentials.apikey,
                                                                  "X-Horreum-API-Key")
                logger.info('Using API Key authentication')

            elif self.__credentials.username is not None:
                if self.__client_config is None or self.__client_config.auth_method == AuthMethod.BEARER:
                    # Bearer token authentication
                    access_provider = await setup_auth_provider(self.__base_url, self.__credentials.username,
                                                                self.__credentials.password, self.__http_client,
                                                                self.__auth_verify)
                    self.auth_provider = BaseBearerTokenAuthenticationProvider(access_provider)
                    logger.info('Using OIDC bearer token authentication')
                elif self.__client_config.auth_method == AuthMethod.BASIC:
                    # Basic authentication
                    basic = "Basic " + base64.b64encode(
                        (self.__credentials.username + ":" + self.__credentials.password).encode()).decode()
                    self.auth_provider = ApiKeyAuthenticationProvider(KeyLocation.Header, basic, "Authentication")
                    logger.info('Using Basic HTTP authentication')
            elif self.__credentials.password is not None:
                raise RuntimeError("provided password without username")

        if self.__http_client:
            req_adapter = HttpxRequestAdapter(authentication_provider=self.auth_provider,
                                              http_client=self.__http_client)
        else:
            # rely on the Kiota default is not provided by user
            req_adapter = HttpxRequestAdapter(authentication_provider=self.auth_provider)

        req_adapter.base_url = self.__base_url

        self.raw_client = HorreumRawClient(req_adapter)

    ##################
    # High-level API #
    ##################

    @staticmethod
    def version() -> str:
        return version("horreum")


async def new_horreum_client(base_url: str, credentials: Optional[HorreumCredentials] = None,
                             client_config: Optional[ClientConfiguration] = None) -> HorreumClient:
    """
    Initialize the horreum client
    :param base_url: horreum api base url
    :param credentials: horreum credentials in the form of username and pwd
    :param client_config: inner http client configuration
    :return: HorreumClient instance
    """
    client = HorreumClient(base_url, credentials=credentials, client_config=client_config)
    await client.setup()

    return client
