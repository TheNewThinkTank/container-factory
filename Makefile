SHELL := /bin/bash

IMAGE ?= hello
TAG ?= local
PLATFORMS ?= linux/amd64
SECURITY_PYTHON ?= .venv-security/bin/python
REGISTRY_IMAGE ?= ghcr.io/$(shell printf '%s' "$(GITHUB_REPOSITORY_OWNER)" | tr '[:upper:]' '[:lower:]')/$(IMAGE)
DIGEST ?=

BUILD_STAMP = .build-$(IMAGE)-$(TAG)

.PHONY: help setup validate prepare-grype build sbom scan security test inspect sign verify clean

help:
	@echo "Targets:"
	@echo "  setup         Create security-policy Python environment"
	@echo "  validate      Validate image metadata"
	@echo "  prepare-grype Download/update the Grype vulnerability database"
	@echo "  build         Build IMAGE=$(IMAGE)"
	@echo "  sbom          Generate local SBOM for IMAGE=$(IMAGE)"
	@echo "  scan          Scan local IMAGE=$(IMAGE) (requires make build first)"
	@echo "  security      Build + prepare-grype + SBOM + scan"
	@echo "  test          Run unit tests"
	@echo "  inspect       Inspect REGISTRY_IMAGE=$(REGISTRY_IMAGE)"
	@echo "  sign          Sign REGISTRY_IMAGE@DIGEST"
	@echo "  verify        Verify REGISTRY_IMAGE@DIGEST"
	@echo "  clean         Remove generated SBOM/report files and build stamps"

setup:
	scripts/setup-security-tools.sh

validate:
	@set -e; \
	for image in images/*; do \
		if [ -f "$$image/metadata.yaml" ]; then \
			echo "Validating $$image/metadata.yaml"; \
			python3 scripts/validate-metadata.py "$$image/metadata.yaml"; \
		fi; \
	done

prepare-grype:
	scripts/prepare-grype.sh

$(BUILD_STAMP): $(wildcard images/$(IMAGE)/*)
	IMAGE=$(IMAGE) TAG=$(TAG) PLATFORMS=$(PLATFORMS) scripts/build-image.sh
	@touch "$(BUILD_STAMP)"

build: $(BUILD_STAMP)

sbom: $(BUILD_STAMP)
	IMAGE=$(IMAGE) TAG=$(TAG) scripts/generate-sbom.sh

scan: prepare-grype
	SECURITY_PYTHON=$(SECURITY_PYTHON) scripts/scan-image.sh $(IMAGE) $(TAG)

security: sbom scan

test:
	PYTHONPATH=src $(SECURITY_PYTHON) -m unittest discover -s tests -v

inspect:
	scripts/inspect-image-digest.sh "$(REGISTRY_IMAGE)"

sign:
	@test -n "$(DIGEST)" || (echo "DIGEST is required" >&2; exit 2)
	scripts/sign-image.sh "$(REGISTRY_IMAGE)@$(DIGEST)"

verify:
	@test -n "$(DIGEST)" || (echo "DIGEST is required" >&2; exit 2)
	scripts/verify-image.sh "$(REGISTRY_IMAGE)@$(DIGEST)"

clean:
	rm -rf sbom reports .build-*
