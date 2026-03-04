## ADDED Requirements

### Requirement: Shared Memory Communication
Agents SHALL communicate primarily through the shared MemoryGraph. An agent writes its results as memory nodes; dependent agents query the graph to retrieve those results before executing their own tasks.

#### Scenario: Result sharing via memory
- **WHEN** an agent completes a subtask and writes results to the memory graph
- **THEN** any dependent agent SHALL be able to query the graph for those results using the task relationship edges

#### Scenario: Implicit request-response
- **WHEN** agent B depends on agent A's output
- **THEN** agent B SHALL wait for agent A's result nodes to appear in the memory graph before proceeding with its own execution

### Requirement: Message Bus
The system SHALL provide a lightweight MessageBus for synchronization signals between agents, handling events such as task completion, errors, and shutdown requests without carrying full data payloads.

#### Scenario: Task completion signal
- **WHEN** an agent completes its assigned task
- **THEN** it SHALL publish a TaskCompleted message on the bus with its AgentId and TaskId

#### Scenario: Error signal
- **WHEN** an agent encounters a fatal error
- **THEN** it SHALL publish a TaskFailed message on the bus with the error details, enabling the parent agent or engine to handle the failure

#### Scenario: Shutdown coordination
- **WHEN** the AgentEngine initiates shutdown
- **THEN** it SHALL broadcast a Shutdown message on the bus, and all active agents SHALL complete their current step and terminate gracefully

### Requirement: Message Types
The system SHALL define a fixed set of message types for the MessageBus: TaskCompleted, TaskFailed, TaskStarted, AgentSpawned, ShutdownRequest, and custom extension messages.

#### Scenario: Message type validation
- **WHEN** a message is published to the bus
- **THEN** it SHALL conform to one of the defined message types with required fields (sender, timestamp, type-specific payload)

#### Scenario: Message subscription
- **WHEN** an agent subscribes to specific message types on the bus
- **THEN** it SHALL receive only messages matching its subscription filter

### Requirement: Result Aggregation
The system SHALL support aggregating results from multiple parallel agent streams into a unified output, combining findings from the memory graph according to the task DAG structure.

#### Scenario: Parallel result merge
- **WHEN** multiple sibling agents complete their subtasks
- **THEN** the parent agent SHALL query the memory graph for all child results and combine them into a coherent output following the task DAG ordering

#### Scenario: Conflict resolution
- **WHEN** parallel agents produce contradictory results for related subtasks
- **THEN** the parent agent SHALL use its LLM to evaluate and resolve the conflict, recording the resolution as a new Discovery node in the memory graph
