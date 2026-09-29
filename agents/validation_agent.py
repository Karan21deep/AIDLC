import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from openai import OpenAI

from models.validation_models import (
    BuildError,
    FileValidationResult,
    SemanticValidation,
    TestResult,
    ValidationReport,
)


class ValidationAgent:
    """
    Validation Agent for the .NET modernization pipeline.

    Validation is performed in multiple layers:

        Layer 1:
            Repository/project discovery

        Layer 2:
            dotnet restore

        Layer 3:
            dotnet build

        Layer 4:
            Compiler error extraction

        Layer 5:
            dotnet test

        Layer 6:
            Source/generated file comparison

        Layer 7:
            LLM semantic validation

        Layer 8:
            Final validation report
    """

    def __init__(
        self,
        generated_repository: str,
        output_root: str = "output",
    ):
        self.generated_repository = Path(
            generated_repository
        ).resolve()

        self.output_root = Path(
            output_root
        )

        self.client = OpenAI()

        self.model = os.getenv(
            "OPENAI_MODEL",
            "gpt-5.5",
        )

    # ======================================================================
    # JSON helpers
    # ======================================================================

    def _load_json(self, path: str) -> Dict:
        """
        Load a JSON file.
        """

        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        with open(
            file_path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    def _save_json(
        self,
        path: Path,
        data: Dict,
    ):
        """
        Save JSON in readable format.
        """

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )

    # ======================================================================
    # Hash
    # ======================================================================

    def _file_hash(
        self,
        file_path: Path,
    ) -> str:
        """
        Calculate SHA-256 hash of a file.
        """

        sha256 = hashlib.sha256()

        with open(
            file_path,
            "rb",
        ) as file:

            while True:

                chunk = file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                sha256.update(chunk)

        return sha256.hexdigest()

    # ======================================================================
    # Command execution
    # ======================================================================

    def _run_command(
        self,
        command: List[str],
        cwd: Path,
        timeout: int = 600,
    ):
        """
        Execute a command inside the generated repository.

        stdout and stderr are captured so they can be included in the
        validation report.
        """

        try:

            process = subprocess.run(
                command,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            output = (
                process.stdout or ""
            )

            error_output = (
                process.stderr or ""
            )

            combined_output = (
                output +
                "\n" +
                error_output
            ).strip()

            return (
                process.returncode,
                combined_output,
            )

        except subprocess.TimeoutExpired as exc:

            return (
                -1,
                f"Command timed out after "
                f"{timeout} seconds.\n{exc}",
            )

        except FileNotFoundError as exc:

            return (
                -1,
                f"Command could not be executed: "
                f"{exc}",
            )

    # ======================================================================
    # Project discovery
    # ======================================================================

    def _find_projects(self) -> List[Path]:
        """
        Find .NET project files.

        Supports:
            .csproj
            .fsproj
            .vbproj
        """

        projects = []

        for extension in [
            "*.csproj",
            "*.fsproj",
            "*.vbproj",
        ]:

            projects.extend(
                self.generated_repository.rglob(
                    extension
                )
            )

        return sorted(
            set(projects)
        )

    # ======================================================================
    # Restore
    # ======================================================================

    def _restore_projects(
        self,
        projects: List[Path],
    ) -> Dict:
        """
        Run dotnet restore.

        Each project is restored independently so a failure can be tied
        to a specific project.
        """

        results = []

        for project in projects:

            relative_path = project.relative_to(
                self.generated_repository
            )

            print(
                f"[RESTORE] {relative_path}"
            )

            return_code, output = self._run_command(
                [
                    "dotnet",
                    "restore",
                    str(project),
                ],
                cwd=self.generated_repository,
            )

            results.append(
                {
                    "project": str(relative_path),
                    "return_code": return_code,
                    "output": output,
                }
            )

        failed = [
            result
            for result in results
            if result["return_code"] != 0
        ]

        return {
            "success": len(failed) == 0,
            "results": results,
        }

    # ======================================================================
    # Build
    # ======================================================================

    def _build_projects(
        self,
        projects: List[Path],
    ) -> Dict:
        """
        Run dotnet build for all projects.

        --no-restore is used because restore was already performed.
        """

        results = []

        for project in projects:

            relative_path = project.relative_to(
                self.generated_repository
            )

            print(
                f"[BUILD] {relative_path}"
            )

            return_code, output = self._run_command(
                [
                    "dotnet",
                    "build",
                    str(project),
                    "--no-restore",
                ],
                cwd=self.generated_repository,
            )

            results.append(
                {
                    "project": str(relative_path),
                    "return_code": return_code,
                    "output": output,
                }
            )

        failed = [
            result
            for result in results
            if result["return_code"] != 0
        ]

        return {
            "success": len(failed) == 0,
            "results": results,
        }

    # ======================================================================
    # Parse compiler errors
    # ======================================================================

    def _parse_build_errors(
        self,
        build_results: Dict,
    ) -> List[BuildError]:
        """
        Parse standard C# compiler errors.

        Typical compiler output:

            Program.cs(15,20): error CS1002: ; expected
        """

        errors = []

        pattern = re.compile(
            r"(?P<file>.*?\.cs)"
            r"\((?P<line>\d+),(?P<column>\d+)\)"
            r":\s*"
            r"(?P<severity>error|warning)"
            r"\s*"
            r"(?P<code>[A-Z]{2,}\d+)"
            r":\s*"
            r"(?P<message>.*)"
        )

        for result in build_results.get(
            "results",
            [],
        ):

            output = result.get(
                "output",
                "",
            )

            for line in output.splitlines():

                match = pattern.search(
                    line
                )

                if not match:
                    continue

                if (
                    match.group(
                        "severity"
                    ).lower()
                    != "error"
                ):
                    continue

                errors.append(
                    BuildError(
                        error_code=match.group(
                            "code"
                        ),
                        message=match.group(
                            "message"
                        ).strip(),
                        file_path=match.group(
                            "file"
                        ),
                        line=int(
                            match.group(
                                "line"
                            )
                        ),
                        column=int(
                            match.group(
                                "column"
                            )
                        ),
                        raw_output=line,
                    )
                )

        return errors

    # ======================================================================
    # Test discovery
    # ======================================================================

    def _find_test_projects(
        self,
        projects: List[Path],
    ) -> List[Path]:
        """
        Identify likely test projects.

        This is intentionally conservative.
        """

        test_projects = []

        for project in projects:

            name = project.name.lower()

            if (
                "test" in name
                or "tests" in name
            ):
                test_projects.append(
                    project
                )
                continue

            try:

                content = project.read_text(
                    encoding="utf-8",
                    errors="ignore",
                ).lower()

                if (
                    "microsoft.net.test.sdk"
                    in content
                    or "xunit"
                    in content
                    or "nunit"
                    in content
                    or "mstest.testadapter"
                    in content
                ):
                    test_projects.append(
                        project
                    )

            except Exception:
                continue

        return sorted(
            set(test_projects)
        )

    # ======================================================================
    # Test execution
    # ======================================================================

    def _run_tests(
        self,
        test_projects: List[Path],
    ) -> TestResult:
        """
        Execute dotnet test for all discovered test projects.
        """

        if not test_projects:

            return TestResult(
                command="dotnet test",
                status="NOT_FOUND",
                output=(
                    "No test project was detected."
                ),
            )

        combined_output = []

        overall_status = "PASSED"

        for project in test_projects:

            relative_path = project.relative_to(
                self.generated_repository
            )

            print(
                f"[TEST] {relative_path}"
            )

            return_code, output = (
                self._run_command(
                    [
                        "dotnet",
                        "test",
                        str(project),
                        "--no-restore",
                        "--no-build",
                    ],
                    cwd=self.generated_repository,
                )
            )

            combined_output.append(
                f"\n===== {relative_path} =====\n"
            )

            combined_output.append(
                output
            )

            if return_code != 0:
                overall_status = "FAILED"

        output = "\n".join(
            combined_output
        )

        total, passed, failed, skipped = (
            self._parse_test_summary(
                output
            )
        )

        return TestResult(
            command="dotnet test",
            status=overall_status,
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            output=output,
        )

    # ======================================================================
    # Parse test summary
    # ======================================================================

    def _parse_test_summary(
        self,
        output: str,
    ):
        """
        Parse common dotnet test summary.

        Example:

            Passed!  - Failed: 0, Passed: 10,
            Skipped: 1, Total: 11
        """

        patterns = {
            "failed": r"Failed:\s*(\d+)",
            "passed": r"Passed:\s*(\d+)",
            "skipped": r"Skipped:\s*(\d+)",
            "total": r"Total:\s*(\d+)",
        }

        values = {}

        for key, pattern in patterns.items():

            matches = re.findall(
                pattern,
                output,
                flags=re.IGNORECASE,
            )

            if matches:
                values[key] = int(
                    matches[-1]
                )
            else:
                values[key] = 0

        return (
            values["total"],
            values["passed"],
            values["failed"],
            values["skipped"],
        )

    # ======================================================================
    # Generated file discovery
    # ======================================================================

    def _find_generated_source_files(
        self,
    ) -> List[Path]:
        """
        Find generated C# files.
        """

        return sorted(
            self.generated_repository.rglob(
                "*.cs"
            )
        )

    # ======================================================================
    # Semantic validation prompt
    # ======================================================================

    def _semantic_system_prompt(self) -> str:
        return """
You are a Senior .NET Code Review Engineer.

You are reviewing code generated by an automated modernization system.

Compare the legacy source and generated source.

Determine whether the generated implementation preserves the important
behavior of the legacy implementation while following the modernization
plan.

Rules:

1. Do not invent requirements.

2. Only identify behavior differences that can be supported by the
   supplied code and modernization plan.

3. Distinguish:
   - actual defects
   - modernization changes
   - warnings
   - uncertain behavior

4. Pay particular attention to:
   - public APIs
   - method behavior
   - database operations
   - exception behavior
   - authentication/authorization
   - WCF operation semantics
   - serialization
   - external service calls
   - configuration
   - dependency injection
   - asynchronous behavior

5. A modernization change is not automatically a defect.

6. Do not require exact line-by-line equivalence.

7. Do not generate code.

8. Return only the structured SemanticValidation response.
"""

    # ======================================================================
    # Semantic validation
    # ======================================================================

    def _semantic_validate(
        self,
        source_file: str,
        original_code: str,
        generated_code: str,
        modernization_plan: Dict,
        code_analysis: Dict,
    ) -> SemanticValidation:
        """
        Ask the LLM to compare original and generated code.
        """

        prompt = f"""
Review this modernization.

SOURCE FILE:

{source_file}

ORIGINAL CODE:

{original_code}

GENERATED CODE:

{generated_code}

MODERNIZATION PLAN:

{json.dumps(
    modernization_plan,
    indent=2,
    ensure_ascii=False,
)}

CODE UNDERSTANDING:

{json.dumps(
    code_analysis,
    indent=2,
    ensure_ascii=False,
)}

Determine:

- whether important behavior appears preserved
- whether generated code follows the modernization intent
- whether there are semantic defects
- whether human review is required
"""

        response = self.client.responses.parse(
            model=self.model,

            input=[
                {
                    "role": "system",
                    "content": (
                        self._semantic_system_prompt()
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],

            text_format=SemanticValidation,
        )

        result = response.output_parsed

        if not result:
            raise RuntimeError(
                "No semantic validation returned."
            )

        return result

    # ======================================================================
    # Main validation
    # ======================================================================

    def validate(
        self,
        modernization_plan_path: str,
        code_analysis_cache_path: str,
    ) -> ValidationReport:
        """
        Execute the complete validation pipeline.
        """

        # ------------------------------------------------------------------
        # Validate generated repository
        # ------------------------------------------------------------------

        if not self.generated_repository.exists():

            raise FileNotFoundError(
                "Generated repository does not exist: "
                f"{self.generated_repository}"
            )

        modernization_plan = (
            self._load_json(
                modernization_plan_path
            )
        )

        code_cache = (
            self._load_json(
                code_analysis_cache_path
            )
        )

        # ------------------------------------------------------------------
        # Find projects
        # ------------------------------------------------------------------

        projects = self._find_projects()

        print(
            f"\nFound {len(projects)} .NET projects."
        )

        report = ValidationReport(
            repository_name=modernization_plan.get(
                "repository_name"
            ),
            generated_repository=str(
                self.generated_repository
            ),
            total_projects=len(projects),
        )

        # ------------------------------------------------------------------
        # No projects
        # ------------------------------------------------------------------

        if not projects:

            report.validation_status = "FAILED"

            report.global_issues.append(
                "No .NET project files were found "
                "in the generated repository."
            )

            self._save_report(
                report
            )

            return report

        # ------------------------------------------------------------------
        # RESTORE
        # ------------------------------------------------------------------

        print("\n" + "=" * 70)
        print("RESTORE")
        print("=" * 70)

        restore_result = (
            self._restore_projects(
                projects
            )
        )

        if not restore_result["success"]:

            report.global_issues.append(
                "One or more projects failed "
                "during dotnet restore."
            )

        # ------------------------------------------------------------------
        # BUILD
        # ------------------------------------------------------------------

        print("\n" + "=" * 70)
        print("BUILD")
        print("=" * 70)

        if restore_result["success"]:

            build_result = (
                self._build_projects(
                    projects
                )
            )

        else:

            # We still attempt build because some projects may have
            # partially restored successfully.
            build_result = (
                self._build_projects(
                    projects
                )
            )

        build_errors = (
            self._parse_build_errors(
                build_result
            )
        )

        report.build_output = "\n".join(
            result.get(
                "output",
                "",
            )
            for result in build_result.get(
                "results",
                [],
            )
        )

        report.build_errors_detail = (
            build_errors
        )

        report.build_errors = len(
            build_errors
        )

        if build_result["success"]:

            report.build_status = "PASSED"

        else:

            report.build_status = "FAILED"

            report.global_issues.append(
                "Generated repository failed "
                "dotnet build."
            )

        # ------------------------------------------------------------------
        # TEST
        # ------------------------------------------------------------------

        print("\n" + "=" * 70)
        print("TEST")
        print("=" * 70)

        test_projects = (
            self._find_test_projects(
                projects
            )
        )

        test_result = (
            self._run_tests(
                test_projects
            )
        )

        report.test_result = test_result

        report.test_status = (
            test_result.status
        )

        report.test_output = (
            test_result.output
        )

        report.tests_total = (
            test_result.total_tests or 0
        )

        report.tests_passed = (
            test_result.passed or 0
        )

        report.tests_failed = (
            test_result.failed or 0
        )

        report.tests_skipped = (
            test_result.skipped or 0
        )

        if test_result.status == "FAILED":

            report.global_issues.append(
                "One or more automated tests failed."
            )

        # ------------------------------------------------------------------
        # SOURCE FILE VALIDATION
        # ------------------------------------------------------------------

        print("\n" + "=" * 70)
        print("SOURCE / GENERATED FILE VALIDATION")
        print("=" * 70)

        generated_files = (
            self._find_generated_source_files()
        )

        report.total_source_files = len(
            generated_files
        )

        for generated_file in generated_files:

            relative_path = (
                generated_file.relative_to(
                    self.generated_repository
                )
            )

            print(
                f"[CHECK] {relative_path}"
            )

            generated_hash = (
                self._file_hash(
                    generated_file
                )
            )

            # The original source is identified through the generated
            # repository-relative path.
            #
            # NOTE:
            # The original repository path is not available directly
            # here, so semantic comparison is performed only when the
            # original source can be located from the code analysis cache.
            original_entry = code_cache.get(
                str(
                    relative_path
                ).replace(
                    "\\",
                    "/",
                )
            )

            source_hash = None

            changed = True

            if original_entry:

                source_hash = (
                    original_entry.get(
                        "source_hash"
                    )
                )

            semantic_result = None

            # ----------------------------------------------------------
            # Build basic file result
            # ----------------------------------------------------------

            file_result = FileValidationResult(
                source_file=str(
                    relative_path
                ),
                generated_file=str(
                    relative_path
                ),
                status="CHECKED",
                source_hash=source_hash,
                generated_hash=generated_hash,
                changed=changed,
            )

            report.changed_files += 1

            report.file_results.append(
                file_result
            )

        # ------------------------------------------------------------------
        # Semantic validation
        #
        # We intentionally do not send every generated file to the LLM.
        #
        # Semantic validation should focus on:
        #   - changed files
        #   - WCF files
        #   - files with build errors
        #
        # A later version can make this configurable.
        # ------------------------------------------------------------------

        print("\n" + "=" * 70)
        print("SEMANTIC VALIDATION")
        print("=" * 70)

        semantic_failures = 0

        # For the first implementation, semantic validation is only
        # performed when build succeeded. This avoids spending LLM
        # tokens analyzing code that is syntactically invalid.

        if report.build_status == "PASSED":

            # Limit the number of semantic LLM calls in the first version.
            #
            # This protects against accidentally sending hundreds of
            # files to OpenAI.
            semantic_limit = int(
                os.getenv(
                    "SEMANTIC_VALIDATION_LIMIT",
                    "20",
                )
            )

            semantic_count = 0

            for file_result in report.file_results:

                if semantic_count >= semantic_limit:
                    report.warnings.append(
                        "Semantic validation limit reached. "
                        "Not all generated files were reviewed "
                        "by the LLM."
                    )
                    break

                generated_file = (
                    self.generated_repository /
                    file_result.generated_file
                )

                if not generated_file.exists():
                    continue

                # Get code analysis.
                code_analysis_entry = (
                    code_cache.get(
                        file_result.source_file
                    )
                )

                if not code_analysis_entry:
                    continue

                code_analysis = (
                    code_analysis_entry.get(
                        "result",
                        {},
                    )
                )

                # Semantic validation needs original source.
                #
                # The cache intentionally contains analysis rather than
                # raw source. Therefore the original source is not
                # available here.
                #
                # We mark it for a future source-repository comparison
                # instead of inventing source code.
                file_result.warnings.append(
                    "Original source was not available "
                    "through code_analysis_cache.json; "
                    "semantic comparison skipped."
                )

                semantic_count += 1

            if semantic_failures == 0:
                report.semantic_validation_status = (
                    "PARTIAL"
                )

        else:

            report.semantic_validation_status = (
                "SKIPPED_BUILD_FAILED"
            )

        # ------------------------------------------------------------------
        # Final status
        # ------------------------------------------------------------------

        if (
            report.build_status == "PASSED"
            and report.test_status in [
                "PASSED",
                "NOT_FOUND",
            ]
            and report.semantic_validation_status
            in [
                "PASSED",
                "PARTIAL",
                "NOT_RUN",
            ]
        ):

            report.validation_status = (
                "PASSED_WITH_WARNINGS"
                if report.warnings
                or report.global_issues
                else "PASSED"
            )

        else:

            report.validation_status = "FAILED"

        # ------------------------------------------------------------------
        # Recommendations
        # ------------------------------------------------------------------

        self._generate_recommendations(
            report
        )

        # ------------------------------------------------------------------
        # Save final report
        # ------------------------------------------------------------------

        self._save_report(
            report
        )

        return report

    # ======================================================================
    # Recommendations
    # ======================================================================

    def _generate_recommendations(
        self,
        report: ValidationReport,
    ):
        """
        Generate deterministic recommendations based on validation results.
        """

        if report.build_errors > 0:

            report.recommendations.append(
                "Fix compiler errors before performing "
                "semantic validation or production deployment."
            )

        if report.tests_failed > 0:

            report.recommendations.append(
                "Investigate failing automated tests and "
                "compare behavior with the legacy implementation."
            )

        if report.test_status == "NOT_FOUND":

            report.recommendations.append(
                "No test projects were detected. "
                "Add automated regression tests for critical "
                "business behavior."
            )

        if report.semantic_validation_status == "PARTIAL":

            report.recommendations.append(
                "Run semantic validation against the original "
                "source repository for changed critical files."
            )

        if report.global_issues:

            report.human_review_items.append(
                "Review all validation failures before accepting "
                "the generated repository."
            )

    # ======================================================================
    # Save report
    # ======================================================================

    def _save_report(
        self,
        report: ValidationReport,
    ):
        """
        Save validation report.
        """

        report_path = (
            self.output_root /
            "validation_report.json"
        )

        self._save_json(
            report_path,
            report.model_dump(),
        )

        print(
            f"\nValidation report saved to:"
            f"\n{report_path}"
        )