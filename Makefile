# ProductPlan API Client Makefile

# Default values (can be overridden)
ENDPOINT ?= ideas
OUTPUT ?= files/productplan_data.xlsx
PAGE ?= 1
PAGE_SIZE ?= 200
ALL_PAGES ?= true
LOCATION_STATUS ?= not_archived
OBJECTIVE_STATUS ?= active
OUTPUT_FORMAT ?= excel
OUTPUT_TYPE ?= auto

# Support lowercase variable names for convenience
ifdef output
OUTPUT := $(output)
endif
ifdef page
PAGE := $(page)
endif
ifdef page_size
PAGE_SIZE := $(page_size)
endif
ifdef all_pages
ALL_PAGES := $(all_pages)
endif
ifdef objective_status
OBJECTIVE_STATUS := $(objective_status)
endif
ifdef location_status
LOCATION_STATUS := $(location_status)
endif
ifdef output_format
OUTPUT_FORMAT := $(output_format)
endif
ifdef output-format
OUTPUT_FORMAT := $(output-format)
endif
ifdef output_type
OUTPUT_TYPE := $(output_type)
endif
ifdef output-type
OUTPUT_TYPE := $(output-type)
endif

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
	@echo "  make build             - Build the Docker image"
	@echo "  make test              - Run mocked unit and integration tests"
	@echo "  make test-smoke        - Run smoke tests (requires env/.env, hits real API)"
	@echo "  make test-all          - Run all tests (mocked + smoke)"
	@echo ""
	@echo "Data fetching commands:"
	@echo "  make ideas             - Get ideas with team columns"
	@echo "  make teams             - Get all teams"
	@echo "  make idea-forms        - Get idea forms"
	@echo "  make okrs              - Get objectives and key results"
	@echo "  make objectivemap      - Get objective relationship mapping"
	@echo "  make all               - Get ideas, teams, idea forms, and OKRs"
	@echo "  make custom            - Run with custom parameters"
	@echo ""
	@echo "SLA tracking commands:"
	@echo "  make sla-init          - Initialize SLA tracking spreadsheet (default: files/sla_tracking.xlsx)"
	@echo "  make sla-update        - Update SLA tracking spreadsheet with recent changes"
	@echo ""
	@echo "Options (can be overridden - uppercase or lowercase):"
	@echo "  OUTPUT=filename.xlsx   - Set output filename (default: files/productplan_data.xlsx)"
	@echo "  PAGE=num               - Set page number (default: $(PAGE))"
	@echo "  PAGE_SIZE=num          - Set page size (default: $(PAGE_SIZE))"
	@echo "  ALL_PAGES=true/false   - Fetch all pages (default: $(ALL_PAGES))"
	@echo "  LOCATION_STATUS=status - Filter ideas by location status (default: $(LOCATION_STATUS))"
	@echo "                           Options: all, visible, hidden, archived, not_archived"
	@echo "  OBJECTIVE_STATUS=status - Filter objectives by status (default: $(OBJECTIVE_STATUS))"
	@echo "                            Options: active, all"
	@echo "  OUTPUT_FORMAT=format    - Output format (default: $(OUTPUT_FORMAT))"
	@echo "                            Options: excel, markdown, javascript"
	@echo "  OUTPUT_TYPE=type        - SLA storage type (default: $(OUTPUT_TYPE))"
	@echo "                            Options: auto (Google Sheets if configured, else Excel),"
	@echo "                                     excel (force Excel), sheets (force Google Sheets)"
	@echo "  FILTERS=\"key1:value1 key2:value2\" - Add multiple filters"
	@echo ""
	@echo "Note: Both uppercase (OUTPUT=) and lowercase (output=) work for convenience"
	@echo "Note: API token is loaded from env/.env (PRODUCTPLAN_API_TOKEN)"
	@echo ""
	@echo "Examples:"
	@echo "  make ideas OUTPUT=files/all_ideas.xlsx"
	@echo "  make ideas FILTERS=\"name:Feature Request channel:Sales\""
	@echo "  make ideas LOCATION_STATUS=visible"
	@echo "  make ideas LOCATION_STATUS=all"
	@echo "  make teams ALL_PAGES=false PAGE=2"
	@echo "  make idea-forms OUTPUT=files/forms.xlsx"
	@echo "  make okrs output=files/objectives.xlsx"
	@echo "  make okrs objective_status=all output=files/all_objectives.xlsx"
	@echo "  make okrs output-format=markdown"
	@echo "  make okrs output_format=markdown output=files/my_objectives.md"
	@echo "  make objectivemap output=files/objective_mapping.xlsx"
	@echo "  make objectivemap output_format=javascript output=files/objectives.js"
	@echo "  make sla-init                          # Auto-detect (Google Sheets or Excel)"
	@echo "  make sla-init OUTPUT=files/custom_sla.xlsx"
	@echo "  make sla-init OUTPUT_TYPE=excel        # Force Excel output"
	@echo "  make sla-init OUTPUT_TYPE=sheets       # Force Google Sheets output"
	@echo "  make sla-update"
	@echo "  make sla-update OUTPUT_TYPE=excel      # Update Excel file"
	@echo "  make custom ENDPOINT=okrs output=files/custom_okrs.xlsx objective_status=active"
	@echo ""
	@echo "Note: You can still use the direct Docker commands if needed:"
	@echo "  docker run --rm -v \$\$(pwd):/app productplan-api --endpoint ideas --all-pages --output output.xlsx"

# Build the Docker image
.PHONY: build
build:
	@echo "Building ProductPlan API Docker image..."
	docker build -t productplan-api .
	@echo "Docker image built successfully!"

# Run mocked unit and integration tests
.PHONY: test
test:
	@echo "Running mocked tests..."
	docker run --rm -v $(CURDIR):/app --entrypoint pytest productplan-api tests/ -v --ignore=tests/smoke
	@echo "Tests completed!"

# Run smoke tests (requires env/.env and hits real API)
.PHONY: test-smoke
test-smoke:
	@echo "Running smoke tests against real ProductPlan API..."
	@echo "Note: This requires a valid env/.env file with PRODUCTPLAN_API_TOKEN and will make real API calls."
	docker run --rm -v $(CURDIR):/app --entrypoint pytest productplan-api tests/smoke/ -v
	@echo "Smoke tests completed!"

# Run all tests (mocked + smoke)
.PHONY: test-all
test-all:
	@make test
	@make test-smoke

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
		--output $(OUTPUT) \
		--location-status $(LOCATION_STATUS) \
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
		--output $(OUTPUT) \
		$(call all_pages_flag) \
		$(call process_filters)
	@echo "Teams saved to $(OUTPUT)"

# Get idea forms
.PHONY: idea-forms
idea-forms:
	@echo "Fetching idea forms..."
	@$(DOCKER_CMD) \
		--endpoint idea-forms \
		--page $(PAGE) \
		--page-size $(PAGE_SIZE) \
		--output $(OUTPUT) \
		$(call all_pages_flag) \
		$(call process_filters)
	@echo "Idea forms saved to $(OUTPUT)"

# Get objectives and key results (OKRs)
.PHONY: okrs
okrs:
	@echo "Fetching objectives and key results..."
	$(eval FINAL_OUTPUT := $(if $(and $(filter markdown,$(OUTPUT_FORMAT)),$(filter files/productplan_data.xlsx,$(OUTPUT))),files/okrs.md,$(OUTPUT)))
	@$(DOCKER_CMD) \
		--endpoint okrs \
		--page $(PAGE) \
		--page-size $(PAGE_SIZE) \
		--output $(FINAL_OUTPUT) \
		--objective-status $(OBJECTIVE_STATUS) \
		--output-format $(OUTPUT_FORMAT) \
		$(call all_pages_flag) \
		$(call process_filters)
	@echo "OKRs saved to $(FINAL_OUTPUT)"

# Get objective relationship mapping
.PHONY: objectivemap
objectivemap:
	@echo "Fetching objective relationship mapping..."
	@$(DOCKER_CMD) \
		--endpoint objectivemap \
		--page $(PAGE) \
		--page-size $(PAGE_SIZE) \
		--output $(OUTPUT) \
		--objective-status $(OBJECTIVE_STATUS) \
		--output-format $(OUTPUT_FORMAT) \
		$(call all_pages_flag) \
		$(call process_filters)
	@echo "Objective mapping saved to $(OUTPUT)"

# Initialize SLA tracking spreadsheet
.PHONY: sla-init
sla-init:
	$(eval SLA_OUTPUT := $(if $(filter files/productplan_data.xlsx,$(OUTPUT)),files/sla_tracking.xlsx,$(OUTPUT)))
	@echo "Initializing SLA tracking spreadsheet..."
	@$(DOCKER_CMD) \
		--endpoint sla-init \
		--output $(SLA_OUTPUT) \
		--output-type $(OUTPUT_TYPE)

# Update SLA tracking spreadsheet (daily incremental updates)
.PHONY: sla-update
sla-update:
	$(eval SLA_OUTPUT := $(if $(filter files/productplan_data.xlsx,$(OUTPUT)),files/sla_tracking.xlsx,$(OUTPUT)))
	@echo "Updating SLA tracking spreadsheet..."
	@$(DOCKER_CMD) \
		--endpoint sla-update \
		--output $(SLA_OUTPUT) \
		--output-type $(OUTPUT_TYPE)

# Get ideas, teams, idea forms, and OKRs
.PHONY: all
all:
	@make ideas OUTPUT=files/ideas.xlsx
	@make teams OUTPUT=files/teams.xlsx
	@make idea-forms OUTPUT=files/idea-forms.xlsx
	@make okrs OUTPUT=files/okrs.xlsx
	@echo "Done! Files saved in files/ directory as ideas.xlsx, teams.xlsx, idea-forms.xlsx, and okrs.xlsx"

# Custom command with all options specified on command line
.PHONY: custom
custom:
	@echo "Running custom command..."
	@$(DOCKER_CMD) \
		--endpoint $(ENDPOINT) \
		--page $(PAGE) \
		--page-size $(PAGE_SIZE) \
		--output $(OUTPUT) \
		--location-status $(LOCATION_STATUS) \
		--objective-status $(OBJECTIVE_STATUS) \
		--output-format $(OUTPUT_FORMAT) \
		$(call all_pages_flag) \
		$(call process_filters)
	@echo "Data saved to $(OUTPUT)"

# Default target when running just 'make'
.DEFAULT_GOAL := help