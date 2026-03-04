## ADDED Requirements

### Requirement: Task Decomposition
The system SHALL provide a TaskDecomposer that uses an LLM to recursively break down complex tasks into a directed acyclic graph (DAG) of subtasks, identifying dependencies and assigning complexity scores.

#### Scenario: Single-step task
- **WHEN** the decomposer receives a task that is simple enough to execute directly
- **THEN** it SHALL return a TaskDAG with a single node and no decomposition

#### Scenario: Multi-step task decomposition
- **WHEN** the decomposer receives a complex task
- **THEN** it SHALL use the LLM to identify subtasks, determine their dependencies, and return a TaskDAG where nodes are subtasks and edges represent dependency ordering

#### Scenario: Dependency identification
- **WHEN** decomposing a task with interdependent steps
- **THEN** the decomposer SHALL correctly identify which subtasks must complete before others can start, enabling maximum parallelism for independent subtasks

### Requirement: Task DAG Data Structure
The system SHALL provide a TaskDAG class that represents the decomposition of a task as a directed acyclic graph with operations for topological traversal, dependency resolution, and status tracking.

#### Scenario: Topological ordering
- **WHEN** a TaskDAG is queried for execution order
- **THEN** it SHALL return subtasks in a valid topological order respecting all dependency edges

#### Scenario: Ready task identification
- **WHEN** the DAG is queried for tasks ready to execute
- **THEN** it SHALL return all tasks whose dependencies have been marked as complete

### Requirement: Dynamic Agent Spawning
The TopologyManager SHALL spawn specialized sub-agents for each subtask in the TaskDAG, assigning role descriptions derived from the subtask requirements and capability needs.

#### Scenario: Sub-agent creation
- **WHEN** a subtask is ready for execution
- **THEN** the TopologyManager SHALL create a new agent with a role description matching the subtask, assign it the appropriate tools, and start its execution

#### Scenario: Hierarchy depth enforcement
- **WHEN** a sub-agent attempts further decomposition that would exceed the configured maximum depth
- **THEN** the TopologyManager SHALL prevent spawning and instruct the agent to execute the subtask directly

#### Scenario: Parallel agent execution
- **WHEN** multiple independent subtasks are ready simultaneously
- **THEN** the TopologyManager SHALL spawn and execute their agents concurrently using asyncio
