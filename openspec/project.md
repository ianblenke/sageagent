# Project Context

## Purpose
SageAgent is an open-source implementation of the OpenSage framework described in arxiv.org/abs/2602.16891. It is an Agent Development Kit (ADK) that enables LLMs to automatically construct agents with self-generated topologies, dynamic toolsets, and hierarchical graph-based memory. The goal is to shift agent development from human-centered to AI-centered paradigms, where systems self-design their operational components.

## Tech Stack
- Python 3.11+
- Anthropic Claude API / Agent SDK (primary LLM backend)
- OpenAI Agents Python library (secondary LLM backend)
- LangGraph (graph-based workflow orchestration)
- Docker (sandboxed execution environments)
- Mem0 (memory management)
- NetworkX or similar (graph-based memory DAG)
- pytest (testing)
- Pydantic (data validation and schemas)

## Project Conventions

### Code Style
- Follow PEP 8 with Black formatter (line length 100)
- Type hints on all public APIs
- Docstrings on modules and public classes/functions (Google style)
- Snake_case for functions/variables, PascalCase for classes
- Use `pathlib.Path` over `os.path`

### Architecture Patterns
- Plugin-based architecture for LLM backends and tool providers
- Abstract base classes define interfaces; concrete implementations are swappable
- Dependency injection for core services (memory, tools, LLM clients)
- DAG-based task decomposition and execution
- Event-driven agent communication via shared memory graph

### Testing Strategy
- Every spec scenario MUST have a corresponding test (spec-to-test traceability)
- All generated code MUST have 100% test coverage (line and branch)
- pytest with fixtures for LLM mock responses
- pytest-cov for coverage enforcement (`--cov-fail-under=100`)
- Integration tests for agent workflows
- Coverage reports generated on every test run

### Git Workflow
- Main branch: `main`
- Feature branches: `feat/<change-id>`
- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`

## Domain Context
OpenSage is an Agent Development Kit where:
- **Agents** are LLM-powered autonomous units that receive tasks, decompose them, and execute using tools
- **Topology** refers to the hierarchical structure of parent/child agents spawned dynamically based on task requirements
- **Toolsets** are collections of callable functions (code analysis, fuzzing, debugging, etc.) that agents invoke
- **Memory** is a directed acyclic graph (DAG) where nodes store information chunks and edges encode semantic/causal relationships
- **Task DAGs** define dependencies between subtasks, enabling parallel execution where possible
- The system targets software engineering benchmarks: SWE-Bench Pro, Terminal-Bench, TBench, Cyber-Gym

## Important Constraints
- All agent execution must be sandboxable (Docker containers for untrusted code)
- LLM API keys must never be logged or stored in memory graph
- Agent hierarchies must have configurable depth limits to prevent runaway spawning
- Memory graph must support garbage collection for long-running sessions
- Tool execution must have configurable timeouts
- Secrets must NEVER be committed to the repo; use SOPS for any secret management
- API keys are loaded from environment variables only (ANTHROPIC_API_KEY, OPENAI_API_KEY)

## External Dependencies
- Anthropic Claude API (LLM inference)
- OpenAI API (alternative LLM backend)
- Docker Engine (sandboxed execution)
- GitHub API (repository operations for SE tasks)
