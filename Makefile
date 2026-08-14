SHELL := /bin/bash

IMAGE ?= hello
TAG ?= local
PLATFORMS ?= linux/amd64
SECURITY_PYTHON ?= .venv-security/bin/python

.PHONY: help setup validate prepare-grype build sbom scan security test clean

help:
	@echo "Targets:"
	@echo "  setup     Create security-policy Python environment"
	@echo "  validate  Validate image metadata"
	@echo "  build     Build IMAGE=$(IMAGE)"
	@echo "  sbom      Generate SBOM for IMAGE=$(IMAGE)"
	@echo "  scan      Scan IMAGE=$(IMAGE)"
	@echo "  security  Build + SBOM + scan"
	@echo "  test      Run security-policy unit tests"
	@echo "  clean     Remove generated SBOM/report files"

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

build:
	IMAGE=$(IMAGE) TAG=$(TAG) PLATFORMS=$(PLATFORMS) scripts/build-image.sh

sbom: build
	IMAGE=$(IMAGE) TAG=$(TAG) scripts/generate-sbom.sh

scan: build
	SECURITY_PYTHON=$(SECURITY_PYTHON) scripts/scan-image.sh $(IMAGE) $(TAG)

security: sbom scan

test:
	PYTHONPATH=src $(SECURITY_PYTHON) -m unittest discover -s tests -v

clean:
	rm -rf sbom reports
