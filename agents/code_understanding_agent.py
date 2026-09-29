import json
import os
from tools.code_filter import classify_file


from openai import OpenAI

from models.code_models import (
    FileAnalysis,
    CodeUnitAnalysis,
    ClassAnalysis,
    DependencyInfo,
    DesignPatternInfo,
    ModernizationObservation
)

from tools.csharp_parser import (
    parse_csharp_file
)

from tools.code_chunker import (
    build_code_units
)

from tools.code_context_builder import (
    build_code_context
)

from models.code_models import (
    FileAnalysis,
    CodeUnitAnalysis
)

from tools.csharp_parser import (
    parse_csharp_file
)

from tools.code_chunker import (
    build_code_units
)

from tools.code_context_builder import (
    build_code_context
)


class CodeUnderstandingAgent:

    def __init__(self):

        self.client = OpenAI(
            api_key=os.getenv(
                "OPENAI_API_KEY"
            )
        )

        self.model = os.getenv(
            "OPENAI_MODEL",
            "gpt-5.5"
        )


    def _ensure_string_list(
        self,
        value
        ) -> list[str]:

        if value is None:

            return []

        if not isinstance(
            value,
            list
        ):

            value = [value]

        result = []

        for item in value:

            if isinstance(
                item,
                str
            ):

                result.append(
                    item
                )

            elif isinstance(
                item,
                dict
            ):

                # Prefer name when available
                if item.get("name"):

                    result.append(
                        str(
                            item["name"]
                        )
                    )

                elif item.get("pattern"):

                    result.append(
                        str(
                            item["pattern"]
                        )
                    )

                else:

                    result.append(
                        json.dumps(
                            item,
                            default=str
                        )
                    )

            else:

                result.append(
                    str(item)
                )

        return result

    def _convert_dependencies(
        self,
        dependencies
    ) -> list:

        result = []

        if not dependencies:

            return result

        if not isinstance(
            dependencies,
            list
        ):

            dependencies = [
                dependencies
            ]

        for dependency in dependencies:

            if isinstance(
                dependency,
                dict
            ):

                result.append(
                    DependencyInfo(

                        name=str(
                            dependency.get(
                                "name",
                                "Unknown"
                            )
                        ),

                        dependency_type=
                            dependency.get(
                                "dependency_type",
                                dependency.get(
                                    "type"
                                )
                            ),

                        description=
                            dependency.get(
                                "description"
                            )
                    )
                )

            elif isinstance(
                dependency,
                str
            ):

                result.append(
                    DependencyInfo(
                        name=dependency
                    )
                )

        return result

    def _convert_design_patterns(
        self,
        patterns
    ) -> list:

        result = []

        if not patterns:

            return result

        if not isinstance(
            patterns,
            list
        ):

            patterns = [
                patterns
            ]

        for pattern in patterns:

            if isinstance(
                pattern,
                dict
            ):

                result.append(
                    DesignPatternInfo(

                        pattern=str(
                            pattern.get(
                                "pattern",
                                pattern.get(
                                    "name",
                                    "Unknown"
                                )
                            )
                        ),

                        evidence=
                            pattern.get(
                                "evidence"
                            ),

                        description=
                            pattern.get(
                                "description"
                            )
                    )
                )

            elif isinstance(
                pattern,
                str
            ):

                result.append(
                    DesignPatternInfo(
                        pattern=pattern
                    )
                )

        return result


    def _convert_modernization_observations(
        self,
        observations
    ) -> list:

        result = []

        if not observations:

            return result

        if not isinstance(
            observations,
            list
        ):

            observations = [
                observations
            ]

        for observation in observations:

            if isinstance(
                observation,
                dict
            ):

                result.append(
                    ModernizationObservation(

                        area=str(
                            observation.get(
                                "area",
                                "Unknown"
                            )
                        ),

                        observation=str(
                            observation.get(
                                "observation",
                                ""
                            )
                        ),

                        recommendation=
                            observation.get(
                                "recommendation"
                            )
                    )
                )

            elif isinstance(
                observation,
                str
            ):

                result.append(
                    ModernizationObservation(

                        area="General",

                        observation=observation
                    )
                )

        return result

















    # =================================================
    # Analyze a single C# file
    # =================================================

    def analyze_file(
        self,
        file_path: str,
        discovery_report: dict,
        architecture_report: dict
    ) -> FileAnalysis:

        # ---------------------------------------------
        # 1. Parse C# using AST
        # ---------------------------------------------

        parsed_file = parse_csharp_file(
            file_path
        )

        # ---------------------------------------------
        # 2. Split into code units
        # ---------------------------------------------

        code_units = build_code_units(
            parsed_file
        )

        # ---------------------------------------------
        # 3. Analyze each unit
        # ---------------------------------------------

        unit_results = []

        for unit in code_units:

            context = build_code_context(
                discovery_report,
                architecture_report,
                unit
            )

            result = self._analyze_unit(
                context
            )

            unit_results.append(
                result
            )

        # ---------------------------------------------
        # 4. Aggregate into file analysis
        # ---------------------------------------------

        return self._aggregate_file_analysis(
            parsed_file,
            unit_results
        )

    # =================================================
    # LLM analysis of individual unit
    # =================================================

    def _analyze_unit(
        self,
        context: dict
    ) -> dict:

        prompt = self._build_unit_prompt(
            context
        )

        response = self.client.responses.create(

            model=self.model,

            instructions=self._system_prompt(),

            input=prompt
        )

        text = response.output_text

        try:

            return json.loads(text)

        except json.JSONDecodeError:

            return {

                "unit_type":
                    context[
                        "code_unit"
                    ].get(
                        "unit_type"
                    ),

                "analysis_error":
                    "LLM returned invalid JSON",

                "raw_response":
                    text
            }

    # =================================================
    # System prompt
    # =================================================

    def _system_prompt(self):

        return """
You are a Senior .NET Code Understanding Agent.

You specialize in:

- C#
- .NET Framework
- WCF
- MSTest
- NMock
- enterprise applications
- legacy modernization

Your job is to understand existing code.

You are NOT a code generation agent.

You MUST NOT rewrite the code.

You MUST NOT invent behavior.

Analyze only the supplied source code and
repository context.

Determine:

- purpose
- responsibilities
- dependencies
- method behavior
- business logic
- database interactions
- external service calls
- WCF interactions
- exception handling
- design patterns
- modernization observations

The code may belong to:

- WCF service
- application layer
- business layer
- domain layer
- data access layer
- mapping layer
- DTO/model layer
- unit tests
- infrastructure
- utility/common library

Identify the actual type based on evidence.

For unit tests, identify:

- test framework
- mocking framework
- class under test
- dependencies being mocked
- test methods
- behavior being verified

For every dependency return:

{
    "name": "...",
    "dependency_type": "...",
    "description": "..."
}

For every design pattern return:

{
    "pattern": "...",
    "evidence": "...",
    "description": "..."
}

For every modernization observation return:

{
    "area": "...",
    "observation": "...",
    "recommendation": "..."
}

Do not invent information.

If information cannot be determined, use
"Unknown".

Do not generate migration code.
"""
    # =================================================
    # Prompt
    # =================================================

    def _build_unit_prompt(
        self,
        context: dict
    ) -> str:

        return f"""
    Analyze this C# code unit.

==================================================
REPOSITORY
==================================================

{json.dumps(
    context["repository"],
    indent=2,
    default=str
)}

==================================================
ARCHITECTURE
==================================================

{json.dumps(
    context["architecture"],
    indent=2,
    default=str
)}

==================================================
FILE TYPE
==================================================

{context.get("file_type", "Unknown")}

==================================================
CODE UNIT
==================================================

{json.dumps(
    context["code_unit"],
    indent=2,
    default=str
)}

==================================================
TASK
==================================================

Understand the supplied code.

Determine:

1. Purpose
2. Responsibilities
3. Dependencies
4. Methods called
5. Business logic
6. Database operations
7. External services
8. Exception handling
9. WCF operations
10. Design patterns
11. Modernization observations

==================================================
DEPENDENCY FORMAT
==================================================

Every dependency must be an object:

{{
    "name": "DependencyName",
    "dependency_type": "interface/class/library/framework",
    "description": "Why this dependency is used"
}}

==================================================
DESIGN PATTERN FORMAT
==================================================

Every design pattern must be:

{{
    "pattern": "Pattern Name",
    "evidence": "Evidence from the source code",
    "description": "How the pattern is used"
}}

==================================================
MODERNIZATION OBSERVATION FORMAT
==================================================

Every modernization observation must be:

{{
    "area": "Area being discussed",
    "observation": "What is observed in the existing code",
    "recommendation": "Potential modernization consideration"
}}

==================================================
IMPORTANT
==================================================

Do not invent information.

If something cannot be determined, use:

"Unknown"

Do not generate migration code.

Do not rewrite the source code.

Analyze the existing implementation only.
"""
    # =================================================
    # Aggregate
    # =================================================

    def _aggregate_file_analysis(
        self,
        parsed_file: dict,
        unit_results: list
    ) -> FileAnalysis:

        class_results = []

        all_dependencies = []

        all_modernization_observations = []

        all_external_integrations = []

        # =================================================
        # Process LLM results
        # =================================================

        for result in unit_results:

            if not isinstance(
                result,
                dict
            ):
                continue

            # ---------------------------------------------
            # Collect dependencies
            # ---------------------------------------------

            dependencies = result.get(
                "dependencies",
                []
            )

            if isinstance(
                dependencies,
                list
            ):

                all_dependencies.extend(
                    dependencies
                )

            # ---------------------------------------------
            # Collect modernization observations
            # ---------------------------------------------

            observations = result.get(
                "modernization_observations",
                []
            )

            if isinstance(
                observations,
                list
            ):

                all_modernization_observations.extend(
                    observations
                )

            # ---------------------------------------------
            # Collect external services
            # ---------------------------------------------

            external_services = result.get(
                "external_services",
                []
            )

            if isinstance(
                external_services,
                list
            ):

                all_external_integrations.extend(
                    external_services
                )

            # ---------------------------------------------
            # Only class results
            # ---------------------------------------------

            if result.get(
                "unit_type"
                ) != "class":

                continue

            # ---------------------------------------------
            # Build ClassAnalysis
            # ---------------------------------------------

            class_result = ClassAnalysis(

                name=result.get(
                    "name",
                    "Unknown"
                ),

                class_type=result.get(
                    "class_type",
                    "class"
                ),

                namespace=
                    parsed_file.get(
                        "namespace"
                    ),

                base_classes=
                    self._ensure_string_list(
                        result.get(
                            "base_classes",
                            []
                        )
                    ),

                interfaces=
                    self._ensure_string_list(
                        result.get(
                            "interfaces",
                            []
                        )
                    ),

                responsibilities=
                    self._ensure_string_list(
                        result.get(
                            "responsibilities",
                            []
                        )
                    ),

                dependencies=
                    self._convert_dependencies(
                        dependencies
                    ),

                methods=[],

                design_patterns=
                    self._convert_design_patterns(
                        result.get(
                            "design_patterns",
                            []
                        )
                    ),

                wcf_related=
                    bool(
                        result.get(
                            "wcf_operations",
                            []
                        )
                    )
            )

            class_results.append(
                class_result
            )

        # =================================================
        # Build FileAnalysis
        # =================================================

        all_text = json.dumps(
            unit_results,
            default=str
        ).lower()

        return FileAnalysis(

        file_path=
            parsed_file[
                "file_path"
            ],

        namespace=
            parsed_file.get(
                "namespace"
            ),

        file_purpose=
            self._derive_file_purpose(
                unit_results
            ),

        usings=
            self._ensure_string_list(
                parsed_file.get(
                    "usings",
                    []
                )
            ),

        classes=
            class_results,

        dependencies=
            self._convert_dependencies(
                all_dependencies
            ),

        database_related=
            self._contains_any(
                all_text,
                [
                    "sql",
                    "database",
                    "entityframework",
                    "dbcontext",
                    "repository"
                ]
            ),

        wcf_related=
            self._contains_any(
                all_text,
                [
                    "wcf",
                    "servicecontract",
                    "operationcontract",
                    "endpoint",
                    "binding"
                ]
            ),

        external_integrations=
            self._ensure_string_list(
                all_external_integrations
            ),

        modernization_observations=
            self._convert_modernization_observations(
                all_modernization_observations
            )
    )

    # =================================================
    # Helpers
    # =================================================

    def _ensure_list(
        self,
        value
    ) -> list:

        if value is None:
            return []

        if isinstance(
            value,
            list
        ):
            return value

        return [value]



    def _safe_string(self, value) -> str:
        if value is None:
            return ""

        if isinstance(value, str):
            return value

        if isinstance(value, dict):
            return (
                value.get("description")
                or value.get("purpose")
                or value.get("name")
                or value.get("pattern")
                or value.get("observation")
                or str(value)
            )

        return str(value)

    def _derive_file_purpose(self, unit_results: list) -> str:

        purposes = []

        for result in unit_results:
            if not isinstance(result, dict):
                continue

            purpose = result.get("purpose")

            if purpose:
                value = self._safe_string(purpose)

                if value.strip():
                    purposes.append(value.strip())

        if not purposes:
            return "Unknown"

        return "; ".join(
            dict.fromkeys(purposes)
        )
    
    def _unique_values(self,results: list,key: str) -> list:
        """
        Collect unique values from LLM results.

        Handles both strings and dictionaries so that
        unhashable dict values do not cause:

            TypeError: unhashable type: 'dict'
        """

        values = []

        seen = set()

        for result in results:

            items = result.get(
                key,
                []
            )

            # ---------------------------------------------
            # Make sure we have a list
            # ---------------------------------------------

            if not isinstance(items, list):

                items = [items]

            for value in items:

                # -----------------------------------------
                # Dictionary value
                # -----------------------------------------

                if isinstance(value, dict):

                    # Convert dictionary into stable JSON
                    # representation for duplicate detection.

                    normalized = json.dumps(
                        value,
                        sort_keys=True,
                        default=str
                    )

                    if normalized not in seen:

                        seen.add(
                            normalized
                        )

                        values.append(
                            value
                        )

                # -----------------------------------------
                # List value
                # -----------------------------------------

                elif isinstance(value, list):

                    normalized = json.dumps(
                        value,
                        sort_keys=True,
                        default=str
                    )

                    if normalized not in seen:

                        seen.add(
                            normalized
                        )

                        values.append(
                            value
                        )

                # -----------------------------------------
                # Normal string / number / boolean
                # -----------------------------------------

                else:

                    normalized = str(
                        value
                    )

                    if normalized not in seen:

                        seen.add(
                            normalized
                        )

                        values.append(
                            value
                        )

        return values
    
    def _contains_any(
        self,
        text: str,
        values: list
    ) -> bool:

        return any(
            value.lower()
            in text
            for value in values
        )