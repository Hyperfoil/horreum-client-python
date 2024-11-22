from typing import Dict, Any

from keycloak import KeycloakOpenID
from kiota_abstractions.authentication import AllowedHostsValidator
from kiota_abstractions.authentication.access_token_provider import AccessTokenProvider

from .raw_client.models.keycloak_config import KeycloakConfig


class KeycloakAccessProvider(AccessTokenProvider):
    config: KeycloakConfig
    username: str
    password: str

    def __init__(self, config: KeycloakConfig, username: str, password: str, verify: bool = True):
        super()
        self.config = config
        self.username = username
        self.password = password
        self.keycloak_openid = KeycloakOpenID(
            server_url=config.url,
            client_id=config.client_id,
            realm_name=config.realm,
            verify=verify
        )

    async def get_authorization_token(self, uri: str, additional_authentication_context: Dict[str, Any] = {}) -> str:
        return self.keycloak_openid.token(username=self.username, password=self.password)["access_token"]

    def get_allowed_hosts_validator(self) -> AllowedHostsValidator:
        return AllowedHostsValidator(allowed_hosts=[])
