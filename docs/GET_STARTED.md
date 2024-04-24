<div align="center">

# Getting Started

</div>

In this document you can find all information to get started using the Horreum python library from scratch.

> **NOTE**: At the moment of writing, the `horreum` package is not yet accessible on PyPI. Consequently, the sole method 
> for installation involves constructing it from source and subsequently installing the generated `wheel`.

---
## Prerequisites

* Python environment, e.g., `pyenv` or `miniconda` with `poetry` dependency installed:
```bash
pip install --constraint=./dev-constraints.txt poetry
poetry --version
```

## Installation

Once all [prerequisites](#prerequisites) are satisfied, run the following commands.

First of all, generate the Horreum client: 

```bash
make generate
```

Then, simply build the _wheel_ by running:

```bash
poetry build
```

Now you can install the local build of `horreum` python client:

```bash
pip install dist/horreum-*.dev0-py3-none-any.whl --force-reinstall
```

## Usage

Horreum Python library leverages the auto-generated client using [Kiota](https://github.com/microsoft/kiota) tool to translate all REST requests
into python methods calls.

Right now Horreum library does not expose any specific high-level api, but it simply offers the Kiota generated client 
which is made available through the `HorreumClient.raw_client` property.

Check [Kiota python examples](https://github.com/microsoft/kiota-samples/tree/main/get-started/quickstart/python) to see
how to interact with a Kiota auto-generated Python client.

Here a very simple example:

```bash
>>> import asyncio

# Import the constructor function
>>> from horreum.horreum_client import new_horreum_client, HorreumCredentials

# Initialize the client
>>> client = await new_horreum_client(base_url="http://localhost:8080", credentials=HorreumCredentials(username=username, password=password))

# Call the api using the underlying raw client, in this case retrieve the Horreum server version
>>> await client.raw_client.api.config.version.get()
VersionInfo(additional_data={}, privacy_statement=None, start_timestamp=1710864862253, version='0.13.0')
```

The previous api call is equivalent to the following `cURL`:
```bash
curl --silent -X 'GET' 'http://localhost:8080/api/config/version' -H 'accept: application/json' | jq '.'
```

Other examples can be found in the [examples folder](../examples), for instance:

```bash
# Import Horreum Test model
>>> from horreum.raw_client.models.test import Test
>>> from horreum.raw_client.models.protected_type_access import ProtectedType_access

# Initialize the client
>>> client = await new_horreum_client(base_url="http://localhost:8080", username="..", password="..")

# Create new Horreum test
>>> t = Test(name="TestName", description="Simple test", owner="dev-team", access=ProtectedType_access.PUBLIC)
>>> created = await client.raw_client.api.test.post(t)
Test(additional_data={}, access=<ProtectedType_access.PUBLIC: 'PUBLIC'>, owner='dev-team', compare_url=None, datastore_id=1, description='Simple test', fingerprint_filter=None, fingerprint_labels=None, folder=None, id=12, name='TestName', notifications_enabled=True, timeline_function=None, timeline_labels=None, tokens=None, transformers=None)

# Delete the Horreum test
>>> await client.raw_client.api.test.by_id(12).delete()
```
