from dataclasses import dataclass
from typing import Optional

import httpx
from kiota_abstractions.request_option import RequestOption


@dataclass(frozen=True)
class HorreumCredentials:
    username: str = None
    password: str = None


@dataclass
class ClientConfiguration:
    # inner http async client that will be used to perform raw requests
    http_client: Optional[httpx.AsyncClient] = None
    # if true, set default middleware on the provided client
    use_default_middlewares: bool = True
    # if set use these options for default middlewares
    options: Optional[dict[str, RequestOption]] = None
