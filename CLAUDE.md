# CLAUDE.md

## 🎯 Purpose of This Document

This document provides a **framework for how to approach** building tools. It does NOT prescribe specific implementations. Instead, it emphasizes:

- **Working methodology** - How to break down work and make progress
- **Decision-making principles** - When to ask questions vs. when to proceed
- **Critical constraints** - Non-negotiable requirements that must be met
- **Risk avoidance** - Common pitfalls and how to avoid them

The *what* is captured plan.md documents. This document is about the *how*.

## 📚 Essential Documentation

**When starting a new session on this project, review these documents:**

1. **`executive-summary.md`** - Provides a high level overview of what this library is for
2. **`plan.md`** - Current development status, completed work, next tasks
3. **`README.md`** - How to run the project, testing commands, dev scripts
4. **`plans/`** - Historical detailed implementation plans for completed features

---

## ⚠️ Critical Operating Principles

### 1. Plan Before You Code

**Never start coding without a plan approved by the developer.**

For any feature or task:
1. **Analyze** the requirement and identify what needs to be built
2. **Break it down** into small increments
3. **Propose the plan** to the developer with:
   - Sequence of steps
   - What will be built in each step
   - How you'll verify each step works
   - Any assumptions or questions
4. **Update the shared plan document** with the pending steps so everyone can review progress
5. **Wait for approval** before writing code
6. **Execute one step at a time**, verifying before proceeding

**Always clarify uncertainty.** If the developer suggests an approach and you're unsure it's the best option, ask follow-up questions and share best-practice alternatives instead of blindly agreeing.

**Prioritize convenience scripts.** Assume the developer prefers simple helper scripts over long Docker or tooling commands; add or update scripts rather than asking them to run complex shell invocations.

**Capture recurring warnings.** When a warning resurfaces after a fix (example: API deprecation), document the permanent remedy in README/plan and bake it into future steps so it doesn’t regress again.

**Organize the plan.** The plan should be organized into logical chunks, in the order they should be tackled. Use checklist items with sub-checklist items as needed to document the work.

**Example:**
❌ "I'll build a tool to fetch roadmap items" (too vague, no plan)
✅ "Here's my plan for the fetching roadmap items:
   1. Create basic structure following guidance
   2. Add filtering options
   3. Add options for saving in different formats
   Does this approach work?"

### 2. Ask Questions First

**When you encounter uncertainty, STOP and ASK before proceeding.**

Ask questions when you're unsure about:
- **Requirements**: "What filters do you need to apply this call?"
- **Architecture**: "Should I use WebSockets for real-time updates, or is polling sufficient?"
- **Priorities**: "We're running short on time - should I focus on polish or add conflict detection?"
- **Trade-offs**: "I can do X quickly but it's less flexible, or Y which takes longer but is more robust. Which matters more for the demo?"

**Present options with trade-offs** rather than just picking one:
✅ "For the data store, I see three options:
   1. In-memory only (fast, simple, data lost on restart)
   2. SQLite (persistent, slightly more complex)
   3. JSON files (persistent, very simple, but slower)
   For a demo that needs data reset capability, which approach do you prefer?"

### 3. Small, Incremental Changes

**Make ONE logical change at a time.**

- Each increment should be **testable independently**
- Aim for **small chunks of work**
- **Commit frequently** with clear messages
- If something breaks, it should be **easy to identify and revert**

Think of it like building with LEGO blocks, not pouring concrete.

### 4. Verify Before Proceeding

**After each increment, demonstrate it works before moving on.**

- Show what you built
- Explain what it does
- Demo that it works
- Get confirmation before continuing

**Don't stack unverified changes.** Each layer should be solid before adding the next.

## 🔒 Non-Negotiable Requirements

These constraints MUST be met regardless of implementation approach:

### Security & Configuration
- ✅ **Environment variables** for all sensitive data (API keys, etc.)
- ✅ **`.env` file is git-ignored** from the start
- ✅ **`.env.example`** provided as template with placeholder values
- ✅ **No secrets in code** ever

### Architecture
- ✅ **Dockerized** - entire project runs via Docker Compose
- ✅ **Container-only dependencies** - install libraries inside Docker images, not on the host (never run `npm install`, Homebrew, etc. on the maintainer’s machine without explicit approval)

### Code Quality
- ✅ **Clear separation of concerns** (don't mix UI, business logic, and data access)
- ✅ **Error handling** - user-friendly messages, not stack traces
- ✅ **Consistent code style** throughout
- ✅ **Fix root causes, not symptoms** - NEVER ignore or suppress errors without attempting proper fixes first
  - ❌ BAD: Adding `// eslint-disable-next-line` to hide type errors
  - ❌ BAD: Using `as any` to bypass TypeScript checks
  - ✅ GOOD: Properly typing function parameters (e.g., `(url: RequestInfo | URL)` instead of `(url)`)
  - ✅ GOOD: Handling all type cases explicitly (type guards, conditional logic)
  - **Only suppress warnings** when the proper fix is genuinely impractical AND you document why
  
  ---
  
  ## 🎨 Implementation Philosophy
  
  ✅ **DO:**
  - Focus on features that will help attain our working goal
  - Build the happy path thoroughly
  - Keep it simple and understandable
  
  ❌ **DON'T:**
  - Over-engineer for scale
  - Handle every edge case
  - Build features not in requirements
  - Optimize for performance beyond reasonable needs
  
  ### Choose Simplicity Over Cleverness
  
  When faced with multiple approaches:
  - **Simple** beats elegant
  - **Working** beats perfect  
  - **Boring** beats exciting
  - **Maintainable** beats optimized
  
### Make Assumptions Explicit
  
  When you make a design decision, **document your reasoning**:
  
  ---
  
  ## 🚨 Common Pitfalls to Avoid
  
  ### 1. The "Big Bang" Approach
  ❌ Writing lots of code without testing
  ✅ Small increments with verification after each change
  
  ### 2. Assuming You Know What They Want
  ❌ "I think they probably want X"
  ✅ "Should I implement X or Y?" - ask with trade-offs presented
  
  ### 3. Skipping Verification
  ❌ "It should work" (without testing)
  ✅ "Here's a demo of it working" - show, don't just tell
  
  ### 4. Unclear Communication
  ❌ "It's done" (without showing anything)
  ✅ "Here's what I built, how it works, and what's next"
  
  ### 5. Over-Engineering
  ❌ Building abstractions for "future flexibility"
  ✅ Build what's needed now, refactor later if required
  
  ### 6. Suppressing Errors Instead of Fixing Them
  ❌ Adding `eslint-disable` or `@ts-ignore` comments to hide problems
  ✅ Fixing the underlying type/lint issue properly
  
  ---
  
  ## 🛠️ Working Methodology
  
  ### Starting a New Task
  
  1. **Read the requirement** from requirements doc
  2. **Understand the goal** - what problem does this solve?
  3. **Identify dependencies** - what needs to exist first?
  4. **Create a plan** broken into small steps
  5. **Present the plan** for approval
  6. **Execute incrementally** with verification
  
  ### During Implementation
  
  - **Stay focused** on the current increment
  - **Test as you go** - don't wait until "finished"
  - **Ask questions** when stuck or uncertain
  - **Document non-obvious decisions** in code comments
  - **Keep the developer informed** of progress
  
  ### When Stuck
  
  1. **Clearly explain the problem** - what are you trying to do?
  2. **Show what you've tried** - what approaches failed?
  3. **Identify the blocker** - what's preventing progress?
  4. **Propose options** - what are possible ways forward?
  5. **Ask for guidance** - which approach should you take?
  
  ### Completing a Task
  
  1. **Demo the functionality** - show it working
  2. **Explain what you built** - at a high level
  3. **Note any limitations** - what doesn't work yet?
  4. **Propose next steps** - what should come next?
  5. **Get confirmation** before moving on
  
  ---
  
  ## 💬 Communication Guidelines
  
  ### 1. Be Clear and Specific
  State exactly what you're working on, not vague generalities.
  - ❌ "Working on the backend"
  - ✅ "Implementing the POST /phases endpoint to create new phases"
  
  ### 2. Show Your Work
  Demonstrate results, don't just describe them.
  - ❌ "The chat interface is done"
  - ✅ "Here's the chat interface working [demo/screenshot]. Next I'll add loading states."
  
  ### 3. Ask Productive Questions
  Present options with trade-offs, not open-ended "how" questions.
  - ❌ "How should I do this?"
  - ✅ "Should I prioritize X or Y? X is faster but less flexible, Y handles edge cases but takes longer."
  
  ---
  
  ## 🎓 Learning as You Go
  
  ### When Encountering New Technology
  1. **Check the requirements doc** - is it specified?
  2. **Research briefly** - what are the basics?
  3. **Ask if unsure** - "I see we need X, should I use approach A or B?"
  4. **Start simple** - get something working, refine later
  
  ### When Facing Technical Challenges
  1. **Try the obvious solution first** - don't overthink
  2. **Search for examples** - has someone solved this?
  3. **Test incrementally** - verify each piece works
  4. **Ask for help** when truly stuck
  
  ### When Making Design Decisions
  1. **Weigh complexity** - is the benefit worth the added complexity?
  2. **Document your choice** - explain why you picked this approach
  3. **Stay flexible** - be ready to change if needed
  
---
  
  ## 🎬 Final Reminders
  
  **This is a helper tool, not a product:**
  - Working features > perfect code
  - Happy path > edge cases  
  - Simple > clever
  - Done > perfect
  
  **You're not alone:**
  - Ask questions liberally
  - Show your work frequently
  - Admit when uncertain
  - Collaborate, don't guess
  
  **Break it down:**
  - Small steps
  - Frequent verification
  - One thing at a time
  - Always have a plan
  
  **You've got this! 🚀**
  
  The requirements are clear, the framework is here, and the developer is ready to collaborate. Take it one increment at a time, ask questions when needed, and build something great.

## Core Commands

### Build and Setup
```bash
# Build Docker image
make build

# Initial setup (creates token.txt and builds image)  
./setup.sh
```

### Data Fetching Commands
```bash
# Fetch ideas with detailed information (includes timestamps, custom dropdown fields, team columns, etc.)
make ideas

# Fetch teams data
make teams

# Fetch idea forms data with detailed information (includes custom fields, instructions, etc.)
make idea-forms

# Fetch objectives and key results (OKRs) data (active objectives by default, Excel format)
make okrs

# Fetch all objectives and key results (including inactive)
make okrs OBJECTIVE_STATUS=all OUTPUT=all_okrs.xlsx

# Generate OKRs in markdown format
make okrs OUTPUT_FORMAT=markdown OUTPUT=okrs.md

# Generate all OKRs in markdown format
make okrs OBJECTIVE_STATUS=all OUTPUT_FORMAT=markdown OUTPUT=all_okrs.md

# Fetch all data types (saves as ideas.xlsx, teams.xlsx, idea-forms.xlsx, and okrs.xlsx)
make all

# Custom endpoint with specific parameters
make custom ENDPOINT=idea-forms OUTPUT=custom.xlsx FILTERS="name:Feature Request"
make custom ENDPOINT=okrs OUTPUT=custom_okrs.xlsx FILTERS="name:Q4 Goals"
make custom ENDPOINT=okrs OUTPUT_FORMAT=markdown OUTPUT=quarterly_review.md OBJECTIVE_STATUS=all
```

### Common Parameters
- `OUTPUT=filename.xlsx` - Set output filename
- `FILTERS="key1:value1 key2:value2"` - Apply multiple filters
- `PAGE=num` - Set page number (default: 1)
- `PAGE_SIZE=num` - Set page size (default: 200, max: 500)
- `ALL_PAGES=true/false` - Fetch all pages (default: true)
- `LOCATION_STATUS=status` - Filter ideas by location status (default: not_archived)
  - Options: all, visible, hidden, archived, not_archived
- `OBJECTIVE_STATUS=status` - Filter objectives by status (default: active)
  - Options: active, all
- `OUTPUT_FORMAT=format` - Output format for OKRs (default: excel)
  - Options: excel, markdown

## Architecture Overview

This is a Python-based ProductPlan API client that runs in Docker containers with simplified Make commands.

### Core Components

1. **ProductPlanAPI class** (`productplan_api.py:13-176`)
   - Handles authentication via Bearer token from `token.txt`
   - Makes paginated requests to ProductPlan API v2
   - Supports ideas (`discovery/ideas`), teams, and idea forms (`discovery/idea_forms`) endpoints
   - Automatic pagination with `_fetch_all_pages` method

2. **DataExporter class** (`productplan_api.py:178-350`)
   - Exports data to Excel format using pandas
   - For ideas: processes custom text fields into separate columns with "Custom: " prefix
   - For ideas: adds team assignment columns (1 if assigned, 0 if not)
   - Handles JSON parsing of nested API response data

3. **Makefile-based interface** (`Makefile:1-119`)
   - Wraps Docker commands with simplified Make targets
   - Processes space-separated filter syntax (`key:value key2:value2`)
   - Handles parameter passing to Docker container
   - Default output path is `files/productplan_data.xlsx` (customizable via OUTPUT parameter)

### Data Processing Flow

When fetching ideas:
1. API call retrieves paginated results from ProductPlan
2. For each idea, detailed information is fetched using individual idea endpoint
3. Location status filtering is applied (excludes archived ideas by default)
4. Team mapping is built from separate teams API call
5. Custom text fields are parsed and extracted into individual columns with "Custom: " prefix
6. Custom dropdown fields are parsed and extracted into individual columns with "Custom_Dropdown: " prefix
7. Team assignments are converted to binary columns (one per team)
8. Enhanced idea data with timestamps and all details is exported to Excel in `files/` directory

When fetching idea forms:
1. API call retrieves list of idea forms from ProductPlan
2. For each form, detailed information is fetched using individual form endpoint
3. Custom text fields and dropdown fields are flattened into separate columns
4. Enhanced form data with all details is exported to Excel in `files/` directory

**File Output:** All generated files are saved to the `files/` directory by default. The script automatically creates this directory if it doesn't exist using `os.makedirs(output_dir, exist_ok=True)` in all export methods.

### Key Files

- `productplan_api.py` - Main API client and data processing logic
- `Makefile` - Command interface with Docker integration
- `Dockerfile` - Python 3.9 container with pandas/requests dependencies
- `requirements.txt` - Python dependencies (requests, pandas, openpyxl, numpy)
- `token.txt` - ProductPlan API token (not in repo, created by setup.sh)
- `files/` - Directory for all generated output files (auto-created, git-ignored)
- `plans/` - Historical detailed implementation plans (git-ignored)

## OKR Usage Examples and Best Practices

### Basic OKR Commands

```bash
# Get active objectives only (default behavior)
make okrs

# Get all objectives including inactive ones
make okrs OBJECTIVE_STATUS=all

# Generate markdown report for quarterly review
make okrs OUTPUT_FORMAT=markdown OUTPUT=q1_okrs.md

# Get all objectives in markdown format with custom filename
make okrs OBJECTIVE_STATUS=all OUTPUT_FORMAT=markdown OUTPUT=company_okrs.md
```

### OKR Output Format Comparison

**Excel Format**: Best for data analysis, filtering, and integration with other tools
- Flattened tabular structure
- One row per key result (or objective if no key results)
- All data in columns for easy sorting/filtering
- Includes reference IDs for linking back to ProductPlan

**Markdown Format**: Best for documentation, reports, and team communication
- Hierarchical structure with clear headings
- Professional formatting for stakeholder reviews
- Easy to read and share
- Perfect for quarterly business reviews and team updates

### Integration Workflow Examples

```bash
# Weekly team review - get active OKRs in markdown
make okrs OUTPUT_FORMAT=markdown OUTPUT=weekly_review.md

# Quarterly analysis - get all OKRs in Excel for data analysis
make okrs OBJECTIVE_STATUS=all OUTPUT=quarterly_analysis.xlsx

# Executive summary - active OKRs in clean markdown format
make okrs OUTPUT_FORMAT=markdown OUTPUT=executive_summary.md

# Complete data export - all OKRs with full details in Excel
make okrs OBJECTIVE_STATUS=all OUTPUT=complete_okr_data.xlsx
```

### Understanding OKR Data Structure

**Team Resolution**: 
- Teams are automatically resolved from IDs to names
- Multiple teams per objective/key result are displayed as comma-separated values
- Team mapping is built once to avoid API rate limiting

**Key Result Names**: 
- Key result names come from the 'description' field in the ProductPlan API
- This ensures you get the actual key result descriptions, not generic identifiers

**Status Filtering**:
- `active` (default): Excludes archived, inactive, or deleted objectives
- `all`: Includes all objectives regardless of status for comprehensive reporting

**Progress Tracking**:
- Target: The goal value for the key result
- Current: The current progress value
- Progress: Progress percentage or completion metric

### API Endpoints Used

- `https://app.productplan.com/api/v2/discovery/ideas` - Ideas list
- `https://app.productplan.com/api/v2/discovery/ideas/{id}` - Individual idea details with timestamps and custom dropdown fields
- `https://app.productplan.com/api/v2/teams` - Team data for ID-to-name mapping
- `https://app.productplan.com/api/v2/discovery/idea_forms` - Idea form definitions
- `https://app.productplan.com/api/v2/discovery/idea_forms/{id}` - Individual idea form details
- `https://app.productplan.com/api/v2/strategy/objectives` - Objectives list
- `https://app.productplan.com/api/v2/strategy/objectives/{id}` - Individual objective details
- `https://app.productplan.com/api/v2/strategy/objectives/{objective_id}/key_results` - Key results for a specific objective

### Available Filters

**Ideas endpoint:**
- id, name, description, channel, customer, opportunities_count, source_name, source_email, location_status
- Enhanced processing fetches detailed information for each idea including:
  - Created and updated timestamps (created_at, updated_at)
  - Custom dropdown fields with values
  - Tags, opportunity_ids, idea_form_id
  - All fields are flattened for Excel export
- Default filtering excludes archived ideas (location_status != "archived")

**Teams endpoint:**  
- id, name

**Idea Forms endpoint:**
- Endpoint supports pagination and filtering (specific filters may vary)
- Enhanced processing fetches detailed information for each form including:
  - Form title, instructions, enabled status
  - Custom text fields with labels
  - Custom dropdown fields with labels and allowed values
  - Creation and update timestamps

**OKRs (Objectives and Key Results) endpoint:**
- **API Endpoints Used**: 
  - `https://app.productplan.com/api/v2/strategy/objectives` - Objectives list and details
  - `https://app.productplan.com/api/v2/strategy/objectives/{objective_id}/key_results` - Key results for each objective
- **Status Filtering**: By default, only active objectives are fetched (use OBJECTIVE_STATUS=all to get all objectives)
- **Output Formats**: Supports both Excel and Markdown export formats
- **Team Resolution**: Automatically resolves team IDs to team names using teams API mapping
- **Enhanced Processing**: Fetches detailed information for each objective and all associated key results
- **Excel Column Structure** (in order):
  - Status (location_status), team name, objective name, objective description
  - Key result name (from 'description' field), key result target, key result current, key result progress
  - Objective id, key result id (at the end for reference)
- **Markdown Structure**:
  - H1: "Objectives and Key Results" (document title)
  - H2: Objective name (clean, without team in parentheses)
  - Objective description (if available)
  - H3: "Team" section with team name
  - H3: "Key Results" section with bulleted list or "No key results"
  - Key result format: "- Description (target: value) - Current: X | Progress: Y"
- **Data Logic**:
  - If objective has key results: one row per key result (Excel) or bulleted list (Markdown)
  - If objective has no key results: one row with empty key result fields (Excel) or "No key results" (Markdown)
- **Team Mapping**: Checks key result team_id first, then objective team_id, supports multiple teams per objective