# Legacy .NET / WCF Modernization Agent

## Overview

This project provides an AI-assisted modernization pipeline for analyzing and modernizing legacy **.NET / WCF applications**.

The pipeline combines deterministic repository analysis, C# code parsing, dependency mapping, WCF analysis, LLM-based reasoning, code generation, and automated validation.

## Architecture

```text
Legacy .NET / WCF Repository
            |
            v
Repository Discovery
            |
            v
Architecture Analysis
            |
            v
Code Understanding
            |
            v
Dependency Mapping
            |
            v
WCF Analysis
            |
            v
Modernization Plan
            |
            v
Code Generation
            |
            v
Validation
            |
            v
Modernized Repository
```

# Agents

## 1. Repository Discovery Agent

Analyzes the repository structure and identifies:

- Solution and project files
- Target frameworks
- Project references and dependencies
- WCF services and contracts
- WCF bindings and endpoints
- Configuration files
- Test projects
- Architectural layers
- External dependencies
- Database indicators
- Modernization risks

**Output:** `output/discovery_report.json`

---

## 2. Architecture Analysis Agent

Analyzes the application's architecture using repository discovery information.

Responsibilities include:

- Architecture style
- Application layers
- Project responsibilities
- Major components
- Communication patterns
- Data-access patterns
- External integrations
- Design patterns
- Architectural risks

**Input:** `discovery_report.json`

**Output:** `output/architecture_report.json`

---

## 3. Code Understanding Agent

Performs detailed C# source-code analysis.

Responsibilities include:

- Namespace and using analysis
- Class and interface identification
- Method identification
- Class responsibilities
- Method purpose
- Business logic
- Dependencies
- Method calls
- Database operations
- External services
- Exception handling
- WCF operations
- Design patterns
- Modernization observations

### Technologies

- Tree-sitter
- tree-sitter-c-sharp
- Python
- OpenAI structured outputs

### Caching

Successful file analyses are cached in:

```text
output/code_analysis_cache.json
```

Source-file hashes are used to avoid unnecessarily reprocessing unchanged files.

---

## 4. Dependency Mapping Agent

Creates a deterministic dependency graph from Code Understanding results.

**This agent does not use an LLM.**

It identifies:

- File dependencies
- Class dependencies
- Method dependencies
- Method calls
- Inheritance
- Interface implementation
- External dependencies
- Unresolved dependencies

The dependency graph contains:

```text
File
  |
  +-- Class
        |
        +-- Method
```

**Output:** `output/dependency_mapping.json`

---

## 5. WCF Analysis Agent

Analyzes legacy Windows Communication Foundation components.

### Input

```text
discovery_report.json
architecture_report.json
code_analysis_cache.json
dependency_mapping.json
```

### Responsibilities

- WCF services
- Service contracts
- Operations
- Endpoints
- Bindings
- Hosting
- Security
- WCF configuration
- Communication patterns
- Migration considerations
- Compatibility risks

**Output:** `output/wcf_analysis.json`

The agent analyzes WCF but does not generate the replacement implementation.

---

## 6. Modernization Agent

Creates the modernization strategy and implementation plan.

### Input

```text
discovery_report.json
architecture_report.json
code_analysis_cache.json
dependency_mapping.json
wcf_analysis.json
```

### Responsibilities

- Target modernization strategy
- Target framework
- Target architecture
- Legacy-to-modern technology mappings
- Affected projects and components
- Dependency modernization
- WCF modernization
- Migration phases
- Prerequisites
- Validation strategy
- Risks
- Assumptions
- Human-review items

**Output:** `output/modernization_plan.json`

The Modernization Agent is a planning/reasoning agent. It does not directly generate source code.

---

## 7. Code Generation Agent

Converts the modernization plan into modernized source code.

For affected files, the LLM receives focused context:

```text
Original source code
        +
Modernization plan
        +
Architecture
        +
File-specific code analysis
        +
Relevant dependencies
        +
WCF analysis
```

Responsibilities:

- Generate modernized C# code
- Preserve existing business behavior
- Follow the modernization plan
- Apply target-framework requirements
- Modernize WCF components according to the plan
- Preserve required public APIs
- Avoid unrelated refactoring
- Identify warnings when information is insufficient

Unaffected files are copied unchanged.

### Cache

```text
output/code_generation_cache.json
```

### Outputs

```text
output/generated_code/
output/code_generation_report.json
```

---

## 8. Validation Agent

Validates the generated repository.

### Deterministic validation

The agent can execute:

```text
dotnet restore
dotnet build
dotnet test
```

It collects:

- Build errors
- Error codes
- File paths
- Line numbers
- Compiler output
- Test counts
- Passed tests
- Failed tests
- Skipped tests
- Test output

### Semantic validation

The LLM can compare:

```text
Original source
        vs
Generated source
```

It checks:

- Business behavior preservation
- Public API behavior
- Method behavior
- Database operations
- Exception behavior
- Authentication/authorization
- WCF operation semantics
- Serialization
- External calls
- Configuration
- Dependency injection
- Async behavior
- Modernization-plan compliance

**Output:** `output/validation_report.json`

---

# Models

The project uses Pydantic models for structured contracts between pipeline stages.

## Discovery Models

Represent repository, project, dependency, WCF, configuration, test, architecture, and risk information.

**Output:** `discovery_report.json`

## Architecture Models

Represent:

- Architecture style
- Architecture summary
- Layers
- Projects
- Components
- Communication patterns
- Data-access patterns
- External integrations
- Design patterns
- Risks

**Output:** `architecture_report.json`

## Code Understanding Models

Key models include:

### `DependencyInfo`

Represents a source-code dependency.

### `DesignPatternInfo`

Represents an identified design pattern and supporting evidence.

### `ModernizationObservation`

Represents a modernization observation and recommendation.

### `MethodAnalysis`

Represents:

- Method name
- Return type
- Parameters
- Purpose
- Business logic
- Dependencies
- Methods called
- Database operations
- External services
- Exceptions
- WCF operations
- Complexity observations

### `ClassAnalysis`

Represents:

- Class name
- Class type
- Namespace
- Base classes
- Interfaces
- Responsibilities
- Dependencies
- Methods
- Design patterns
- WCF relationship

### `FileAnalysis`

Represents:

- File path
- Project
- Namespace
- File purpose
- Usings
- Classes
- Dependencies
- Database relationship
- WCF relationship
- External integrations
- Modernization observations

### `CodeUnitAnalysis`

Represents analysis of a parsed code unit.

---

## Dependency Models

The Dependency Mapping Agent uses:

```text
DependencyNode
DependencyEdge
FileDependency
ClassDependency
MethodDependency
DependencyMappingReport
```

These represent the dependency graph at file, class, and method levels.

---

## WCF Models

Represent:

- WCF files
- Contracts
- Services
- Operations
- Endpoints
- Bindings
- Hosting
- Security
- Migration considerations
- Risks

**Output:** `wcf_analysis.json`

---

## Modernization Models

The Modernization Agent uses:

```text
ModernizationMapping
ProjectModernization
WCFModernization
DependencyModernization
MigrationPhase
ValidationStrategy
ModernizationPlan
```

These models represent the complete modernization strategy.

---

## Code Generation Models

The Code Generation Agent uses:

```text
GeneratedFile
FileGenerationRecord
CodeGenerationReport
```

These track:

- Source file
- Target file
- Generated code
- Changes
- Preserved behavior
- Warnings
- Generation status
- Source hash
- Plan hash
- Cache status

---

## Validation Models

The Validation Agent uses:

```text
BuildError
TestResult
SemanticValidation
FileValidationResult
ValidationReport
```

---

# Tools and Technologies

## Python

Primary implementation language for:

- Agent orchestration
- Repository scanning
- C# parsing
- Dependency analysis
- LLM integration
- File processing
- Validation
- Report generation

## OpenAI

Used for LLM-based reasoning and source-code generation.

The project uses the OpenAI Python SDK and Responses API with structured Pydantic outputs where applicable.

Example:

```python
client.responses.parse(
    model=model,
    input=[...],
    text_format=SomePydanticModel,
)
```

Model configuration:

```env
OPENAI_MODEL=gpt-5.5
```

## Tree-sitter

Used for deterministic C# source-code parsing.

It identifies structural elements such as:

```text
Namespace
Using
Class
Interface
Method
```

## tree-sitter-c-sharp

Provides the C# grammar used by Tree-sitter.

## Pydantic

Used for:

- Data validation
- Typed models
- Structured LLM responses
- JSON serialization
- Contracts between pipeline stages

## python-dotenv

Loads environment variables from `.env`.

Example:

```env
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-5.5
SOURCE_REPOSITORY_PATH=D:\projects\legacy-wcf-project
```

The repository path can also be entered dynamically through the Streamlit UI.

## Streamlit

Provides the user interface for:

- Repository path input
- Repository validation
- C# file count
- Pipeline execution
- Stage progress
- Pipeline logs
- Modernization statistics
- Validation results
- Generated file listing
- JSON report viewing
- Report downloads

Run:

```powershell
streamlit run streamlit_app.py
```

## .NET CLI

Used by the Validation Agent for deterministic validation:

```powershell
dotnet restore
dotnet build
dotnet test
```

## FAISS

The broader AI/RAG stack can use FAISS for:

- Vector indexing
- Similarity search
- Retrieval of semantically related content

## LangChain

The broader RAG stack can use:

```text
LangChain
langchain_community
FAISS vector store
RetrievalQA
ConversationalRetrievalChain
```

---

# Project Directory Structure

```text
wcf-modernization-agent/
│
├── .env
├── requirements.txt
├── main.py
├── streamlit_app.py
│
├── agents/
│   ├── repository_discovery_agent.py
│   ├── architecture_analysis_agent.py
│   ├── code_understanding_agent.py
│   ├── dependency_mapping_agent.py
│   ├── wcf_analysis_agent.py
│   ├── modernization_agent.py
│   ├── code_generation_agent.py
│   └── validation_agent.py
│
├── models/
│   ├── discovery_models.py
│   ├── architecture_models.py
│   ├── code_models.py
│   ├── dependency_models.py
│   ├── wcf_models.py
│   ├── modernization_models.py
│   ├── code_generation_models.py
│   └── validation_models.py
│
├── tools/
│   ├── repository_scanner.py
│   ├── architecture_scanner.py
│   ├── csharp_parser.py
│   ├── code_filter.py
│   ├── code_chunker.py
│   └── code_context_builder.py
│
└── output/
    ├── discovery_report.json
    ├── architecture_report.json
    ├── code_analysis_cache.json
    ├── dependency_mapping.json
    ├── wcf_analysis.json
    ├── modernization_plan.json
    ├── code_generation_cache.json
    ├── code_generation_report.json
    ├── validation_report.json
    └── generated_code/
```

---

# Pipeline Data Flow

```text
Repository
    |
    v
Discovery
    |
    | discovery_report.json
    v
Architecture
    |
    | architecture_report.json
    v
Code Understanding
    |
    | code_analysis_cache.json
    v
Dependency Mapping
    |
    | dependency_mapping.json
    v
WCF Analysis
    |
    | wcf_analysis.json
    v
Modernization Planning
    |
    | modernization_plan.json
    v
Code Generation
    |
    | generated_code/
    v
Validation
    |
    | validation_report.json
    v
Modernized Repository
```

---

# LLM Usage Strategy

The pipeline does not use an LLM for every operation.

| Stage | LLM | Main Purpose |
|---|---|---|
| Repository Discovery | Yes | Repository-level understanding |
| Architecture Analysis | Yes | Architecture reasoning |
| Code Understanding | Yes | Code and business-logic understanding |
| Dependency Mapping | No | Deterministic dependency graph |
| WCF Analysis | Yes | WCF understanding and migration analysis |
| Modernization Plan | Yes | Migration strategy |
| Code Generation | Yes | Modernized source generation |
| Restore / Build / Test | No | Deterministic validation |
| Semantic Validation | Yes | Source and behavior comparison |

This approach reduces unnecessary LLM calls and keeps deterministic tasks deterministic.

---

# Output Artifacts

```text
output/
├── discovery_report.json
├── architecture_report.json
├── code_analysis_cache.json
├── dependency_mapping.json
├── wcf_analysis.json
├── modernization_plan.json
├── code_generation_cache.json
├── code_generation_report.json
├── validation_report.json
└── generated_code/
```

---

# Key Design Principles

## Analyze Before Generating

```text
Discover
   ↓
Understand
   ↓
Map
   ↓
Plan
   ↓
Generate
   ↓
Validate
```

## Deterministic First, LLM Second

Use deterministic tools whenever reasoning is not required:

```text
C# Parsing       → Tree-sitter
Dependency Map   → Deterministic analysis
Build            → dotnet build
Tests            → dotnet test
```

## Focused Context

The system avoids blindly sending an entire repository to the LLM.

The Code Generation Agent receives relevant context for the specific file being generated.

## Preserve Unaffected Files

Files not affected by the modernization plan are copied unchanged.

## Cache Successful Work

Source hashes and generation information are used to avoid repeating expensive analysis and generation operations.

## Separate Planning From Generation

The Modernization Agent creates the plan.

The Code Generation Agent executes the plan.

## Validate Generated Code

Generated code is validated through:

```text
Restore
   ↓
Build
   ↓
Tests
   ↓
Semantic Validation
```

---

# Getting Started

Install dependencies:

```powershell
pip install -r requirements.txt
```

Configure `.env`:

```env
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-5.5
```

Optionally configure a default repository:

```env
SOURCE_REPOSITORY_PATH=D:\projects\legacy-wcf-project
```

Run:

```powershell
streamlit run streamlit_app.py
```

Enter the legacy repository path in the Streamlit UI and start the modernization pipeline.
