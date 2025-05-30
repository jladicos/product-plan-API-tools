# ProductPlan API Client Makefile

# Default values (can be overridden)
ENDPOINT ?= ideas
OUTPUT ?= productplan_data.xlsx
PAGE ?= 1
PAGE_SIZE ?= 200
TOKEN_FILE ?= token.txt
ALL_PAGES ?= true

# Allow multiple filters
# Usage: make ideas FILTERS="name:Feature Request customer:Acme"
FILTERS ?=

# Base Docker command
DOCKER_CMD = docker run --rm -v $(CURDIR):/app productplan-api

# Help command
.PHONY: help
help:
	@echo "ProductPlan API Client"
	@echo ""
	@echo "Available commands:"
	@echo "  make help              - Show this help message"
	@echo "  make ideas             - Get ideas with team columns"
	@echo "  make teams             - Get all teams"
	@echo "  make all               - Get both ideas and teams"
	@echo "  make custom            - Run with custom parameters"
	@echo "  make build             - Build the Docker image"
	@echo ""
	@echo "Options (can be overridden):"
	@echo "  OUTPUT=filename.xlsx   - Set output filename (default: $(OUTPUT))"
	@echo "  PAGE=num               - Set page number (default: $(PAGE))"
	@echo "  PAGE_SIZE=num          - Set page size (default: $(PAGE_SIZE))"
	@echo "  TOKEN_FILE=file        - Set token file (default: $(TOKEN_FILE))"
	@echo "  ALL_PAGES=true/false   - Fetch all pages (default: $(ALL_PAGES))"
	@echo "  FILTERS=\"key1:value1 key2:value2\" - Add multiple filters"
	@echo ""
	@echo "Examples:"
	@echo "  make ideas OUTPUT=all_ideas.xlsx"
	@echo "  make ideas FILTERS=\"name:Feature Request channel:Sales\""
	@echo "  make teams ALL_PAGES=false PAGE=2"
	@echo "  make custom ENDPOINT=ideas OUTPUT=custom.xlsx ALL_PAGES=true"
	@echo ""
	@echo "Note: You can still use the direct Docker commands if needed:"
	@echo "  docker run --rm -v \$\$(pwd):/app productplan-api --endpoint ideas --all-pages --output output.xlsx"

# Build the Docker image
.PHONY: build
build:
	@echo "Building ProductPlan API Docker image..."
	docker build -t productplan-api .
	@echo "Docker image built successfully!"

# Process filters from space-separated key:value pairs
define process_filters
	$(if $(FILTERS), \
		$(foreach filter,$(FILTERS), \
			--filter $(shell echo $(filter) | cut -d: -f1) "$(shell echo $(filter) | cut -d: -f2-)" \
		) \
	)
endef

# Add --all-pages flag if ALL_PAGES is true
define all_pages_flag
	$(if $(filter true,$(ALL_PAGES)),--all-pages,)
endef

# Get ideas (with team columns by default)
.PHONY: ideas
ideas:
	@echo "Fetching ideas..."
	@$(DOCKER_CMD) \
		--endpoint ideas \
		--page $(PAGE) \
		--page-size $(PAGE_SIZE) \
		--token-file $(TOKEN_FILE) \
		--output $(OUTPUT) \
		$(call all_pages_flag) \
		$(call process_filters)
	@echo "Ideas saved to $(OUTPUT)"

# Get teams
.PHONY: teams
teams:
	@echo "Fetching teams..."
	@$(DOCKER_CMD) \
		--endpoint teams \
		--page $(PAGE) \
		--page-size $(PAGE_SIZE) \
		--token-file $(TOKEN_FILE) \
		--output $(OUTPUT) \
		$(call all_pages_flag) \
		$(call process_filters)
	@echo "Teams saved to $(OUTPUT)"

# Get both ideas and teams
.PHONY: all
all:
	@make ideas OUTPUT=ideas.xlsx
	@make teams OUTPUT=teams.xlsx
	@echo "Done! Files saved as ideas.xlsx and teams.xlsx"

# Custom command with all options specified on command line
.PHONY: custom
custom:
	@echo "Running custom command..."
	@$(DOCKER_CMD) \
		--endpoint $(ENDPOINT) \
		--page $(PAGE) \
		--page-size $(PAGE_SIZE) \
		--token-file $(TOKEN_FILE) \
		--output $(OUTPUT) \
		$(call all_pages_flag) \
		$(call process_filters)
	@echo "Data saved to $(OUTPUT)"

# Default target when running just 'make'
.DEFAULT_GOAL := help