## ADDED Requirements

### Requirement: Memory Graph Data Structure
The system SHALL provide a MemoryGraph implemented as a directed acyclic graph where nodes store typed information chunks and edges encode semantic or causal relationships between them.

#### Scenario: Node creation
- **WHEN** an agent writes information to the memory graph
- **THEN** a new MemoryNode SHALL be created with a unique NodeId, a typed payload, the creating agent's AgentId, a timestamp, and optional relationship edges to existing nodes

#### Scenario: Edge creation
- **WHEN** a memory node is related to existing nodes
- **THEN** directed edges SHALL be created from the new node to related nodes with a labeled relationship type (e.g., "derived_from", "depends_on", "supersedes")

#### Scenario: DAG enforcement
- **WHEN** an edge would create a cycle in the graph
- **THEN** the system SHALL reject the edge and raise an error

### Requirement: Typed Memory Nodes
The system SHALL support four memory node types: TaskContext (current problem state and decomposition history), Discovery (findings about code, vulnerabilities, patterns), Execution (tool outputs and intermediate results), and Relationship (dependencies between subtasks and outcomes).

#### Scenario: TaskContext node
- **WHEN** a task is decomposed or updated
- **THEN** a TaskContext node SHALL be created capturing the task description, decomposition decisions, and assigned agent

#### Scenario: Discovery node
- **WHEN** an agent discovers a finding (code pattern, vulnerability, test case)
- **THEN** a Discovery node SHALL be created with the finding details and edges linking it to the originating task and any related discoveries

#### Scenario: Execution node
- **WHEN** a tool returns a result
- **THEN** an Execution node SHALL be created containing the tool name, parameters, output, and execution status

### Requirement: Memory Query and Traversal
The system SHALL provide query operations for traversing the memory graph: retrieving nodes by type, following relationship edges, finding related context for a given task, and full-text search across node payloads.

#### Scenario: Query by node type
- **WHEN** an agent queries the memory graph for all Discovery nodes
- **THEN** the system SHALL return all nodes of that type, optionally filtered by agent or time range

#### Scenario: Context retrieval for task
- **WHEN** an agent needs context for its current task
- **THEN** the system SHALL traverse the graph from the task's TaskContext node, following edges to gather related discoveries, execution results, and parent task context

#### Scenario: Related node traversal
- **WHEN** an agent queries for nodes related to a specific node
- **THEN** the system SHALL follow outgoing and incoming edges to return directly connected nodes with their relationship labels

### Requirement: Memory Garbage Collection
The system SHALL support garbage collection to manage memory growth in long-running sessions, removing nodes that are no longer reachable from active tasks or that exceed a configurable age threshold.

#### Scenario: Unreachable node cleanup
- **WHEN** garbage collection runs
- **THEN** nodes not reachable from any active task's context SHALL be candidates for removal

#### Scenario: Age-based cleanup
- **WHEN** a node exceeds the configured maximum age and is not pinned
- **THEN** it SHALL be eligible for garbage collection regardless of reachability
