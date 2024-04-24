# useful paths
MKFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
PROJECT_PATH := $(patsubst %/,%,$(dir $(MKFILE_PATH)))
PROJECT_BIN := $(PROJECT_PATH)/bin
PROJECT_DIST := $(PROJECT_PATH)/dist

OS_NAME := $(shell uname -s | tr A-Z a-z)
OS_ARCH := $(shell uname -m | tr A-Z a-z)

ifeq ($(OS_NAME),linux)
	OS_NAME = "linux"
endif
ifeq ($(OS_NAME),darwin)
	OS_NAME = "osx"
endif

ifeq ($(OS_ARCH),x86_64)
	OS_ARCH = x64
endif
ifneq ($(filter %86,$(OS_ARCH)),)
	OS_ARCH = x86
endif
ifneq ($(filter arm%,$(OS_ARCH)),)
	OS_ARCH = arm64
endif

# env variables
KIOTA_VERSION ?= "v1.13.0"
HORREUM_BRANCH ?= "master"
HORREUM_OPENAPI_PATH ?= "https://raw.githubusercontent.com/Hyperfoil/Horreum/${HORREUM_BRANCH}/docs/site/content/en/openapi/openapi.yaml"
GENERATED_CLIENT_PATH = "${PROJECT_PATH}/src/horreum/raw_client"
OPENAPI_PATH = "${PROJECT_PATH}/openapi"
OPENAPI_SPEC = "${OPENAPI_PATH}/openapi.yaml"

.PHONY: help
help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development

.PHONY: clean-bin
clean-bin: ## Clean external tools
	@rm -rf ${PROJECT_BIN}

.PHONY: clean
clean: ## Clean output directories
	@rm -rf ${PROJECT_DIST} ${GENERATED_CLIENT_PATH} ${OPENAPI_PATH}

.PHONY: kiota
kiota: ${PROJECT_BIN}/kiota ## Install kiota tool under ${PROJECT_PATH}/bin

${PROJECT_BIN}/kiota:
	@{\
		set -e ;\
		echo "installing kiota version ${KIOTA_VERSION}" ;\
		mkdir -p ${PROJECT_BIN}/kiota-installation ;\
		cd ${PROJECT_BIN}/kiota-installation ;\
		curl -sLO https://github.com/microsoft/kiota/releases/download/${KIOTA_VERSION}/${OS_NAME}-${OS_ARCH}.zip ;\
		unzip -o ${OS_NAME}-${OS_ARCH}.zip ;\
		mv kiota ${PROJECT_BIN}/ ;\
		rm -rf ${PROJECT_BIN}/kiota-installation ;\
	}

.PHONY: tools
tools: kiota ## Install external tools.

${OPENAPI_SPEC}:
	@{\
		set -e ;\
		mkdir -p ${OPENAPI_PATH} ;\
		echo "fetching openapi spec from ${HORREUM_OPENAPI_PATH}" ;\
		curl -sSfL -o ${OPENAPI_SPEC} ${HORREUM_OPENAPI_PATH} ;\
	}

.PHONY: generate
generate: tools ${OPENAPI_SPEC} ## Generate the Horreum client
	@{\
		set -e ;\
		${PROJECT_BIN}/kiota generate -l python -c HorreumRawClient -n raw_client -d ${OPENAPI_PATH}/openapi.yaml -o ${GENERATED_CLIENT_PATH} ;\
	}


##@ Example

.PHONY: run-basic-example
run-basic-example: ## Run basic example
	cd examples && python basic_example.py

.PHONY: run-read-only-example
run-read-only-example: ## Run read-only example
	cd examples && python read_only_example.py
