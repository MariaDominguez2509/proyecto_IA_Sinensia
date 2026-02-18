# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**BookAI** is an LLM-powered book intelligence platform that provides:
- Intelligent book recommendations using embeddings and LLM reasoning
- Literary chatbot for questions about books, authors, and trends
- Automated analysis of editorial patterns (prices, ratings, genres, publication years)
- Content generation (synopses, reviews, alternative titles)
- Advanced semantic search across the entire catalog
- Optional interactive dashboard for natural language data exploration

**Dataset schema**: Book name, Author, Rating, Reviews count, Form, Price, Reading age, Print Length, Publishing date, Genre, and year-specific IDs (id_2023, id_2024, id_2025).

## Development Workflow with Speckit

This project uses **Speckit**, a structured development system with 9 specialized skills for feature development. The mandatory workflow is:

### 1. Feature Specification
```bash
/speckit.specify <feature description>
```
Creates `specs/<###-feature-name>/spec.md` with:
- Prioritized user stories (P1, P2, P3...) that are independently testable
- Acceptance criteria in Given-When-Then format
- Each story represents a deployable MVP slice

### 2. Implementation Planning
```bash
/speckit.plan
```
Generates design artifacts in `specs/<###-feature-name>/`:
- `plan.md` - Technical approach, constitution compliance checks
- `research.md` - Codebase exploration, existing patterns
- `data-model.md` - Entities, relationships, schemas
- `contracts/` - API contracts, interfaces
- `quickstart.md` - Setup and usage guide

**Gate**: Must pass constitution checks before proceeding.

### 3. Task Generation
```bash
/speckit.tasks
```
Creates `specs/<###-feature-name>/tasks.md` with:
- Dependency-ordered task list grouped by user story
- Parallel execution markers `[P]`
- Exact file paths for implementation

### 4. Implementation
```bash
/speckit.implement
```
Executes tasks in order, following TDD cycle (tests first, then implementation).

### Additional Skills
- `/speckit.clarify` - Ask targeted questions about underspecified areas
- `/speckit.analyze` - Cross-artifact consistency analysis
- `/speckit.checklist` - Generate custom feature checklist
- `/speckit.taskstoissues` - Convert tasks to GitHub issues
- `/speckit.constitution` - Update project constitution

## Constitution & Non-Negotiables

**Location**: `.specify/memory/constitution.md` (v1.0.0, ratified 2026-02-17)

### Core Principles (MUST be followed)

1. **Modular Architecture**
   - Each feature is an independent, composable library
   - Self-contained modules with clear boundaries
   - Common utilities (embeddings, LLM calls, caching) are extracted and shared

2. **Test-Driven Development (NON-NEGOTIABLE)**
   - Red-Green-Refactor cycle strictly enforced
   - Tests written BEFORE implementation, no exceptions
   - Minimum 80% coverage; 100% for LLM validation and recommendation algorithms
   - No merge without tests

3. **Responsible AI**
   - All LLM outputs MUST be validated (content safety, hallucination detection)
   - Document which models are used and why
   - Regular bias audits (genre, author representation, recommendation fairness)
   - Graceful fallback when LLM services fail
   - Monitor token usage and costs

4. **Performance First**
   - Simple queries: <200ms
   - Recommendations: <1s
   - Chatbot responses: <3s
   - Batch analysis: <30s per 1000 books
   - Pre-compute and cache embeddings; use Redis for frequent queries

5. **Observability**
   - Structured JSON logging with: timestamp, request_id, operation, duration, tokens_used
   - Log every LLM call: model, prompt hash, tokens, latency, cost
   - Track metrics: recommendation acceptance, cache hit ratio, error rates

6. **Simplicity & YAGNI**
   - Build minimal viable features first
   - No abstractions for hypothetical requirements
   - Simple, readable code over clever optimizations (unless performance requires it)

### AI/ML Constraints

- **No PII in LLM prompts** - sanitize user data
- **Prompt library** - version control, A/B test improvements
- **Model selection** - smaller models for classification, larger for generation
- **Error handling** - exponential backoff, model fallbacks, response caching

## Architecture Notes

### Expected Component Structure
Based on constitution and feature list, modules will be organized as:
- **Recommender Engine** - Embeddings, similarity search, LLM reasoning
- **Chatbot** - Conversation management, context handling, book Q&A
- **Analyzer** - Pattern detection, statistical analysis, trend identification
- **Content Generator** - Synopses, reviews, title alternatives
- **Semantic Search** - Vector store, query processing, ranking
- **Shared Utilities** - LLM client, caching layer, logging, validation

Each module must be independently testable and deployable.

### LLM Integration Pattern
All LLM interactions must follow:
1. Pre-validation (input sanitization, token optimization)
2. Execution (with logging: model, tokens, latency)
3. Post-validation (safety, format, hallucination checks)
4. Caching (successful responses for reuse)
5. Observability (metrics, cost tracking)

## Project Structure

```
.
├── .specify/               # Speckit system
│   ├── memory/
│   │   └── constitution.md # Project constitution (read this!)
│   ├── templates/          # Feature templates
│   └── scripts/            # Automation scripts
├── .claude/
│   └── commands/           # 9 speckit skills (see above)
├── specs/                  # Feature specifications (created by /speckit.specify)
│   └── <###-feature-name>/
│       ├── spec.md
│       ├── plan.md
│       ├── tasks.md
│       └── ...
└── BRAINSTROMING.md        # Initial project vision
```

**Note**: Source code structure (src/, tests/, etc.) not yet established - will be defined during first feature planning phase based on chosen tech stack.

## Working with This Codebase

### Before Starting Work
1. **Read the constitution**: `.specify/memory/constitution.md` - understand the 6 principles
2. **Check existing specs**: Review `specs/` for related features or patterns
3. **Use Speckit workflow**: Don't write code without going through specify → plan → tasks

### When Adding Features
1. Always start with `/speckit.specify <description>`
2. Review generated spec with user, refine if needed
3. Run `/speckit.plan` and verify constitution compliance
4. Generate tasks with `/speckit.tasks`
5. Implement with `/speckit.implement` (follows TDD automatically)

### When Writing Tests (MANDATORY)
- Write tests FIRST (TDD is non-negotiable)
- For LLM components: test with mocked responses, then integration tests
- Validate all edge cases: API failures, malformed responses, rate limits
- Performance tests for <200ms / <1s / <3s targets

### When Making LLM Calls
- Use shared LLM utility (once created)
- Log: model, prompt, tokens, latency, cost
- Validate output before returning
- Implement retry logic with exponential backoff
- Cache successful responses

### When Reviewing Code
Use constitution checklist:
- [ ] Modular design (independent, composable)
- [ ] Tests written first, passing, >80% coverage
- [ ] LLM outputs validated (safety, accuracy, format)
- [ ] Performance targets met (see constitution)
- [ ] Structured logging with LLM traceability
- [ ] Simple implementation (YAGNI followed)

## Tech Stack (To Be Determined)

Language, frameworks, and dependencies will be chosen during first feature planning based on:
- Performance requirements (embedding generation, vector search)
- LLM provider selection (OpenAI, Anthropic, local models)
- Deployment target (cloud, on-premise, hybrid)
- Team expertise and maintenance considerations

This decision is deferred to align with Simplicity principle (YAGNI) - no premature technology choices.
