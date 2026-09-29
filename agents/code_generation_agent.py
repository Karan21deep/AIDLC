import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from openai import OpenAI

from models.code_generation_models import (
    CodeGenerationReport,
    FileGenerationRecord,
    GeneratedFile,
)


# ---------------------------------------------------------------------------
# Version this prompt.
#
# If we change the generation prompt later, changing this version forces
# regeneration even if the source file itself has not changed.
# ---------------------------------------------------------------------------

GENERATION_PROMPT_VERSION = "v1"


class CodeGenerationAgent:
    """
    Code Generation Agent for legacy WCF/.NET modernization.

    Responsibilities:
        1. Read original source code.
        2. Identify files affected by modernization_plan.json.
        3. Build focused context for each file.
        4. Ask OpenAI to generate modernized code.
        5. Cache successful generations.
        6. Copy unaffected files unchanged.
        7. Write generated source into generated_code/.
    """

    def __init__(
        self,
        output_root: str = "output",
        generated_root: str = "output/generated_code",
        cache_file: str = "output/code_generation_cache.json",
    ):
        self.client = OpenAI()

        self.model = os.getenv(
            "OPENAI_MODEL",
            "gpt-5.5",
        )

        self.output_root = Path(output_root)

        # Generated repository is kept separate from the original repository.
        self.generated_root = Path(generated_root)

        # Cache prevents repeated LLM generation.
        self.cache_file = Path(cache_file)

    # ======================================================================
    # Generic JSON helpers
    # ======================================================================

    def _load_json(self, path: str) -> Dict:
        """
        Load a JSON report.
        """

        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"Required file does not exist: {file_path}"
            )

        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _save_json(self, path: Path, data: Dict):
        """
        Save JSON with readable formatting.
        """

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(path, "w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )

    # ======================================================================
    # Hash helpers
    # ======================================================================

    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA-256 hash of a source file.

        The hash is used to determine whether the source file changed.
        """

        sha256 = hashlib.sha256()

        with open(file_path, "rb") as file:
            while True:
                chunk = file.read(1024 * 1024)

                if not chunk:
                    break

                sha256.update(chunk)

        return sha256.hexdigest()

    def _calculate_object_hash(self, value) -> str:
        """
        Calculate a stable hash for JSON-compatible objects.

        This is used for the modernization plan.
        """

        serialized = json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
        )

        return hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest()

    # ======================================================================
    # Cache
    # ======================================================================

    def _load_cache(self) -> Dict:
        """
        Load generation cache.

        Cache structure:

        {
            "relative/path.cs": {
                "source_hash": "...",
                "plan_hash": "...",
                "prompt_version": "v1",
                "status": "success",
                "generated_file": {...}
            }
        }
        """

        if not self.cache_file.exists():
            return {}

        try:
            with open(
                self.cache_file,
                "r",
                encoding="utf-8",
            ) as file:
                return json.load(file)

        except Exception:
            # A corrupted cache should not stop the modernization process.
            return {}

    def _save_cache(self, cache: Dict):
        """
        Save generation cache immediately.

        Saving after every successful file protects against losing all
        generated work if the process crashes halfway through.
        """

        self.cache_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_file = self.cache_file.with_suffix(".tmp")

        with open(
            temp_file,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                cache,
                file,
                indent=2,
                ensure_ascii=False,
            )

        # Atomic replacement.
        temp_file.replace(self.cache_file)

    def _get_cached_generation(
        self,
        cache: Dict,
        relative_path: str,
        source_hash: str,
        plan_hash: str,
    ) -> Optional[GeneratedFile]:
        """
        Return cached generation only if all generation inputs are still
        compatible.
        """

        entry = cache.get(relative_path)

        if not entry:
            return None

        if entry.get("status") != "success":
            return None

        if entry.get("source_hash") != source_hash:
            return None

        if entry.get("plan_hash") != plan_hash:
            return None

        if entry.get("prompt_version") != GENERATION_PROMPT_VERSION:
            return None

        generated_file = entry.get("generated_file")

        if not generated_file:
            return None

        try:
            return GeneratedFile.model_validate(
                generated_file
            )

        except Exception:
            return None

    # ======================================================================
    # Path handling
    # ======================================================================

    def _normalize_relative_path(
        self,
        repository_root: Path,
        file_path: str,
    ) -> str:
        """
        Convert an absolute or relative source path into a repository-relative
        path.

        Example:

            C:/repo/Services/OrderService.cs

        becomes:

            Services/OrderService.cs
        """

        path = Path(file_path)

        if path.is_absolute():
            try:
                return str(
                    path.relative_to(repository_root)
                ).replace("\\", "/")

            except ValueError:
                return path.name

        return str(path).replace("\\", "/")

    def _safe_target_path(
        self,
        relative_path: str,
    ) -> Path:
        """
        Prevent path traversal when writing generated files.

        The LLM is allowed to suggest a target path, but we never allow:

            ../../some-file

        to escape generated_code/.
        """

        clean_path = Path(relative_path)

        # Remove absolute path information.
        if clean_path.is_absolute():
            clean_path = Path(clean_path.name)

        target = (
            self.generated_root /
            clean_path
        ).resolve()

        generated_root = (
            self.generated_root.resolve()
        )

        if generated_root not in target.parents and target != generated_root:
            raise ValueError(
                f"Unsafe generated target path: {relative_path}"
            )

        return target

    # ======================================================================
    # Source discovery
    # ======================================================================

    def _get_source_files(
        self,
        repository_root: Path,
    ) -> List[Path]:
        """
        Find source files that can participate in generation.

        Currently C# and common .NET project/configuration files are included.
        """

        extensions = {
            ".cs",
            ".csproj",
            ".config",
        }

        files = []

        for path in repository_root.rglob("*"):

            if not path.is_file():
                continue

            # Ignore common generated/build directories.
            parts_lower = {
                part.lower()
                for part in path.parts
            }

            if {
                "bin",
                "obj",
                ".git",
                ".vs",
            } & parts_lower:
                continue

            if path.suffix.lower() in extensions:
                files.append(path)

        return sorted(files)

    # ======================================================================
    # Determine affected files
    # ======================================================================

    def _get_affected_files(
        self,
        modernization_plan: Dict,
        wcf_analysis: Dict,
        repository_root: Path,
    ) -> set:
        """
        Extract source files explicitly affected by the modernization plan.

        The primary source is:

            modernization_plan.component_mappings[].affected_files

        WCF analysis is also checked because WCF migration may identify
        service/contract files separately.
        """

        affected = set()

        # --------------------------------------------------------------
        # Component mappings
        # --------------------------------------------------------------

        mappings = modernization_plan.get(
            "component_mappings",
            [],
        )

        for mapping in mappings:

            for file_path in mapping.get(
                "affected_files",
                [],
            ):

                normalized = self._normalize_relative_path(
                    repository_root,
                    file_path,
                )

                affected.add(normalized)

        # --------------------------------------------------------------
        # WCF modernization
        # --------------------------------------------------------------

        wcf_items = modernization_plan.get(
            "wcf_modernization",
            [],
        )

        for item in wcf_items:

            for operation in item.get(
                "operations",
                [],
            ):
                # Operations normally contain names rather than files.
                # They are therefore not directly added here.
                pass

        # --------------------------------------------------------------
        # WCF analysis service files
        # --------------------------------------------------------------

        services = wcf_analysis.get(
            "services",
            [],
        )

        for service in services:

            source_file = service.get(
                "source_file"
            )

            if source_file:
                affected.add(
                    self._normalize_relative_path(
                        repository_root,
                        source_file,
                    )
                )

        contracts = wcf_analysis.get(
            "contracts",
            [],
        )

        for contract in contracts:

            source_file = contract.get(
                "source_file"
            )

            if source_file:
                affected.add(
                    self._normalize_relative_path(
                        repository_root,
                        source_file,
                    )
                )

        return affected

    # ======================================================================
    # Code analysis context
    # ======================================================================

    def _find_code_analysis(
        self,
        code_cache: Dict,
        relative_path: str,
    ) -> Optional[Dict]:
        """
        Find Code Understanding result for a specific source file.
        """

        entry = code_cache.get(relative_path)

        if not entry:
            return None

        if entry.get("status") != "success":
            return None

        return entry.get("result")

    # ======================================================================
    # Dependency context
    # ======================================================================

    def _get_file_dependencies(
        self,
        dependency_mapping: Dict,
        relative_path: str,
    ) -> Dict:
        """
        Extract only dependency information relevant to the current file.

        We deliberately do NOT send the complete dependency graph to OpenAI
        for every file.
        """

        file_dependencies = []
        class_dependencies = []
        method_dependencies = []

        for dependency in dependency_mapping.get(
            "file_dependencies",
            [],
        ):

            source = dependency.get(
                "source_file",
                "",
            )

            target = dependency.get(
                "target_file",
                "",
            )

            if (
                relative_path in source
                or relative_path in target
            ):
                file_dependencies.append(
                    dependency
                )

        for dependency in dependency_mapping.get(
            "class_dependencies",
            [],
        ):

            source = dependency.get(
                "source_file",
                "",
            )

            target = dependency.get(
                "target_file",
                "",
            )

            if (
                relative_path in source
                or relative_path in target
            ):
                class_dependencies.append(
                    dependency
                )

        for dependency in dependency_mapping.get(
            "method_dependencies",
            [],
        ):

            source = dependency.get(
                "source_file",
                "",
            )

            target = dependency.get(
                "target_file",
                "",
            )

            if (
                relative_path in source
                or relative_path in target
            ):
                method_dependencies.append(
                    dependency
                )

        return {
            "file_dependencies": file_dependencies,
            "class_dependencies": class_dependencies,
            "method_dependencies": method_dependencies,
        }

    # ======================================================================
    # WCF context
    # ======================================================================

    def _get_wcf_context(
        self,
        wcf_analysis: Dict,
        relative_path: str,
    ) -> Dict:
        """
        Extract only WCF information related to the current file.
        """

        result = {
            "contracts": [],
            "services": [],
            "endpoints": [],
            "bindings": [],
            "migration_recommendations": [],
        }

        for contract in wcf_analysis.get(
            "contracts",
            [],
        ):

            if relative_path in str(
                contract.get("source_file", "")
            ):
                result["contracts"].append(
                    contract
                )

        for service in wcf_analysis.get(
            "services",
            [],
        ):

            if relative_path in str(
                service.get("source_file", "")
            ):
                result["services"].append(
                    service
                )

        # Endpoints/bindings may not have source file information.
        # We therefore keep only those explicitly linked through service
        # or contract names when possible.

        for endpoint in wcf_analysis.get(
            "endpoints",
            [],
        ):
            result["endpoints"].append(
                endpoint
            )

        for binding in wcf_analysis.get(
            "bindings",
            [],
        ):
            result["bindings"].append(
                binding
            )

        for recommendation in wcf_analysis.get(
            "migration_recommendations",
            [],
        ):
            result["migration_recommendations"].append(
                recommendation
            )

        return result

    # ======================================================================
    # Build generation context
    # ======================================================================

    def _build_file_context(
        self,
        source_file: Path,
        relative_path: str,
        original_code: str,
        modernization_plan: Dict,
        architecture_report: Dict,
        code_analysis: Optional[Dict],
        dependency_context: Dict,
        wcf_context: Dict,
    ) -> Dict:
        """
        Build focused context for one source file.

        The LLM receives:
            - original source
            - modernization instructions
            - architecture
            - code understanding
            - dependencies
            - WCF analysis

        It does NOT receive unrelated repository information.
        """

        return {
            "file": {
                "path": relative_path,
                "extension": source_file.suffix.lower(),
                "original_code": original_code,
            },

            "modernization": {
                "current_framework": modernization_plan.get(
                    "current_framework"
                ),
                "target_framework": modernization_plan.get(
                    "target_framework"
                ),
                "migration_strategy": modernization_plan.get(
                    "migration_strategy"
                ),
                "target_architecture": modernization_plan.get(
                    "target_architecture"
                ),
                "component_mappings": [
                    mapping
                    for mapping in modernization_plan.get(
                        "component_mappings",
                        []
                    )
                    if relative_path in [
                        str(x).replace("\\", "/")
                        for x in mapping.get(
                            "affected_files",
                            []
                        )
                    ]
                ],
                "wcf_modernization": modernization_plan.get(
                    "wcf_modernization",
                    []
                ),
                "dependency_modernization": modernization_plan.get(
                    "dependency_modernization",
                    []
                ),
                "risks": modernization_plan.get(
                    "risks",
                    []
                ),
                "human_review_items": modernization_plan.get(
                    "human_review_items",
                    []
                ),
            },

            "architecture": {
                "style": architecture_report.get(
                    "architecture_style"
                ),
                "summary": architecture_report.get(
                    "architecture_summary"
                ),
                "layers": architecture_report.get(
                    "layers",
                    []
                ),
                "projects": architecture_report.get(
                    "projects",
                    []
                ),
            },

            "code_analysis": code_analysis or {},

            "dependencies": dependency_context,

            "wcf_analysis": wcf_context,
        }

    # ======================================================================
    # LLM prompt
    # ======================================================================

    def _system_prompt(self) -> str:
        """
        System prompt for the Code Generation Agent.
        """

        return """
You are a Senior .NET Modernization Engineer.

Your task is to transform legacy C#/.NET source code according to a
provided modernization plan.

IMPORTANT RULES:

1. Generate actual production-quality source code.

2. Preserve the original business behavior unless the modernization
   plan explicitly requires behavior changes.

3. Do not invent business requirements.

4. Do not remove functionality merely because it looks old.

5. Replace legacy technologies only when the modernization plan indicates
   that they must be replaced.

6. Follow the target architecture described in the modernization plan.

7. Respect existing interfaces, contracts, method behavior and data flow
   unless the modernization plan explicitly changes them.

8. For WCF:
   - Analyze the provided WCF migration recommendation.
   - Replace WCF implementation according to the recommended target.
   - Preserve operation semantics.
   - Preserve request/response models where appropriate.
   - Preserve security requirements.
   - Do not invent endpoints, authentication mechanisms or business rules.

9. For dependency modernization:
   - Follow the target dependency specified by the modernization plan.
   - Do not add unnecessary packages.

10. Do not introduce unrelated refactoring.

11. Do not change public APIs unless required by the modernization plan.

12. Do not generate markdown.

13. Return ONLY source code inside generated_code.

14. The generated code must be syntactically valid.

15. Use appropriate modern C# practices:
   - async/await where appropriate
   - dependency injection
   - interfaces
   - nullable reference types where appropriate
   - modern configuration patterns
   - proper exception handling
   - cancellation tokens where appropriate

16. Do not convert synchronous code to asynchronous code merely for style.
    Do it when the target architecture or underlying operation benefits
    from asynchronous execution.

17. If the provided information is insufficient to safely perform a
    migration, preserve the existing behavior and explain the uncertainty
    in warnings.

18. Never fabricate missing classes, services, database schemas or APIs.

19. If the source file does not require a meaningful modernization change,
    return the source code with generation_status = "unchanged".

20. Do not include ```csharp or ``` around the generated code.
"""

    def _build_user_prompt(
        self,
        context: Dict,
    ) -> str:
        """
        Build the user prompt for one source file.
        """

        return f"""
Modernize the following source file according to the supplied
modernization context.

Return a GeneratedFile object.

SOURCE FILE:

{json.dumps(context["file"], indent=2, ensure_ascii=False)}

MODERNIZATION CONTEXT:

{json.dumps(context["modernization"], indent=2, ensure_ascii=False)}

ARCHITECTURE:

{json.dumps(context["architecture"], indent=2, ensure_ascii=False)}

CODE UNDERSTANDING:

{json.dumps(context["code_analysis"], indent=2, ensure_ascii=False)}

DEPENDENCY INFORMATION:

{json.dumps(context["dependencies"], indent=2, ensure_ascii=False)}

WCF INFORMATION:

{json.dumps(context["wcf_analysis"], indent=2, ensure_ascii=False)}

Generation requirements:

- source_file must identify the original file.
- target_file must be repository-relative.
- generated_code must contain the complete source file.
- changes must explain meaningful modernization changes.
- preserved_behavior must identify important behavior retained.
- warnings must contain anything requiring human review.
- generation_status must be one of:
    "generated"
    "unchanged"
    "needs_review"
"""

    # ======================================================================
    # Generate one file
    # ======================================================================

    def _generate_file(
        self,
        context: Dict,
    ) -> GeneratedFile:
        """
        Call OpenAI for one source file.
        """

        response = self.client.responses.parse(
            model=self.model,

            input=[
                {
                    "role": "system",
                    "content": self._system_prompt(),
                },
                {
                    "role": "user",
                    "content": self._build_user_prompt(
                        context
                    ),
                },
            ],

            text_format=GeneratedFile,
        )

        result = response.output_parsed

        if not result:
            raise RuntimeError(
                "OpenAI returned no structured generation result."
            )

        return result

    # ======================================================================
    # Write generated source
    # ======================================================================

    def _write_generated_file(
        self,
        generated_file: GeneratedFile,
        default_relative_path: str,
    ) -> Path:
        """
        Write generated source code to generated_code/.

        The LLM can suggest a target path, but the path is validated first.
        """

        target_relative_path = (
            generated_file.target_file
            or default_relative_path
        )

        target_path = self._safe_target_path(
            target_relative_path
        )

        target_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            target_path,
            "w",
            encoding="utf-8",
        ) as file:
            file.write(
                generated_file.generated_code
            )

        return target_path

    # ======================================================================
    # Copy unchanged file
    # ======================================================================

    def _copy_unchanged_file(
        self,
        source_file: Path,
        relative_path: str,
    ) -> Path:
        """
        Copy a source file without modification.

        This allows the generated repository to remain a complete repository,
        rather than containing only LLM-generated files.
        """

        target_path = self._safe_target_path(
            relative_path
        )

        target_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source_file,
            target_path,
        )

        return target_path

    # ======================================================================
    # Main generation pipeline
    # ======================================================================

    def generate(
        self,
        repository_path: str,
        modernization_plan_path: str,
        architecture_report_path: str,
        code_cache_path: str,
        dependency_mapping_path: str,
        wcf_analysis_path: str,
    ) -> CodeGenerationReport:
        """
        Execute complete code generation process.
        """

        repository_root = Path(
            repository_path
        ).resolve()

        if not repository_root.exists():
            raise FileNotFoundError(
                f"Repository does not exist: {repository_root}"
            )

        # --------------------------------------------------------------
        # Load reports
        # --------------------------------------------------------------

        modernization_plan = self._load_json(
            modernization_plan_path
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

        # --------------------------------------------------------------
        # Prepare directories
        # --------------------------------------------------------------

        self.generated_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        # --------------------------------------------------------------
        # Load generation cache
        # --------------------------------------------------------------

        cache = self._load_cache()

        # Hash of modernization plan.
        plan_hash = self._calculate_object_hash(
            modernization_plan
        )

        # --------------------------------------------------------------
        # Determine files
        # --------------------------------------------------------------

        source_files = self._get_source_files(
            repository_root
        )

        affected_files = self._get_affected_files(
            modernization_plan,
            wcf_analysis,
            repository_root,
        )

        report = CodeGenerationReport(
            repository_name=modernization_plan.get(
                "repository_name"
            ),
            total_source_files=len(
                source_files
            ),
            affected_files=len(
                affected_files
            ),
        )

        # --------------------------------------------------------------
        # Process files
        # --------------------------------------------------------------

        for source_file in source_files:

            relative_path = self._normalize_relative_path(
                repository_root,
                str(source_file),
            )

            # ==========================================================
            # Unaffected file
            # ==========================================================

            if relative_path not in affected_files:

                self._copy_unchanged_file(
                    source_file,
                    relative_path,
                )

                report.copied_files += 1

                report.files.append(
                    FileGenerationRecord(
                        source_file=relative_path,
                        target_file=relative_path,
                        source_hash=self._calculate_file_hash(
                            source_file
                        ),
                        plan_hash=plan_hash,
                        status="copied",
                        copied_unchanged=True,
                    )
                )

                continue

            # ==========================================================
            # Affected file
            # ==========================================================

            source_hash = self._calculate_file_hash(
                source_file
            )

            # Read original source.
            with open(
                source_file,
                "r",
                encoding="utf-8",
                errors="replace",
            ) as file:
                original_code = file.read()

            # ----------------------------------------------------------
            # Check cache
            # ----------------------------------------------------------

            cached_generation = (
                self._get_cached_generation(
                    cache,
                    relative_path,
                    source_hash,
                    plan_hash,
                )
            )

            if cached_generation:

                self._write_generated_file(
                    cached_generation,
                    relative_path,
                )

                report.cached_files += 1
                report.generated_files += 1

                report.files.append(
                    FileGenerationRecord(
                        source_file=relative_path,
                        target_file=(
                            cached_generation.target_file
                        ),
                        source_hash=source_hash,
                        plan_hash=plan_hash,
                        status="cached",
                        llm_generated=False,
                        changes=(
                            cached_generation.changes
                        ),
                        warnings=(
                            cached_generation.warnings
                        ),
                    )
                )

                continue

            # ----------------------------------------------------------
            # Build focused context
            # ----------------------------------------------------------

            code_analysis = self._find_code_analysis(
                code_cache,
                relative_path,
            )

            dependency_context = (
                self._get_file_dependencies(
                    dependency_mapping,
                    relative_path,
                )
            )

            wcf_context = self._get_wcf_context(
                wcf_analysis,
                relative_path,
            )

            context = self._build_file_context(
                source_file=source_file,
                relative_path=relative_path,
                original_code=original_code,
                modernization_plan=modernization_plan,
                architecture_report=architecture_report,
                code_analysis=code_analysis,
                dependency_context=dependency_context,
                wcf_context=wcf_context,
            )

            # ----------------------------------------------------------
            # Generate
            # ----------------------------------------------------------

            try:

                generated_file = self._generate_file(
                    context
                )

                # Make sure source file is always associated correctly.
                generated_file.source_file = (
                    relative_path
                )

                if not generated_file.target_file:
                    generated_file.target_file = (
                        relative_path
                    )

                # ------------------------------------------------------
                # Write generated source
                # ------------------------------------------------------

                self._write_generated_file(
                    generated_file,
                    relative_path,
                )

                # ------------------------------------------------------
                # Store successful generation in cache
                # ------------------------------------------------------

                cache[relative_path] = {
                    "source_hash": source_hash,
                    "plan_hash": plan_hash,
                    "prompt_version": (
                        GENERATION_PROMPT_VERSION
                    ),
                    "status": "success",
                    "generated_file": (
                        generated_file.model_dump()
                    ),
                }

                self._save_cache(cache)

                report.generated_files += 1

                report.files.append(
                    FileGenerationRecord(
                        source_file=relative_path,
                        target_file=(
                            generated_file.target_file
                        ),
                        source_hash=source_hash,
                        plan_hash=plan_hash,
                        status=(
                            generated_file.generation_status
                        ),
                        llm_generated=True,
                        changes=(
                            generated_file.changes
                        ),
                        warnings=(
                            generated_file.warnings
                        ),
                    )
                )

            except Exception as exc:

                # ------------------------------------------------------
                # IMPORTANT:
                #
                # Failed generations are NOT added as successful cache
                # entries.
                #
                # Therefore the next run will retry the file.
                # ------------------------------------------------------

                report.failed_files += 1

                report.files.append(
                    FileGenerationRecord(
                        source_file=relative_path,
                        target_file=relative_path,
                        source_hash=source_hash,
                        plan_hash=plan_hash,
                        status="failed",
                        llm_generated=False,
                        warnings=[
                            str(exc)
                        ],
                    )
                )

                print(
                    f"[ERROR] Generation failed: "
                    f"{relative_path}"
                )

                print(
                    f"        {exc}"
                )

        # --------------------------------------------------------------
        # Save generation report
        # --------------------------------------------------------------

        report_path = (
            self.output_root /
            "code_generation_report.json"
        )

        self._save_json(
            report_path,
            report.model_dump(),
        )

        return report