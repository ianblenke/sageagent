# Change: Add Core Architecture for SageAgent (OpenSage ADK)

## Why
SageAgent needs its foundational architecture to implement the OpenSage framework described in arxiv.org/abs/2602.16891. This proposal defines the five core capabilities that form the system: agent engine, topology manager, toolset generator, memory graph, and agent communication. Without these, no agent workflows can be built.

## What Changes
- Add **agent-engine** capability: core agent lifecycle (create, configure, execute, terminate), LLM backend abstraction, and the main orchestration loop
- Add **topology-manager** capability: self-generated agent hierarchies via recursive task decomposition into DAGs, dynamic sub-agent spawning with role specialization
- Add **toolset-generator** capability: dynamic tool creation, tool registry, tool wrapping/invocation with standardized interfaces, built-in SE tools (static analysis, fuzzing, debugging, Docker execution)
- Add **memory-graph** capability: directed acyclic graph for hierarchical memory with typed nodes (task context, discovery, execution, relationship), edge-based traversal, read/write/query operations, garbage collection
- Add **agent-communication** capability: inter-agent messaging via shared memory graph, task DAG synchronization, result aggregation from parallel agent streams

## Impact
- Affected specs: agent-engine, topology-manager, toolset-generator, memory-graph, agent-communication (all new)
- Affected code: entire `sageagent/` package (new)
- This is the foundational change; all future work builds on these capabilities
