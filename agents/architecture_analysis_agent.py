import json
import os

from openai import OpenAI

from models.architecture_models import (
    ArchitectureAnalysisReport
)

from tools.architecture_scanner import (
    scan_architecture
)


class ArchitectureAnalysisAgent:

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

    def run(
        self,
        repo_path: str,
        discovery_report_path: str
    ) -> ArchitectureAnalysisReport:

        # ------------------------------------------
        # 1. Load Repository Discovery Report
        # ------------------------------------------

        discovery_report = (
            self._load_discovery_report(
                discovery_report_path
            )
        )

        # ------------------------------------------
        # 2. Extract project paths
        # ------------------------------------------

        project_files = [
            project["path"]
            for project
            in discovery_report.get(
                "projects",
                []
            )
        ]

        # ------------------------------------------
        # 3. Deterministic architecture scan
        # ------------------------------------------

        architecture_metadata = (
            scan_architecture(
                repo_path,
                project_files
            )
        )

        # ------------------------------------------
        # 4. Build LLM context
        # ------------------------------------------

        context = {

            "discovery_report":
                discovery_report,

            "architecture_metadata":
                architecture_metadata
        }

        prompt = self._build_prompt(
            context
        )

        # ------------------------------------------
        # 5. Ask OpenAI to reason about architecture
        # ------------------------------------------

        response = self.client.responses.parse(

            model=self.model,

            instructions=self._system_prompt(),

            input=prompt,

            text_format=ArchitectureAnalysisReport
        )

        report = response.output_parsed

        if report is None:

            raise RuntimeError(
                "Architecture Analysis Agent "
                "did not return a structured report."
            )

        return report

    # ==================================================
    # Load discovery report
    # ==================================================

    def _load_discovery_report(
        self,
        path: str
    ) -> dict:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    # ==================================================
    # System prompt
    # ==================================================

    def _system_prompt(self) -> str:

        return """
You are a Senior Software Architect specializing
in legacy .NET Framework and WCF modernization.

You are the Architecture Analysis Agent.

Your job is to understand the architecture of an
existing repository.

The repository has already been scanned by a
Repository Discovery Agent.

You will receive:

1. Repository discovery information.
2. Project structure.
3. Project references.
4. Target framework information.
5. Package references.
6. Directory and file structure.

Your responsibility is to determine:

- Overall architecture style.
- Architectural layers.
- Project responsibilities.
- Project-to-project dependencies.
- Major components.
- Entry points.
- Communication patterns.
- Data access components.
- External integrations.
- Design patterns.
- Architecture risks.
- Modernization observations.

IMPORTANT RULES:

1. Do not invent information.

2. Base conclusions on evidence from the supplied
   repository information.

3. If something cannot be determined, explicitly
   state that it cannot be determined.

4. Do not generate migration code.

5. Do not modify the repository.

6. Do not assume REST is automatically the target
   architecture.

7. Do not assume a particular modernization pattern
   without evidence.

8. Distinguish clearly between:
   - observed facts
   - architectural interpretation
   - modernization recommendation.

9. Identify dependencies between projects.

10. Identify possible architectural layers from:
    - project names
    - folder names
    - namespaces
    - project references
    - source file organization.

11. Identify patterns only when there is reasonable
    evidence.

12. Pay special attention to WCF service projects.

This is an architecture understanding phase.
"""
    
    # ==================================================
    # Prompt builder
    # ==================================================

    def _build_prompt(
        self,
        context: dict
    ) -> str:

        return f"""
Analyze the following repository.

====================================================
REPOSITORY DISCOVERY REPORT
====================================================

{json.dumps(
    context["discovery_report"],
    indent=2
)}

====================================================
ARCHITECTURE METADATA
====================================================

{json.dumps(
    context["architecture_metadata"],
    indent=2
)}

====================================================
TASK
====================================================

Create a complete architecture analysis.

Determine:

1. Overall architecture style.

2. Architectural layers.

3. Project responsibilities.

4. Project dependencies.

5. Important components.

6. Entry points.

7. Communication patterns.

8. Data access components.

9. External integrations.

10. Design patterns.

11. Architecture risks.

12. Modernization observations.

For every architectural conclusion,
use the available repository evidence.

Do not create migration code.

Do not invent missing information.
"""