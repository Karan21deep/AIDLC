import json
import os

from openai import OpenAI

from models.discovery_models import (
    RepositoryDiscoveryReport
)

from tools.repository_scanner import (
    scan_repository,
    collect_project_content,
    detect_wcf
)


class RepositoryDiscoveryAgent:

    def __init__(self):

        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )

        self.model = os.getenv(
            "OPENAI_MODEL",
            "gpt-5.5"
        )

    def run(
        self,
        repo_path: str
    ) -> RepositoryDiscoveryReport:

        print(
            "Scanning repository..."
        )

        metadata = scan_repository(
            repo_path
        )

        project_content = (
            collect_project_content(
                repo_path,
                metadata["project_files"]
            )
        )

        wcf_info = detect_wcf(
            root=__import__(
                "pathlib"
            ).Path(repo_path),
            files=metadata["files"]
        )

        repository_context = {

            "repository_metadata":
                metadata,

            "project_files":
                project_content,

            "wcf_analysis":
                wcf_info,
        }

        prompt = self._build_prompt(
            repository_context
        )

        print(
            "Sending repository metadata to OpenAI..."
        )

        response = self.client.responses.parse(

            model=self.model,

            instructions=self._system_prompt(),

            input=prompt,

            text_format=RepositoryDiscoveryReport,
        )

        report = response.output_parsed

        if report is None:

            raise RuntimeError(
                "OpenAI did not return a "
                "structured discovery report."
            )

        return report

    def _system_prompt(self) -> str:

        return """
                You are a senior software architect specializing
                in legacy .NET and WCF modernization.

                You are the Repository Discovery Agent.

                Your responsibility is to analyze a repository
                and create a reliable repository-level inventory.

                You must:

                        1. Understand the repository structure.
                        2. Identify solution files.
                        3. Identify .NET projects.
                        4. Identify target frameworks.
                        5. Identify project dependencies.
                        6. Identify WCF services.
                        7. Identify ServiceContract and OperationContract.
                        8. Identify WCF bindings.
                        9. Identify endpoints.
                        10. Identify configuration files.
                        11. Identify test projects.
                        12. Identify architectural layers.
                        13. Identify common design patterns.
                        14. Identify database indicators.
                        15. Identify external dependencies.
                        16. Identify modernization risks.

                IMPORTANT:

                    Do not invent information.

                    Only make conclusions supported by the
                    repository metadata and project files.

                    If something cannot be determined,
                    state that it is unknown.

                    This is the discovery phase.

                    DO NOT generate migration code.

                    DO NOT modify the repository.

                    DO NOT assume that every .NET Framework
                    application should become REST.

                    The output will be consumed by other
                    specialized agents.
                """

    def _build_prompt(
        self,
        repository_context: dict
        ) -> str:

        return f"""
                Analyze the following repository metadata.

                REPOSITORY INFORMATION
                ======================

                {json.dumps(
                    repository_context,
                    indent=2
                        )}

                Create a repository discovery report.

                Focus on:

                - repository structure
                - projects
                - project relationships
                - WCF services
                - configuration
                - architecture
                - dependencies
                - database indicators
                - tests
                - risks
                - modernization observations

                Remember:
                This is discovery only.
                 Do not generate migration code.
                    """