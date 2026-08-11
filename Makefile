SHELL := /bin/bash

IMAGE ?= hello
TAG ?= local
PLATFORMS ?= linux/amd64

.PHONY: help validate build sbom scan security clean

help:
	@echo "Targets:"
	@echo "  validate  Validate image metadata"
	@echo "  build     Build IMAGE=$(IMAGE)"
	@echo "  sbom      Generate SBOM for IMAGE=$(IMAGE)"
	@echo "  scan      Scan IMAGE=$(IMAGE)"
	@echo "  security  Build + SBOM + scan"
	@echo "  clean     Remove generated SBOM files"

validate:
	python3 scripts/validate-metadata.py

build:
	IMAGE=$(IMAGE) TAG=$(TAG) PLATFORMS=$(PLATFORMS) scripts/build-image.sh

sbom: build
	IMAGE=$(IMAGE) TAG=$(TAG) scripts/generate-sbom.sh

scan: build
	IMAGE=$(IMAGE) TAG=$(TAG) scripts/scan-image.sh

security: sbom scan

clean:
	rm -rf sbom
