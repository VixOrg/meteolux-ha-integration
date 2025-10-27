# MeteoLux Home Assistant Integration Constitution

<!--
  ============================================================================
  SYNC IMPACT REPORT - Constitution Update
  ============================================================================
  Version Change: 1.0.0 (no version change - clarification update)

  Modified Principles:
  - N/A

  Added Sections:
  - Principle IX: Documentation Management (permanent vs intermediate docs)
  - Contribution Guidelines: Spec-driven vs conventional development approaches

  Removed Sections:
  - N/A

  Templates Requiring Updates:
  ✅ .specify/templates/plan-template.md - Constitution Check section aligns
  ✅ .specify/templates/spec-template.md - Requirements align with principles
  ✅ .specify/templates/tasks-template.md - Task structure reflects principles

  Follow-up TODOs:
  - Add `.*.md` pattern to `.gitignore` to exclude hidden intermediate docs
  - Create or update `CONTRIBUTING.md` with contribution workflow guidance
  - Migrate existing intermediate docs to hidden file convention:
    - `IMPLEMENTATION_STATUS.md` → `.implementation-status.md`
    - `MVP_COMPLETION_REPORT.md` → `.mvp-completion-report.md`
    - `COMPLETE_FEATURE_REPORT.md` → `.complete-feature-report.md`
    - `TESTING_NOTES.md` → `.testing-notes.md`

  ============================================================================
-->

## Core Principles

### I. Simplicity First (KISS - Keep It Simple, Stupid)

**Principle**: Favor the simplest solution that meets requirements. Complexity must be explicitly justified against simpler alternatives.

**Rules**:
- MUST start with the most straightforward implementation
- MUST document rationale when introducing abstraction layers
- MUST reject complexity not justified by measurable requirements
- MUST prefer readability over cleverness

**Rationale**: Simple code is maintainable code. Home Assistant integrations run in diverse environments; simplicity reduces edge cases and support burden.

### II. Code Reusability (DRY - Don't Repeat Yourself)

**Principle**: Extract common patterns into reusable components, but only after the third occurrence.

**Rules**:
- MUST NOT abstract until a pattern appears at least 3 times
- MUST ensure abstractions have clear, single purposes
- MUST document the problem each abstraction solves
- SHOULD prefer composition over inheritance

**Rationale**: Premature abstraction creates coupling. Wait for patterns to emerge before extracting, ensuring abstractions serve real needs.

### III. Functional Robustness (SOLID Principles)

**Principle**: Design components with clear responsibilities, open for extension but closed for modification.

**Rules**:
- **Single Responsibility**: Each class/function MUST have one clear purpose
- **Open/Closed**: MUST extend behavior via configuration or inheritance, not modification
- **Liskov Substitution**: Subclasses MUST be substitutable for their base classes
- **Interface Segregation**: MUST NOT force clients to depend on methods they don't use
- **Dependency Inversion**: MUST depend on abstractions (coordinator pattern), not concrete implementations

**Rationale**: SOLID principles ensure code remains maintainable as the integration evolves through versions.

### IV. Minimal Implementation (YAGNI - You Aren't Gonna Need It)

**Principle**: Implement only what is specified. Do not add features "for the future."

**Rules**:
- MUST implement only requirements in the current specification
- MUST NOT add configuration options without explicit user request
- MUST NOT implement features based on speculation
- SHOULD track rejected features in issue tracker for community validation

**Rationale**: Every line of code is a maintenance burden. Unneeded features create complexity, bugs, and support overhead.

### V. Single Level of Abstraction (SLAP)

**Principle**: Each function should operate at one level of abstraction. Mix high-level logic with low-level details sparingly.

**Rules**:
- MUST NOT mix high-level orchestration with implementation details in the same function
- SHOULD extract implementation details into clearly-named helper functions
- MUST ensure function names accurately describe their abstraction level
- SHOULD limit function length to ~20 lines when possible

**Rationale**: Consistent abstraction levels make code scannable and reduce cognitive load during maintenance.

### VI. Test-First Development (NON-NEGOTIABLE)

**Principle**: Tests are not optional. Integration and contract tests MUST exist before merging features.

**Rules**:
- MUST write integration tests for user-facing workflows (config flow, coordinator updates, entity state changes)
- MUST write contract tests for external API interactions (MeteoLux API, OpenStreetMap)
- SHOULD follow Red-Green-Refactor: write failing test → implement → refactor
- MUST maintain test coverage above 80% for core logic (coordinator, API client)
- MUST include tests in every pull request affecting functionality

**Test Categories**:
1. **Integration tests**: User workflows end-to-end (setup, reconfigure, entity updates)
2. **Contract tests**: External API boundary validation (request/response formats)
3. **Unit tests**: Pure functions, data transformations, validation logic (optional but encouraged)

**Rationale**: Home Assistant integrations run in unpredictable environments. Tests are the only reliable way to prevent regressions across HA versions, Python versions, and user configurations.

### VII. User Experience Consistency

**Principle**: Integration behavior MUST align with Home Assistant conventions and user expectations.

**Rules**:
- MUST follow Home Assistant naming conventions (snake_case for entity IDs, Title Case for friendly names)
- MUST use standard entity device classes and units of measurement
- MUST provide clear, actionable error messages in the language selected by the user
- MUST support reconfiguration without data loss where feasible
- MUST document breaking changes and migration paths in release notes
- SHOULD default to sensible values (10min current, 30min hourly, 6h daily updates)

**Rationale**: Consistency reduces friction. Users should not need to "learn" this integration; it should behave like every other HA integration.

### VIII. Performance Requirements

**Principle**: Integration MUST NOT degrade Home Assistant performance.

**Rules**:
- MUST use the coordinator pattern for API requests (no direct polling from entities)
- MUST respect update intervals (no more frequent than 1 minute for current conditions)
- MUST implement exponential backoff on API failures (2s, 4s, 8s, 16s, 30s, 60s)
- MUST NOT block the event loop (all I/O via async/await)
- SHOULD complete API requests within 10 seconds (timeout after 30s)
- MUST NOT load entity state from disk on every HA restart (use restore state pattern)

**Performance Targets**:
- Startup: Integration loads within 5 seconds on HA restart
- API response: 95th percentile < 2 seconds for current conditions
- Memory: < 50MB steady-state for single location (< 100MB for 5 locations)
- Coordinator updates: Complete within 10 seconds including retries

**Rationale**: Slow integrations frustrate users and destabilize Home Assistant. Performance is a feature.

### IX. Documentation Management

**Principle**: Maintain a minimal set of permanent documentation while allowing flexible intermediate documentation.

**Rules**:
- **Permanent Documentation** (MUST be maintained and version-controlled):
  - `README.md`: User-facing documentation, installation, and usage guide
  - `CONTRIBUTING.md`: Contribution guidelines and development setup
  - `CLAUDE.md`: AI agent guidance and project context
  - `LICENSE`: Project license (MIT)
  - `CHANGELOG.md`: Version history and release notes
  - `specs/`: Feature specifications and design documents

- **Intermediate Documentation** (SHOULD use hidden file convention):
  - MUST be placed inside `.tmp_doc` folder
  - MUST use `.<filename>.md` naming convention (e.g., `.implementation-status.md`, `.testing-notes.md`)
  - MUST be git-ignored via `.tmp_doc/` pattern in `.gitignore`
  - SHOULD be used for progress tracking, implementation notes, test reports, and temporary analysis
  - MAY be deleted once their purpose is fulfilled
  - SHOULD NOT be committed to version control

- **Documentation Organization**:
  - MUST keep root directory clean (only permanent docs visible)
  - MUST NOT create documentation that duplicates information already in permanent docs
  - SHOULD consolidate intermediate docs into permanent docs when appropriate

**Rationale**: A clean, minimal documentation structure reduces maintenance burden and cognitive overhead. Hidden intermediate docs allow flexible working documentation without cluttering the repository.

## Quality Standards

### Testing Requirements

**Integration Tests** (MANDATORY):
- MUST cover config flow: initial setup, reconfigure location, reconfigure settings, reconfigure name
- MUST cover coordinator: successful update, API failure handling, partial data handling
- MUST cover entity lifecycle: entity creation, state updates, availability changes
- MUST use fixtures for API responses (no live API calls in tests)

**Contract Tests** (MANDATORY):
- MUST validate MeteoLux API request formats (query parameters, headers)
- MUST validate MeteoLux API response schemas (required fields, data types)
- MUST validate OpenStreetMap Nominatim requests/responses
- MUST document API version tested against (e.g., MeteoLux API v1)

**Code Quality Gates** (MANDATORY):
- MUST pass `ruff` linting with no errors
- MUST pass `black` formatting checks
- MUST pass `mypy` type checking in strict mode
- MUST include type hints on all public functions
- SHOULD include docstrings on public classes and complex functions

**Running Tests Locally** (MANDATORY for contributors):
- MUST run tests locally before pushing commits
- MUST use Docker for local test execution to ensure consistency with CI environment
- MUST verify all tests pass before submitting pull requests

**Docker Test Execution**:
```bash
# Build the test environment (first time only)
docker-compose build

# Run all tests
docker-compose run --rm test

# Run specific test file
docker-compose run --rm test pytest tests/test_config_flow.py -v

# Run with coverage report
docker-compose run --rm test pytest --cov=custom_components.meteolux --cov-report=html tests/
```

**Why Docker?**:
- Tests use `pytest-homeassistant-custom-component` which blocks sockets
- Windows asyncio requires sockets for event loop pipes, making tests incompatible on Windows
- Docker provides a consistent Linux environment matching GitHub Actions CI
- Eliminates "works on my machine" issues across different development environments

**Alternatives to Docker**:
- GitHub Actions (tests run automatically on push)
- WSL (Windows Subsystem for Linux) for Windows developers
- Native Linux/macOS environments (tests run directly with `pytest`)

### Code Review Standards

**Every Pull Request MUST**:
- Link to issue or specification describing the change
- Include tests demonstrating the change works
- Pass all automated checks (linting, type checking, tests)
- Include CHANGELOG entry for user-facing changes
- Update README.md or other docs if behavior changes

**Reviewers MUST Verify**:
- Constitution compliance (especially KISS, YAGNI, testing)
- Test coverage for new code paths
- Error handling for new API interactions
- Breaking changes are documented with migration path

## Development Workflow

### Pull Request Process

1. **Branch Naming**: `feature/<issue-number>-<short-description>` or `fix/<issue-number>-<short-description>`
2. **Commit Messages**: Follow Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`)
3. **PR Description**: MUST include:
   - Problem statement
   - Solution approach
   - Testing performed
   - Breaking changes (if any)
4. **Review**: Requires one approval from a maintainer
5. **Merge**: Squash and merge to keep history clean

### Release Process

**Versioning** (Semantic Versioning):
- **MAJOR (X.0.0)**: Breaking changes requiring user action (config format changes, entity ID changes)
- **MINOR (x.Y.0)**: New features, backward-compatible (new entities, new config options)
- **PATCH (x.y.Z)**: Bug fixes, performance improvements, documentation

**Release Checklist**:
- [ ] All tests pass on supported HA versions (current, previous)
- [ ] CHANGELOG.md updated with user-facing changes
- [ ] manifest.json version incremented
- [ ] README.md updated if needed
- [ ] GitHub release created with release notes
- [ ] HACS validation passes

### Maintenance Standards

**Backward Compatibility**:
- MUST support current and previous major Home Assistant version
- MUST NOT remove config options without deprecation period (one major version)
- MUST NOT rename entities without opt-in migration or reconfigure workflow

**Dependency Management**:
- MUST pin Home Assistant minimum version in manifest.json
- MUST NOT add external dependencies without justification (prefer stdlib)
- MUST verify dependencies are compatible with Home Assistant's Python environment

**Security**:
- MUST validate all user input (addresses, coordinates, intervals)
- MUST NOT log sensitive data (API responses with location data)
- MUST handle API rate limits gracefully
- MUST use HTTPS for all external requests

## Governance

### Amendment Procedure

1. **Proposal**: Open GitHub issue with `constitution` label describing the proposed change
2. **Discussion**: Community discussion period (minimum 7 days)
3. **Approval**: Maintainer consensus required for approval
4. **Documentation**: Update this constitution with rationale for change
5. **Migration**: Update templates and codebase to reflect new principles

### Contribution Guidelines

**Principle**: The project promotes spec-driven development but also welcomes contributions using conventional development approaches.

**Development Approaches**:

1. **Spec-Driven Development** (RECOMMENDED):
   - Write specifications first using `.specify/templates/spec-template.md`
   - Create implementation plans with `.specify/templates/plan-template.md`
   - Generate tasks using `.specify/templates/tasks-template.md`
   - Execute tasks systematically with constitution compliance checks
   - **Benefits**: Clear requirements, better planning, alignment with project principles
   - **When to Use**: New features, complex refactoring, architectural changes

2. **Conventional Development** (ALLOWED):
   - Open GitHub issue describing the problem or feature request
   - Submit pull request with implementation and tests
   - Ensure PR includes constitution compliance (KISS, YAGNI, testing requirements)
   - Document design decisions in PR description
   - **Benefits**: Faster iteration for simple changes, familiar workflow
   - **When to Use**: Bug fixes, small improvements, documentation updates

3. **Hybrid Approach** (ENCOURAGED):
   - Start with lightweight specification (issue description + acceptance criteria)
   - Implement with iterative feedback
   - Document final design in PR or update specs after implementation
   - **Benefits**: Balance between planning and agility
   - **When to Use**: Medium-complexity features, exploratory work

**Contribution Standards** (ALL approaches MUST follow):
- Code MUST pass all quality gates (linting, type checking, tests)
- Changes MUST include appropriate test coverage
- Breaking changes MUST be documented with migration path
- All contributions MUST comply with Core Principles (I-IX)

**For First-Time Contributors**:
- SHOULD start with conventional development (issue + PR)
- MAY adopt spec-driven workflow after becoming familiar with the project
- SHOULD ask maintainers for guidance on which approach to use

**Rationale**: Different contribution types and contributor experience levels benefit from different workflows. Spec-driven development ensures alignment with project principles for complex work, while conventional development enables quick contributions for simple changes.

### Versioning Policy

**Version Increment Rules**:
- **MAJOR**: Principle removed or redefined in backward-incompatible way (e.g., removing SOLID requirement)
- **MINOR**: New principle added or existing principle materially expanded (e.g., adding security section)
- **PATCH**: Clarifications, wording improvements, typo fixes (no semantic change)

### Compliance Review

**All Pull Requests**:
- MUST be reviewed for constitution compliance by a maintainer
- MUST justify any complexity violations in PR description
- MUST update this constitution if introducing new patterns that should be standard

**Constitution Supersedes**:
- This constitution takes precedence over individual preferences
- Coding style guides (defer to this constitution, then `ruff` defaults)
- Implementation patterns not explicitly addressed here (use best judgment, document in PR)

**Guidance File**:
- Use `.specify/templates/agent-file-template.md` for runtime development guidance
- Templates in `.specify/templates/` provide workflow structure
- This constitution provides non-negotiable principles

---

**Version**: 1.0.0 | **Ratified**: 2025-10-28 | **Last Amended**: 2025-10-29
