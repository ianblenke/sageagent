## ADDED Requirements

### Requirement: Agent Lifecycle Management
The system SHALL provide an Agent base class that manages the full lifecycle of an agent: creation with a role definition, configuration with an LLM backend and toolset, execution of assigned tasks, and graceful termination with result reporting.

#### Scenario: Agent creation with role
- **WHEN** an AgentEngine creates a new agent with a role description and task assignment
- **THEN** the agent SHALL be initialized with a unique AgentId, the specified role, an LLM backend, and an empty local memory scope

#### Scenario: Agent execution loop
- **WHEN** an agent is started with a task
- **THEN** the agent SHALL enter an execution loop that: (1) queries its LLM backend with current context, (2) selects and invokes tools based on LLM output, (3) writes results to the memory graph, and (4) repeats until the task is complete or a termination condition is met

#### Scenario: Agent graceful termination
- **WHEN** an agent completes its task or reaches a configured timeout
- **THEN** the agent SHALL write its final results to the memory graph, release its resources, and report completion status to its parent agent

### Requirement: Agent Engine Orchestration
The system SHALL provide an AgentEngine that serves as the top-level orchestrator, wiring together the topology manager, tool registry, memory graph, and communication bus to coordinate multi-agent workflows.

#### Scenario: Task submission
- **WHEN** a user submits a task to the AgentEngine
- **THEN** the engine SHALL create a root agent, invoke the TopologyManager to decompose the task, and manage the resulting agent hierarchy until all subtasks complete

#### Scenario: Result aggregation
- **WHEN** all agents in a task hierarchy have completed
- **THEN** the engine SHALL aggregate results from the memory graph and return the combined output to the caller

### Requirement: LLM Backend Abstraction
The system SHALL provide an abstract LLMBackend interface with concrete implementations for Anthropic Claude and OpenAI, supporting text generation, structured output, and tool-use calling conventions.

#### Scenario: Claude backend generation
- **WHEN** an agent requests LLM generation using the Claude backend
- **THEN** the system SHALL call the Anthropic API with the agent's messages and return the response in a standardized format

#### Scenario: OpenAI backend generation
- **WHEN** an agent requests LLM generation using the OpenAI backend
- **THEN** the system SHALL call the OpenAI API with the agent's messages and return the response in the same standardized format

#### Scenario: Tool-use generation
- **WHEN** an agent requests generation with available tools
- **THEN** the LLM backend SHALL format the tool schemas according to the provider's tool-use convention and parse any tool-call responses into standardized ToolCall objects

### Requirement: Engine Configuration
The system SHALL support configuration via Pydantic models covering: LLM backend selection, API keys (from environment variables), max agent hierarchy depth, tool execution timeouts, and memory garbage collection thresholds.

#### Scenario: Configuration from environment
- **WHEN** the engine is initialized without explicit configuration
- **THEN** it SHALL load API keys from environment variables (ANTHROPIC_API_KEY, OPENAI_API_KEY) and apply sensible defaults for all other settings

#### Scenario: Depth limit enforcement
- **WHEN** an agent attempts to spawn a sub-agent that would exceed the configured max hierarchy depth
- **THEN** the engine SHALL reject the spawn request and instruct the agent to handle the subtask directly
