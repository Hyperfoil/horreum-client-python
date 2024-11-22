from dataclasses import dataclass
from enum import Enum
from typing import Optional

import httpx
from kiota_abstractions.request_option import RequestOption


@dataclass(frozen=True)
class HorreumCredentials:
    username: str = None
    password: str = None
    apikey: str = None

class AuthMethod(Enum):
    BEARER = 1
    BASIC = 2
    API_KEY = 3

@dataclass
class ClientConfiguration:
    # inner http async client that will be used to perform raw requests
    http_client: Optional[httpx.AsyncClient] = None
    # if true, set default middleware on the provided client
    use_default_middlewares: bool = True
    # if set use these options for default middlewares
    options: Optional[dict[str, RequestOption]] = None
    # which authentication method to use
    auth_method: AuthMethod = AuthMethod.BEARER
    # SSL cert verification against the oidc provider
    auth_verify: bool = True
