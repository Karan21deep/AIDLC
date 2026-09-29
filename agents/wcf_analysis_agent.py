import json
from typing import List, Optional

from pathlib import Path
from typing import Optional

from openai import OpenAI

from models.wcf_models import (
    WCFOperation,
    WCFContractAnalysis,
    WCFServiceAnalysis,
    WCFEndpointAnalysis,
    WCFBindingAnalysis,
    WCFMigrationRecommendation,
    WCFAnalysisReport
)


class WCFAnalysisAgent:

    """
    =========================================================
    WCF ANALYSIS AGENT
    =========================================================

    Purpose:

        Analyze WCF components in a legacy .NET repository.

    Input:

        1. discovery_report.json
        2. architecture_report.json
        3. code_analysis_cache.json
        4. dependency_mapping.json

    Output:

        WCFAnalysisReport

    Important:

        This agent does NOT generate migration code.

        It only analyzes the existing WCF implementation and
        creates migration-oriented observations.

    =========================================================
    """

    # =====================================================
    # Constructor
    # =====================================================

    def __init__(
        self,
        model: Optional[str] = None
    ):

        # Create OpenAI client.

        self.client = OpenAI()

        # Read model from environment if one is not
        # explicitly provided.

        import os

        self.model = (
            model
            or os.getenv(
                "OPENAI_MODEL",
                "gpt-5.5"
            )
        )

        # -------------------------------------------------
        # These structures are populated during analysis.
        # -------------------------------------------------

        self.wcf_files = []

        self.contracts = []

        self.services = []

        self.endpoints = []

        self.bindings = []

        self.recommendations = []

        self.observations = []

        self.risks = []

        self.unresolved_items = []

    # =====================================================
    # Load JSON
    # =====================================================

    def _load_json(
        self,
        path: str
    ) -> dict:

        """
        Load a JSON file.

        This helper is used for:

            discovery_report.json
            architecture_report.json
            code_analysis_cache.json
            dependency_mapping.json
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
    # Find WCF Files
    # =====================================================

    def _find_wcf_files(
        self,
        discovery_report: dict,
        code_cache: dict
    ) -> list:

        """
        Identify files that are likely to contain WCF code.

        We use both:

            1. Discovery report
            2. Code Understanding results

        This is more reliable than looking only at filenames.
        """

        wcf_files = set()

        # -------------------------------------------------
        # Use repository discovery information.
        # -------------------------------------------------

        wcf_info = discovery_report.get(
            "wcf",
            {}
        )

        for file_path in wcf_info.get(
            "service_files",
            []
        ):

            wcf_files.add(
                str(file_path)
            )

        for file_path in wcf_info.get(
            "contracts",
            []
        ):

            wcf_files.add(
                str(file_path)
            )

        # -------------------------------------------------
        # Inspect Code Understanding cache.
        # -------------------------------------------------

        for file_path, entry in code_cache.items():

            if not isinstance(
                entry,
                dict
            ):
                continue

            # Ignore failed analyses.
            if entry.get(
                "status"
            ) != "success":

                continue

            result = entry.get(
                "result"
            )

            if not isinstance(
                result,
                dict
            ):
                continue

            # Explicit WCF flag.
            if result.get(
                "wcf_related"
            ) is True:

                wcf_files.add(
                    file_path
                )

                continue

            # Search classes.
            for class_info in result.get(
                "classes",
                []
            ):

                if class_info.get(
                    "wcf_related"
                ) is True:

                    wcf_files.add(
                        file_path
                    )

                    break

            # Search WCF-specific fields.
            result_text = json.dumps(
                result,
                default=str
            ).lower()

            wcf_keywords = [

                "servicecontract",

                "operationcontract",

                "servicebehavior",

                "wcf",

                "endpoint",

                "binding",

                "servicehost",

                "channel"

            ]

            if any(
                keyword in result_text
                for keyword in wcf_keywords
            ):

                wcf_files.add(
                    file_path
                )

        return sorted(
            wcf_files
        )

    # =====================================================
    # Analyze Repository
    # =====================================================

    def analyze_repository(
        self,
        discovery_report_path: str,
        architecture_report_path: str,
        code_cache_path: str,
        dependency_mapping_path: str
    ) -> WCFAnalysisReport:

        """
        Main repository-level WCF analysis.

        Steps:

            1. Load existing reports.
            2. Identify WCF files.
            3. Extract relevant code.
            4. Analyze WCF contracts/services.
            5. Analyze endpoints/bindings.
            6. Generate migration recommendations.
            7. Build final report.
        """

        # -------------------------------------------------
        # Load existing artifacts.
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

        # -------------------------------------------------
        # Find WCF files.
        # -------------------------------------------------

        wcf_files = self._find_wcf_files(

            discovery_report,

            code_cache
        )

        self.wcf_files = wcf_files

        print(
            f"\nDetected {len(wcf_files)} "
            f"potential WCF files."
        )

        # -------------------------------------------------
        # Analyze code belonging to WCF files.
        # -------------------------------------------------

        for file_path in wcf_files:

            analysis = code_cache.get(
                file_path
            )

            # Cache keys may have normalized paths.
            if analysis is None:

                analysis = self._find_cache_entry(
                    code_cache,
                    file_path
                )

            if not analysis:

                self.unresolved_items.append(
                    f"No code analysis found for: "
                    f"{file_path}"
                )

                continue

            if analysis.get(
                "status"
            ) != "success":

                self.unresolved_items.append(
                    f"Code analysis failed for: "
                    f"{file_path}"
                )

                continue

            result = analysis.get(
                "result"
            )

            if not result:

                continue

            # -------------------------------------------------
            # Analyze the WCF file using OpenAI.
            # -------------------------------------------------

            self._analyze_wcf_file(

                result,

                discovery_report,

                architecture_report,

                dependency_mapping
            )

        # -------------------------------------------------
        # Analyze WCF configuration.
        # -------------------------------------------------

        self._analyze_wcf_configuration(
            discovery_report
        )

        # -------------------------------------------------
        # Build final report.
        # -------------------------------------------------

        return WCFAnalysisReport(

            repository_name=
                discovery_report.get(
                    "repository_name"
                ),

            wcf_detected=
                len(self.wcf_files) > 0,

            wcf_files=
                self.wcf_files,

            contracts=
                self.contracts,

            services=
                self.services,

            endpoints=
                self.endpoints,

            bindings=
                self.bindings,

            migration_recommendations=
                self.recommendations,

            observations=
                self.observations,

            risks=
                self.risks,

            unresolved_items=
                self.unresolved_items
        )

    # =====================================================
    # Analyze Individual WCF File
    # =====================================================

    def _analyze_wcf_file(
        self,
        code_analysis: dict,
        discovery_report: dict,
        architecture_report: dict,
        dependency_mapping: dict
    ):

        """
        Send only the relevant WCF code context to the LLM.

        We do NOT send the entire repository.

        The LLM receives:

            Repository WCF information
            Architecture information
            Code analysis
            Relevant dependency graph
        """

        prompt = self._build_prompt(

            code_analysis,

            discovery_report,

            architecture_report,

            dependency_mapping
        )

        try:

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

                text_format=WCFFileLLMAnalysis
            )

            parsed = response.output_parsed

            if parsed is None:

                return

            self._merge_llm_result(
                parsed
            )

        except Exception as error:

            file_path = code_analysis.get(
                "file_path",
                "Unknown"
            )

            self.unresolved_items.append(

                f"Failed to analyze WCF file "
                f"{file_path}: {error}"
            )

    # =====================================================
    # System Prompt
    # =====================================================

    def _system_prompt(self) -> str:

        """
        System instructions for the WCF specialist.

        The agent is explicitly prevented from generating
        migration code.

        Its job is analysis and migration mapping only.
        """

        return """
You are a Senior .NET and WCF Migration Analysis Agent.

Your responsibility is to analyze an existing legacy WCF
implementation.

You specialize in:

- C#
- .NET Framework
- WCF
- ServiceContract
- OperationContract
- ServiceBehavior
- InstanceContextMode
- ConcurrencyMode
- WCF endpoints
- WCF bindings
- WCF configuration
- service implementation classes
- service contracts
- WCF clients
- dependency relationships
- legacy enterprise applications

IMPORTANT:

You are NOT a code generation agent.

Do NOT rewrite the source code.

Do NOT generate migration code.

Analyze only the supplied information.

Determine:

1. WCF service contracts
2. WCF service implementations
3. WCF operations
4. Dependencies
5. WCF configuration
6. Endpoint information
7. Binding information
8. Security-related configuration
9. Hosting-related information
10. Important migration considerations
11. Risks
12. Recommended modern .NET target technology

For migration recommendations:

Do not assume that every WCF service should use the
same target technology.

Base recommendations on the actual characteristics
of the supplied WCF implementation.

Clearly distinguish:

- observed facts
- inferred relationships
- migration considerations

Do not invent missing configuration or behavior.

If information is unavailable, use "Unknown".

Do not generate source code.
"""

    # =====================================================
    # Build Prompt
    # =====================================================

    def _build_prompt(
        self,
        code_analysis: dict,
        discovery_report: dict,
        architecture_report: dict,
        dependency_mapping: dict
    ) -> str:

        """
        Build the context sent to the WCF specialist LLM.

        We intentionally keep the context focused on WCF
        rather than sending the entire repository.
        """

        return f"""
Analyze the following WCF-related component.

=========================================================
REPOSITORY WCF INFORMATION
=========================================================

{json.dumps(
    discovery_report.get(
        "wcf",
        {}
    ),
    indent=2,
    default=str
)}

=========================================================
ARCHITECTURE
=========================================================

{json.dumps(
    {
        "architecture_style":
            architecture_report.get(
                "architecture_style"
            ),

        "architecture_summary":
            architecture_report.get(
                "architecture_summary"
            ),

        "layers":
            architecture_report.get(
                "layers",
                []
            ),

        "components":
            architecture_report.get(
                "components",
                []
            )
    },
    indent=2,
    default=str
)}

=========================================================
CODE ANALYSIS
=========================================================

{json.dumps(
    code_analysis,
    indent=2,
    default=str
)}

=========================================================
DEPENDENCY INFORMATION
=========================================================

{json.dumps(
    self._get_relevant_dependencies(
        code_analysis,
        dependency_mapping
    ),
    indent=2,
    default=str
)}

=========================================================
TASK
=========================================================

Analyze this WCF component.

Identify:

1. Service contracts
2. Service implementations
3. WCF operations
4. Dependencies
5. Endpoint relationships
6. Binding relationships
7. Hosting characteristics
8. Security characteristics
9. Important WCF behavior
10. Risks
11. Migration considerations
12. Recommended modern .NET target technology

Do not generate migration code.

Do not invent information.

If information is not available, use "Unknown".
"""

    # =====================================================
    # Get Relevant Dependencies
    # =====================================================

    def _get_relevant_dependencies(
        self,
        code_analysis: dict,
        dependency_mapping: dict
    ) -> dict:

        """
        Extract only dependency graph information related
        to the current WCF file.

        This prevents unnecessarily large prompts.
        """

        file_path = code_analysis.get(
            "file_path"
        )

        if not file_path:

            return {}

        relevant_edges = []

        for edge in dependency_mapping.get(
            "edges",
            []
        ):

            source_file = edge.get(
                "source_file"
            )

            target_file = edge.get(
                "target_file"
            )

            if (
                source_file == file_path
                or target_file == file_path
            ):

                relevant_edges.append(
                    edge
                )

        return {
            "edges":
                relevant_edges
        }

    # =====================================================
    # Merge LLM Result
    # =====================================================

    def _merge_llm_result(
        self,
        result
    ):

        """
        Merge structured LLM output into the final report
        collections.

        The result is already validated by Pydantic.
        """

        # -------------------------------------------------
        # Contracts
        # -------------------------------------------------

        self.contracts.extend(
            result.contracts
        )

        # -------------------------------------------------
        # Services
        # -------------------------------------------------

        self.services.extend(
            result.services
        )

        # -------------------------------------------------
        # Endpoints
        # -------------------------------------------------

        self.endpoints.extend(
            result.endpoints
        )

        # -------------------------------------------------
        # Bindings
        # -------------------------------------------------

        self.bindings.extend(
            result.bindings
        )

        # -------------------------------------------------
        # Migration recommendations
        # -------------------------------------------------

        self.recommendations.extend(
            result.migration_recommendations
        )

        # -------------------------------------------------
        # General observations
        # -------------------------------------------------

        self.observations.extend(
            result.observations
        )

        # -------------------------------------------------
        # Risks
        # -------------------------------------------------

        self.risks.extend(
            result.risks
        )

        # -------------------------------------------------
        # Unresolved items
        # -------------------------------------------------

        self.unresolved_items.extend(
            result.unresolved_items
        )

    # =====================================================
    # Analyze WCF Configuration
    # =====================================================

    def _analyze_wcf_configuration(
        self,
        discovery_report: dict
    ):

        """
        Extract WCF configuration information already found
        by the Repository Discovery Agent.

        This method does not call OpenAI.

        The Discovery Agent already identified:

            bindings
            endpoints
            configuration files
        """

        wcf_info = discovery_report.get(
            "wcf",
            {}
        )

        # -------------------------------------------------
        # Configuration files
        # -------------------------------------------------

        configuration_files = (
            wcf_info.get(
                "configuration_files",
                []
            )
        )

        # -------------------------------------------------
        # Bindings
        # -------------------------------------------------

        for binding in wcf_info.get(
            "bindings",
            []
        ):

            self.bindings.append(

                WCFBindingAnalysis(

                    name=str(
                        binding
                    ),

                    binding_type=None,

                    configuration_file=(
                        configuration_files[0]
                        if configuration_files
                        else None
                    ),

                    configuration=[],

                    security=[],

                    migration_considerations=[]
                )
            )

        # -------------------------------------------------
        # Endpoints
        # -------------------------------------------------

        for endpoint in wcf_info.get(
            "endpoints",
            []
        ):

            self.endpoints.append(

                WCFEndpointAnalysis(

                    name=None,

                    contract=str(
                        endpoint
                    ),

                    binding=None,

                    address=None,

                    configuration_file=(
                        configuration_files[0]
                        if configuration_files
                        else None
                    ),

                    observations=[]
                )
            )

    # =====================================================
    # Find Cache Entry
    # =====================================================

    def _find_cache_entry(
        self,
        cache: dict,
        file_path: str
    ):

        """
        Find a Code Understanding cache entry when the
        exact path representation differs.

        This is useful on Windows where path separators
        may be represented differently.
        """

        normalized_target = (
            str(
                Path(
                    file_path
                ).resolve()
            ).lower()
        )

        for cached_path, entry in cache.items():

            try:

                normalized_cached = (
                    str(
                        Path(
                            cached_path
                        ).resolve()
                    ).lower()
                )

                if normalized_cached == normalized_target:

                    return entry

            except Exception:

                continue

        return None


# =========================================================
# LLM Output Models
# =========================================================
#
# These models are intentionally defined separately from
# WCFAnalysisReport.
#
# The LLM analyzes ONE WCF file at a time.
#
# The results are then aggregated into the final
# WCFAnalysisReport.
# =========================================================

from pydantic import BaseModel, Field


class WCFFileLLMAnalysis(BaseModel):

    # Contracts discovered in the file.
    contracts: List[
        WCFContractAnalysis
    ] = Field(
        default_factory=list
    )

    # Services discovered in the file.
    services: List[
        WCFServiceAnalysis
    ] = Field(
        default_factory=list
    )

    # Endpoints discovered in the file.
    endpoints: List[
        WCFEndpointAnalysis
    ] = Field(
        default_factory=list
    )

    # Bindings discovered in the file.
    bindings: List[
        WCFBindingAnalysis
    ] = Field(
        default_factory=list
    )

    # Migration recommendations.
    migration_recommendations: List[
        WCFMigrationRecommendation
    ] = Field(
        default_factory=list
    )

    # General observations.
    observations: List[str] = Field(
        default_factory=list
    )

    # Risks.
    risks: List[str] = Field(
        default_factory=list
    )

    # Items that could not be determined.
    unresolved_items: List[str] = Field(
        default_factory=list
    )