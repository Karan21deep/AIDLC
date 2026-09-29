import json
import os

from pathlib import Path
from typing import Optional, List

from openai import OpenAI

from pydantic import BaseModel, Field

from models.modernization_models import (
    ModernizationMapping,
    ProjectModernization,
    WCFModernization,
    DependencyModernization,
    MigrationPhase,
    ValidationStrategy,
    ModernizationPlan
)


# =========================================================
# LLM Output Model
# =========================================================
#
# The LLM analyzes the complete modernization context and
# returns a structured modernization plan.
#
# Pydantic guarantees that the response follows the expected
# structure.
# =========================================================

class ModernizationLLMOutput(BaseModel):

    # Current architecture.
    current_architecture: Optional[str] = None

    # Target architecture.
    target_architecture: Optional[str] = None

    # Current framework.
    current_framework: Optional[str] = None

    # Target framework.
    target_framework: Optional[str] = None

    # Overall strategy.
    migration_strategy: str

    # Project recommendations.
    projects: List[
        ProjectModernization
    ] = Field(
        default_factory=list
    )

    # Component mappings.
    component_mappings: List[
        ModernizationMapping
    ] = Field(
        default_factory=list
    )

    # WCF mappings.
    wcf_modernization: List[
        WCFModernization
    ] = Field(
        default_factory=list
    )

    # Dependency mappings.
    dependency_modernization: List[
        DependencyModernization
    ] = Field(
        default_factory=list
    )

    # Migration phases.
    migration_phases: List[
        MigrationPhase
    ] = Field(
        default_factory=list
    )

    # Validation strategy.
    validation_strategy: List[
        ValidationStrategy
    ] = Field(
        default_factory=list
    )

    # Risks.
    risks: List[str] = Field(
        default_factory=list
    )

    # Assumptions.
    assumptions: List[str] = Field(
        default_factory=list
    )

    # Items requiring human review.
    human_review_items: List[str] = Field(
        default_factory=list
    )


# =========================================================
# Modernization Agent
# =========================================================

class ModernizationAgent:

    """
    =========================================================
    MODERNIZATION AGENT
    =========================================================

    Purpose:

        Create a modernization strategy for a legacy
        .NET/WCF repository.

    Input:

        discovery_report.json
        architecture_report.json
        code_analysis_cache.json
        dependency_mapping.json
        wcf_analysis.json

    Output:

        ModernizationPlan

    IMPORTANT:

        This agent does NOT generate source code.

        It determines:

            WHAT needs to change
            WHY it needs to change
            WHAT technology should replace it
            IN WHAT ORDER it should be migrated

        A later Code Generation Agent will implement
        the actual changes.

    =========================================================
    """

    # =====================================================
    # Constructor
    # =====================================================

    def __init__(
        self,
        model: Optional[str] = None
    ):

        # Initialize OpenAI client.
        self.client = OpenAI()

        # Read model from environment.
        self.model = (
            model
            or os.getenv(
                "OPENAI_MODEL",
                "gpt-5.5"
            )
        )

    # =====================================================
    # Load JSON
    # =====================================================

    def _load_json(
        self,
        path: str
    ) -> dict:

        """
        Load one of the previously generated JSON reports.
        """

        file_path = Path(
            path
        )

        if not file_path.exists():

            raise FileNotFoundError(
                f"Required file not found: {path}"
            )

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(
                file
            )

    # =====================================================
    # Build Modernization Plan
    # =====================================================

    def build_plan(
        self,
        discovery_report_path: str,
        architecture_report_path: str,
        code_cache_path: str,
        dependency_mapping_path: str,
        wcf_analysis_path: str
    ) -> ModernizationPlan:

        """
        Main method.

        It loads all previous agent outputs and sends a
        consolidated context to the Modernization Agent.

        The Modernization Agent does NOT inspect the raw
        repository directly.

        It works from structured analysis generated by
        previous stages.
        """

        # -------------------------------------------------
        # Load previous reports.
        # -------------------------------------------------

        discovery_report = self._load_json(
            discovery_report_path
        )

        architecture_report = self._load_json(
            architecture_report_path
        )

        code_cache = self._load_json(
            code_cache_path
        )

        dependency_mapping = self._load_json(
            dependency_mapping_path
        )

        wcf_analysis = self._load_json(
            wcf_analysis_path
        )

        # -------------------------------------------------
        # Build a compact Code Understanding summary.
        #
        # We don't want to send all source code again.
        #
        # The previous agent has already converted source
        # code into structured information.
        # -------------------------------------------------

        code_summary = (
            self._build_code_summary(
                code_cache
            )
        )

        # -------------------------------------------------
        # Build prompt.
        # -------------------------------------------------

        prompt = self._build_prompt(

            discovery_report,

            architecture_report,

            code_summary,

            dependency_mapping,

            wcf_analysis
        )

        # -------------------------------------------------
        # Call OpenAI using structured output.
        # -------------------------------------------------

        response = self.client.responses.parse(

            model=self.model,

            input=[

                {
                    "role": "system",

                    "content":
                        self._system_prompt()
                },

                {
                    "role": "user",

                    "content":
                        prompt
                }

            ],

            text_format=
                ModernizationLLMOutput
        )

        # -------------------------------------------------
        # Extract structured response.
        # -------------------------------------------------

        result = (
            response.output_parsed
        )

        if result is None:

            raise RuntimeError(
                "OpenAI returned no structured "
                "modernization plan."
            )

        # -------------------------------------------------
        # Convert LLM output into final report.
        # -------------------------------------------------

        return ModernizationPlan(
            repository_name=
                discovery_report.get(
                    "repository_name"
                ),

            current_architecture=
                result.current_architecture,

            target_architecture=
                result.target_architecture,

            current_framework=
                result.current_framework,

            target_framework=
                result.target_framework,

            migration_strategy=
                result.migration_strategy,

            projects=
                result.projects,

            component_mappings=
                result.component_mappings,

            wcf_modernization=
                result.wcf_modernization,

            dependency_modernization=
                result.dependency_modernization,

            migration_phases=
                result.migration_phases,

            validation_strategy=
                result.validation_strategy,

            risks=
                result.risks,

            assumptions=
                result.assumptions,

            human_review_items=
                result.human_review_items
        )

    # =====================================================
    # Build Code Summary
    # =====================================================

    def _build_code_summary(
        self,
        code_cache: dict
    ) -> dict:

        """
        Convert the large Code Understanding cache into a
        compact summary.

        We don't need to send every low-level detail to the
        Modernization Agent.

        Important information includes:

            files
            projects
            namespaces
            classes
            responsibilities
            WCF flags
            database flags
            external integrations
            modernization observations
        """

        files = []

        successful = 0

        failed = 0

        for file_path, entry in code_cache.items():

            # Ignore invalid cache entries.
            if not isinstance(
                entry,
                dict
            ):

                continue

            # Ignore failed files.
            if entry.get(
                "status"
            ) != "success":

                failed += 1

                continue

            successful += 1

            result = entry.get(
                "result"
            )

            if not isinstance(
                result,
                dict
            ):

                continue

            # -------------------------------------------------
            # Build class summary.
            # -------------------------------------------------

            classes = []

            for class_info in result.get(
                "classes",
                []
            ):

                classes.append({

                    "name":
                        class_info.get(
                            "name"
                        ),

                    "class_type":
                        class_info.get(
                            "class_type"
                        ),

                    "namespace":
                        class_info.get(
                            "namespace"
                        ),

                    "base_classes":
                        class_info.get(
                            "base_classes",
                            []
                        ),

                    "interfaces":
                        class_info.get(
                            "interfaces",
                            []
                        ),

                    "responsibilities":
                        class_info.get(
                            "responsibilities",
                            []
                        ),

                    "wcf_related":
                        class_info.get(
                            "wcf_related",
                            False
                        ),

                    "design_patterns":
                        class_info.get(
                            "design_patterns",
                            []
                        ),

                    "method_count":
                        len(
                            class_info.get(
                                "methods",
                                []
                            )
                        )
                })

            # -------------------------------------------------
            # Store compact file information.
            # -------------------------------------------------

            files.append({

                "file_path":
                    result.get(
                        "file_path"
                    ),

                "project":
                    result.get(
                        "project"
                    ),

                "namespace":
                    result.get(
                        "namespace"
                    ),

                "file_purpose":
                    result.get(
                        "file_purpose"
                    ),

                "database_related":
                    result.get(
                        "database_related",
                        False
                    ),

                "wcf_related":
                    result.get(
                        "wcf_related",
                        False
                    ),

                "external_integrations":
                    result.get(
                        "external_integrations",
                        []
                    ),

                "modernization_observations":
                    result.get(
                        "modernization_observations",
                        []
                    ),

                "classes":
                    classes
            })

        return {

            "successful_files":
                successful,

            "failed_files":
                failed,

            "files":
                files
        }

    # =====================================================
    # System Prompt
    # =====================================================

    def _system_prompt(self) -> str:

        """
        Instructions for the Modernization Agent.

        This is deliberately different from the Code
        Generation Agent.

        The Modernization Agent plans.

        It does not implement.
        """

        return """
You are a Senior .NET Modernization Architect.

You specialize in:

- legacy .NET Framework applications
- modern .NET
- ASP.NET Core
- WCF
- enterprise application modernization
- layered architecture
- dependency analysis
- database-heavy applications
- automated migration planning
- test modernization

Your job is to create a modernization plan based ONLY
on the supplied repository analysis.

You are NOT a code generation agent.

DO NOT generate:

- C# migration code
- controller implementations
- service implementations
- project files
- configuration files
- complete source files

Instead determine:

1. Current architecture
2. Target architecture
3. Current framework
4. Target framework
5. Components that need modernization
6. WCF migration strategy
7. Dependency migration strategy
8. Project migration strategy
9. Migration order
10. Validation strategy
11. Risks
12. Human review requirements

=========================================================
IMPORTANT
=========================================================

Do not assume every WCF service should be migrated using
the same technology.

Evaluate each service based on:

- contract structure
- operation semantics
- bindings
- security
- clients
- dependencies
- communication requirements
- existing architecture

Distinguish between:

FACT:
Information directly present in the supplied analysis.

INFERENCE:
A relationship reasonably inferred from the supplied
dependency/code analysis.

RECOMMENDATION:
A proposed modernization direction.

Do not invent missing information.

If something cannot be determined:

Use "Unknown".

=========================================================
TARGET FRAMEWORK
=========================================================

If the supplied repository information does not explicitly
identify the desired target .NET version, do not invent a
specific version.

Use:

"Modern .NET"

and explain that the exact target version should be
confirmed.

=========================================================
WCF
=========================================================

Analyze:

- ServiceContract
- OperationContract
- Service implementation
- endpoints
- bindings
- behaviors
- security
- hosting
- clients
- dependencies

Determine an appropriate modernization direction for each
WCF component.

=========================================================
DEPENDENCIES
=========================================================

Identify dependencies that should be:

- retained
- replaced
- removed
- refactored
- reviewed

Do not recommend replacing a dependency without evidence
that it needs replacement.

=========================================================
MIGRATION PHASES
=========================================================

Create an ordered migration strategy.

Consider:

1. Foundation/project setup
2. Shared models/contracts
3. Domain/application layers
4. Data access
5. WCF service migration
6. Tests
7. Integration
8. Validation
9. Decommissioning legacy components

Adjust this order according to the actual repository.

=========================================================
VALIDATION
=========================================================

Preserving behavior is important.

Identify:

- unit tests
- integration tests
- contract tests
- regression tests
- API behavior validation
- database behavior validation

Do not assume that a migration is successful simply
because the new application builds.

=========================================================
OUTPUT
=========================================================

Return structured information.

Do not generate source code.
"""

    # =====================================================
    # Build Prompt
    # =====================================================

    def _build_prompt(
        self,
        discovery_report: dict,
        architecture_report: dict,
        code_summary: dict,
        dependency_mapping: dict,
        wcf_analysis: dict
    ) -> str:

        """
        Build the complete context for the Modernization
        Agent.

        The context comes entirely from previous agents.
        """

        return f"""
Create a modernization plan for this legacy .NET
repository.

=========================================================
REPOSITORY DISCOVERY
=========================================================

{json.dumps(
    discovery_report,
    indent=2,
    default=str
)}

=========================================================
ARCHITECTURE ANALYSIS
=========================================================

{json.dumps(
    architecture_report,
    indent=2,
    default=str
)}

=========================================================
CODE UNDERSTANDING SUMMARY
=========================================================

{json.dumps(
    code_summary,
    indent=2,
    default=str
)}

=========================================================
DEPENDENCY MAPPING
=========================================================

{json.dumps(
    dependency_mapping,
    indent=2,
    default=str
)}

=========================================================
WCF ANALYSIS
=========================================================

{json.dumps(
    wcf_analysis,
    indent=2,
    default=str
)}

=========================================================
TASK
=========================================================

Create a detailed modernization plan.

The plan must explain:

1. Current architecture

2. Target architecture

3. Current framework

4. Target framework

5. Project modernization

6. Component modernization

7. WCF modernization

8. Dependency modernization

9. Migration phases

10. Validation strategy

11. Risks

12. Assumptions

13. Items requiring human review

Do not generate migration code.

Do not invent repository information.

Use "Unknown" when information is unavailable.
"""
