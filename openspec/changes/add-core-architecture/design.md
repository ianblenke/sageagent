## Context
SageAgent implements the OpenSage paper's architecture: an Agent Development Kit where LLMs autonomously construct agent hierarchies, generate toolsets, and manage graph-based memory. The system must support multiple LLM backends (Claude, OpenAI), sandboxed tool execution, and configurable depth limits.

## Goals / Non-Goals
- Goals:
  - Modular, plugin-based architecture with clear interfaces between components
  - Support Claude API and OpenAI as swappable LLM backends
  - Graph-based memory with typed nodes and relationship edges
  - Dynamic agent spawning with configurable hierarchy depth limits
  - Tool registry with standardized invocation interface
  - Sandboxed execution via Docker for untrusted code
- Non-Goals:
  - Web UI or REST API (CLI-first for now)
  - Fine-tuning integration (LlamaFactory deferred to later proposal)
  - Distributed multi-node deployment (single-process for v1)
  - Benchmark harness (separate proposal)

## Decisions

### Package Structure
```
sageagent/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── agent.py          # Agent base class, lifecycle
│   ├── engine.py         # AgentEngine orchestrator
│   ├── config.py         # Configuration models
│   └── types.py          # Shared type definitions
├── topology/
│   ├── __init__.py
│   ├── manager.py        # TopologyManager
│   ├── decomposer.py     # TaskDecomposer (LLM-driven)
│   └── dag.py            # TaskDAG data structure
├── tools/
│   ├── __init__.py
│   ├── registry.py       # ToolRegistry
│   ├── generator.py      # DynamicToolGenerator
│   ├── base.py           # Tool base class / interface
│   └── builtins/         # Built-in SE tools
│       ├── __init__.py
│       ├── shell.py      # Shell command execution
│       ├── file_ops.py   # File read/write/search
│       ├── docker.py     # Docker container execution
│       └── code_analysis.py  # Static analysis wrappers
├── memory/
│   ├── __init__.py
│   ├── graph.py          # MemoryGraph (DAG implementation)
│   ├── node.py           # MemoryNode types
│   └── query.py          # Graph query/traversal
├── communication/
│   ├── __init__.py
│   ├── bus.py            # MessageBus for inter-agent messaging
│   └── protocols.py      # Message types and coordination protocols
└── llm/
    ├── __init__.py
    ├── base.py           # LLMBackend abstract interface
    ├── claude.py         # Anthropic Claude implementation
    └── openai.py         # OpenAI implementation
```

- Decision: Flat package with sub-packages per capability. Each capability maps to a sub-package.
- Alternatives considered: Monolithic single module (rejected - poor separation), microservices (rejected - premature for v1).

### LLM Backend Abstraction
- Decision: Abstract `LLMBackend` class with `generate()`, `generate_structured()`, and `generate_with_tools()` methods. Concrete implementations for Claude and OpenAI.
- Alternatives considered: Direct SDK usage everywhere (rejected - tight coupling), LangChain abstraction (rejected - unnecessary dependency weight).

### Memory Graph Implementation
- Decision: Use NetworkX for the in-memory DAG. Nodes are Pydantic models with typed payloads. Edges carry relationship metadata.
- Alternatives considered: Custom graph (rejected - reinventing the wheel), Neo4j (rejected - too heavy for embedded use), Mem0 directly (considered for later integration but too opinionated for core).

### Tool Interface
- Decision: Tools implement a `Tool` base class with `name`, `description`, `parameters_schema` (JSON Schema), and `execute(**kwargs) -> ToolResult`. The ToolRegistry manages discovery and invocation.
- Alternatives considered: Function decorators only (rejected - harder to generate dynamically), LangChain tools (rejected - dependency coupling).

### Agent Communication
- Decision: Shared MemoryGraph as primary communication channel. Agents write results as nodes; dependent agents query for them. A lightweight MessageBus handles synchronization signals (task complete, error, etc.).
- Alternatives considered: Direct message passing (rejected - tight coupling), external queue like Redis (rejected - premature complexity).

### Testing and Coverage
- Decision: 100% test coverage enforced via `pytest-cov --cov-fail-under=100`. Every spec scenario maps to at least one test. Tests are co-located in `tests/` mirroring the `sageagent/` package structure.
- Test naming convention: `test_<module>::test_<scenario_name>` where scenario names derive from spec scenarios (e.g., `#### Scenario: Agent creation with role` → `test_agent::test_agent_creation_with_role`)
- All LLM calls are mocked in unit tests. Integration tests may use live APIs behind a `--live` pytest marker.
- CI blocks merge if coverage drops below 100%.

## Risks / Trade-offs
- NetworkX in-memory graph won't scale to very large memory stores → Mitigation: add garbage collection, plan for persistent backend in future proposal
- Single-process limits parallelism → Mitigation: use asyncio for concurrent agent execution within one process
- Dynamic tool generation via LLM could produce unsafe tools → Mitigation: sandboxed Docker execution, tool validation before registration

## Migration Plan
N/A - greenfield implementation.

## Open Questions
- Should the CLI entry point use Click or Typer? (Leaning Typer for type-hint integration)
- Exact Mem0 integration points (deferred to separate proposal)
- LangGraph integration for workflow orchestration (evaluate after core is working)
