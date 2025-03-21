project_path = $(shell pwd)
config_path = $(project_path)/tests/data/configs
port = 8002
service := $(shell basename $(project_path))

REGISTRY_SERVER := $(REGISTRY_SERVER)
REGISTRY_USERNAME := $(REGISTRY_USERNAME)
REGISTRY_PASSWORD := $(REGISTRY_PASSWORD)
commit_sha := $(shell git rev-parse HEAD)
ref_name := $(shell git rev-parse --abbrev-ref HEAD)
IMAGE := $(REGISTRY_SERVER)\/docker\/$(service):$(ref_name)\.
NEW_IMAGE_TAG := $(REGISTRY_SERVER)/docker/$(service):$(ref_name).$(commit_sha)

ifeq ($(shell which zsh 2>/dev/null),)
	SHELL := /bin/bash
	if [ -f "$$HOME/.bashrc" ]; then \
		SHELLPROFILE := $$HOME/.bashrc; \
	else \
		echo ".bashrc doesn't exist, skipping..."; \
	fi
else
	SHELL := /bin/zsh
	SHELLPROFILE := $$HOME/.zshrc
endif

define get_tex_corver_deps
$(shell source $(SHELLPROFILE) && conda activate $(service) && poetry show | grep '^tex-corver' | cut -d ' ' -f1)
endef

.PHONY: list-tex-corver-deps
	@echo "$(call get_tex_corver_deps)" | tr ' ' '\n'

.PHONY: update-tex-corver-deps
update-tex-corver-deps:
	@source $(SHELLPROFILE) && \
	conda activate $(service) && \
	poetry update $(call get_tex_corver_deps)

.PHONY: _test
_test:
	CONFIG_PATH=$(config_path) pytest \
		-c $(project_path)/pyproject.toml \
		$(o) \
		$(project_path)/tests/$(p)


.PHONY: local-test
local-test:
	$(MAKE) _test p="$(p)" o="$(o)"

.PHONY: test
test: 
	$(MAKE) _test p="$(p)" o=" \
		-x \
		-s \
		-vvv \
		-p no:warnings \
		--strict-markers \
		--tb=short \
		--cov=src \
		--cov-branch \
		--cov-report=term-missing \
		--cov-fail-under=40 \
		$(o)"