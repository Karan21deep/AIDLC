import argparse
import hashlib
import json
import os
import traceback
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

from agents.repository_discovery_agent import RepositoryDiscoveryAgent
from agents.architecture_analysis_agent import ArchitectureAnalysisAgent
from agents.code_understanding_agent import CodeUnderstandingAgent
from agents.dependency_mapping_agent import DependencyMappingAgent
from agents.wcf_analysis_agent import WCFAnalysisAgent
from agents.modernization_agent import ModernizationAgent
from agents.code_generation_agent import CodeGenerationAgent
from agents.validation_agent import ValidationAgent


# ============================================================================
# Environment
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"

DISCOVERY_REPORT = OUTPUT_DIR / "discovery_report.json"
ARCHITECTURE_REPORT = OUTPUT_DIR / "architecture_report.json"
CODE_CACHE = OUTPUT_DIR / "code_analysis_cache.json"
DEPENDENCY_MAPPING = OUTPUT_DIR / "dependency_mapping.json"
WCF_ANALYSIS = OUTPUT_DIR / "wcf_analysis.json"
MODERNIZATION_PLAN = OUTPUT_DIR / "modernization_plan.json"
GENERATION_REPORT = OUTPUT_DIR / "code_generation_report.json"
VALIDATION_REPORT = OUTPUT_DIR / "validation_report.json"
GENERATED_ROOT = OUTPUT_DIR / "generated_code"
GENERATION_CACHE = OUTPUT_DIR / "code_generation_cache.json"

CODE_ANALYSIS_PROMPT_VERSION = "v1"
PIPELINE_VERSION = "all-agents-v1"


# ============================================================================
# Utilities
# ============================================================================

def log(message: str) -> None:
    print(message, flush=True)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if hasattr(data, "model_dump"):
        data = data.model_dump()

    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
            default=str,
        )


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return {} if default is None else default

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def file_hash(path: Path) -> str:
    sha256 = hashlib.sha256()

    with open(path, "rb") as file:
        while True:
            chunk = file.read(1024 * 1024)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def is_excluded_path(path: Path) -> bool:
    excluded = {
        ".git",
        ".vs",
        ".idea",
        "bin",
        "obj",
        "node_modules",
        ".venv",
        "venv",
        "packages",
        "output",
    }

    return any(part.lower() in excluded for part in path.parts)


def find_csharp_files(repository: Path):
    return sorted(
        path
        for path in repository.rglob("*.cs")
        if path.is_file()
        and not is_excluded_path(path)
    )


def validate_file(path: Path, description: str) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"{description} not found: {path}"
        )


# ============================================================================
# Stage 1 - Repository Discovery
# ============================================================================

def run_discovery(repository: Path):
    log("")
    log("=" * 70)
    log("STEP 1/8 - REPOSITORY DISCOVERY")
    log("=" * 70)

    agent = RepositoryDiscoveryAgent()

    log(f"Scanning repository: {repository}")

    report = agent.run(str(repository))

    save_json(
        DISCOVERY_REPORT,
        report,
    )

    validate_file(
        DISCOVERY_REPORT,
        "Discovery report",
    )

    log("[OK] Repository Discovery completed")
    log(f"Report: {DISCOVERY_REPORT}")

    return report


# ============================================================================
# Stage 2 - Architecture Analysis
# ============================================================================

def run_architecture(repository: Path):
    log("")
    log("=" * 70)
    log("STEP 2/8 - ARCHITECTURE ANALYSIS")
    log("=" * 70)

    agent = ArchitectureAnalysisAgent()

    log("Analyzing repository architecture...")

    report = agent.run(
        repo_path=str(repository),
        discovery_report_path=str(DISCOVERY_REPORT),
    )

    save_json(
        ARCHITECTURE_REPORT,
        report,
    )

    validate_file(
        ARCHITECTURE_REPORT,
        "Architecture report",
    )

    log("[OK] Architecture Analysis completed")
    log(f"Report: {ARCHITECTURE_REPORT}")

    return report


# ============================================================================
# Stage 3 - Code Understanding
# ============================================================================

def load_code_cache() -> Dict[str, Any]:
    cache = load_json(
        CODE_CACHE,
        default={},
    )

    if not isinstance(cache, dict):
        return {}

    return cache


def save_code_cache(cache: Dict[str, Any]) -> None:
    save_json(
        CODE_CACHE,
        cache,
    )


def cache_is_valid(
    entry: Dict[str, Any],
    source_hash: str,
) -> bool:
    if not isinstance(entry, dict):
        return False

    if entry.get("status") != "success":
        return False

    if entry.get("source_hash") != source_hash:
        return False

    if entry.get("pipeline_version") != PIPELINE_VERSION:
        return False

    if entry.get("prompt_version") != CODE_ANALYSIS_PROMPT_VERSION:
        return False

    result = entry.get("result")

    return isinstance(result, dict)


def run_code_understanding(
    repository: Path,
    discovery_report: Dict[str, Any],
    architecture_report: Dict[str, Any],
):
    log("")
    log("=" * 70)
    log("STEP 3/8 - CODE UNDERSTANDING")
    log("=" * 70)

    agent = CodeUnderstandingAgent()

    cache = load_code_cache()

    source_files = find_csharp_files(repository)

    log(f"C# source files found: {len(source_files)}")

    successful = 0
    failed = 0
    cached = 0

    for index, source_file in enumerate(source_files, start=1):
        relative_file = source_file.relative_to(repository)

        log(
            f"[{index}/{len(source_files)}] "
            f"Analyzing: {relative_file}"
        )

        try:
            source_hash = file_hash(source_file)

            cache_key = str(source_file.resolve())

            existing = cache.get(cache_key)

            if cache_is_valid(
                existing,
                source_hash,
            ):
                cached += 1
                successful += 1

                log("  [CACHE] Existing successful analysis reused.")
                continue

            result = agent.analyze_file(
                file_path=str(source_file),
                discovery_report=discovery_report,
                architecture_report=architecture_report,
            )

            if hasattr(result, "model_dump"):
                result_dict = result.model_dump()
            elif isinstance(result, dict):
                result_dict = result
            else:
                raise TypeError(
                    "Code Understanding Agent returned "
                    f"unsupported result type: {type(result)}"
                )

            cache[cache_key] = {
                "status": "success",
                "source_hash": source_hash,
                "pipeline_version": PIPELINE_VERSION,
                "prompt_version": CODE_ANALYSIS_PROMPT_VERSION,
                "result": result_dict,
            }

            save_code_cache(cache)

            successful += 1

            log("  [OK] Analysis completed and cached.")

        except Exception as exc:
            failed += 1

            # Do not overwrite a previous successful cache entry
            # with a failed result.
            log(
                f"  [FAILED] {relative_file}: {exc}"
            )

            log(
                traceback.format_exc()
            )

    log("")
    log("Code Understanding summary:")
    log(f"  Source files : {len(source_files)}")
    log(f"  Successful   : {successful}")
    log(f"  Cached       : {cached}")
    log(f"  Failed       : {failed}")

    validate_file(
        CODE_CACHE,
        "Code Understanding cache",
    )

    if successful == 0:
        raise RuntimeError(
            "Code Understanding produced no successful file analyses."
        )

    log("[OK] Code Understanding completed")
    log(f"Cache: {CODE_CACHE}")

    return load_code_cache()


# ============================================================================
# Stage 4 - Dependency Mapping
# ============================================================================

def run_dependency_mapping(repository: Path):
    log("")
    log("=" * 70)
    log("STEP 4/8 - DEPENDENCY MAPPING")
    log("=" * 70)

    agent = DependencyMappingAgent(
        repository_name=repository.name
    )

    log("Building deterministic dependency graph...")

    report = agent.build_dependency_map(
        str(CODE_CACHE)
    )

    save_json(
        DEPENDENCY_MAPPING,
        report,
    )

    validate_file(
        DEPENDENCY_MAPPING,
        "Dependency mapping report",
    )

    log("[OK] Dependency Mapping completed")
    log(f"Files   : {report.total_files}")
    log(f"Classes : {report.total_classes}")
    log(f"Methods : {report.total_methods}")
    log(f"Nodes   : {report.total_nodes}")
    log(f"Edges   : {report.total_edges}")

    return report


# ============================================================================
# Stage 5 - WCF Analysis
# ============================================================================

def run_wcf_analysis():
    log("")
    log("=" * 70)
    log("STEP 5/8 - WCF ANALYSIS")
    log("=" * 70)

    agent = WCFAnalysisAgent()

    log("Analyzing WCF services, contracts, endpoints and bindings...")

    report = agent.analyze_repository(
        discovery_report_path=str(DISCOVERY_REPORT),
        architecture_report_path=str(ARCHITECTURE_REPORT),
        code_cache_path=str(CODE_CACHE),
        dependency_mapping_path=str(DEPENDENCY_MAPPING),
    )

    save_json(
        WCF_ANALYSIS,
        report,
    )

    validate_file(
        WCF_ANALYSIS,
        "WCF analysis report",
    )

    log("[OK] WCF Analysis completed")
    log(f"WCF files : {len(report.wcf_files)}")
    log(f"Contracts : {len(report.contracts)}")
    log(f"Services  : {len(report.services)}")
    log(f"Endpoints : {len(report.endpoints)}")
    log(f"Bindings  : {len(report.bindings)}")

    return report


# ============================================================================
# Stage 6 - Modernization Planning
# ============================================================================

def run_modernization_plan():
    log("")
    log("=" * 70)
    log("STEP 6/8 - MODERNIZATION PLAN")
    log("=" * 70)

    agent = ModernizationAgent()

    log("Creating modernization strategy...")

    plan = agent.build_plan(
        discovery_report_path=str(DISCOVERY_REPORT),
        architecture_report_path=str(ARCHITECTURE_REPORT),
        code_cache_path=str(CODE_CACHE),
        dependency_mapping_path=str(DEPENDENCY_MAPPING),
        wcf_analysis_path=str(WCF_ANALYSIS),
    )

    save_json(
        MODERNIZATION_PLAN,
        plan,
    )

    validate_file(
        MODERNIZATION_PLAN,
        "Modernization plan",
    )

    log("[OK] Modernization Planning completed")
    log(f"Strategy: {plan.migration_strategy}")
    log(f"Projects: {len(plan.projects)}")
    log(f"Component mappings: {len(plan.component_mappings)}")
    log(f"WCF mappings: {len(plan.wcf_modernization)}")
    log(
        "Dependency mappings: "
        f"{len(plan.dependency_modernization)}"
    )
    log(
        "Migration phases: "
        f"{len(plan.migration_phases)}"
    )

    return plan


# ============================================================================
# Stage 7 - Code Generation
# ============================================================================

def run_code_generation(repository: Path):
    log("")
    log("=" * 70)
    log("STEP 7/8 - CODE GENERATION")
    log("=" * 70)

    GENERATED_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    agent = CodeGenerationAgent(
        output_root=str(OUTPUT_DIR),
        generated_root=str(GENERATED_ROOT),
        cache_file=str(GENERATION_CACHE),
    )

    log("Generating modernized source code...")

    report = agent.generate(
        repository_path=str(repository),
        modernization_plan_path=str(MODERNIZATION_PLAN),
        architecture_report_path=str(ARCHITECTURE_REPORT),
        code_cache_path=str(CODE_CACHE),
        dependency_mapping_path=str(DEPENDENCY_MAPPING),
        wcf_analysis_path=str(WCF_ANALYSIS),
    )

    # CodeGenerationAgent normally saves this report itself.
    # Save again so the orchestration layer guarantees the artifact.
    save_json(
        GENERATION_REPORT,
        report,
    )

    validate_file(
        GENERATION_REPORT,
        "Code generation report",
    )

    validate_file(
        GENERATED_ROOT,
        "Generated repository",
    )

    log("[OK] Code Generation completed")
    log(f"Source files : {report.total_source_files}")
    log(f"Affected     : {report.affected_files}")
    log(f"Generated    : {report.generated_files}")
    log(f"Copied       : {report.copied_files}")
    log(f"Cached       : {report.cached_files}")
    log(f"Failed       : {report.failed_files}")

    return report


# ============================================================================
# Stage 8 - Validation
# ============================================================================

def run_validation():
    log("")
    log("=" * 70)
    log("STEP 8/8 - VALIDATION")
    log("=" * 70)

    agent = ValidationAgent(
        generated_repository=str(GENERATED_ROOT),
        output_root=str(OUTPUT_DIR),
    )

    log("Running restore, build, tests and semantic validation...")

    report = agent.validate(
        modernization_plan_path=str(MODERNIZATION_PLAN),
        code_analysis_cache_path=str(CODE_CACHE),
    )

    save_json(
        VALIDATION_REPORT,
        report,
    )

    validate_file(
        VALIDATION_REPORT,
        "Validation report",
    )

    log("[OK] Validation completed")
    log(f"Validation : {report.validation_status}")
    log(f"Build      : {report.build_status}")
    log(f"Tests      : {report.test_status}")
    log(
        "Semantic   : "
        f"{report.semantic_validation_status}"
    )
    log(f"Build errors : {report.build_errors}")
    log(f"Tests total  : {report.tests_total}")
    log(f"Tests passed : {report.tests_passed}")
    log(f"Tests failed : {report.tests_failed}")

    return report


# ============================================================================
# Complete Pipeline
# ============================================================================

def execute_pipeline(repository_path: str):
    repository = Path(repository_path).resolve()

    if not repository.exists():
        raise FileNotFoundError(
            f"Repository does not exist: {repository}"
        )

    if not repository.is_dir():
        raise NotADirectoryError(
            f"Repository path is not a directory: {repository}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    log("")
    log("=" * 80)
    log("LEGACY .NET / WCF MODERNIZATION - COMPLETE AGENTIC PIPELINE")
    log("=" * 80)
    log(f"Repository: {repository}")
    log("")
    log("Execution order:")
    log("  1. Repository Discovery")
    log("  2. Architecture Analysis")
    log("  3. Code Understanding")
    log("  4. Dependency Mapping")
    log("  5. WCF Analysis")
    log("  6. Modernization Plan")
    log("  7. Code Generation")
    log("  8. Validation")
    log("=" * 80)

    # ------------------------------------------------------------------------
    # 1. Discovery
    # ------------------------------------------------------------------------

    discovery_report = run_discovery(
        repository
    )

    # ------------------------------------------------------------------------
    # 2. Architecture
    # ------------------------------------------------------------------------

    architecture_report = run_architecture(
        repository
    )

    # ------------------------------------------------------------------------
    # 3. Code Understanding
    # ------------------------------------------------------------------------

    code_cache = run_code_understanding(
        repository=repository,
        discovery_report=(
            discovery_report.model_dump()
            if hasattr(discovery_report, "model_dump")
            else discovery_report
        ),
        architecture_report=(
            architecture_report.model_dump()
            if hasattr(architecture_report, "model_dump")
            else architecture_report
        ),
    )

    # ------------------------------------------------------------------------
    # 4. Dependency Mapping
    # ------------------------------------------------------------------------

    dependency_report = run_dependency_mapping(
        repository
    )

    # ------------------------------------------------------------------------
    # 5. WCF Analysis
    # ------------------------------------------------------------------------

    wcf_report = run_wcf_analysis()

    # ------------------------------------------------------------------------
    # 6. Modernization
    # ------------------------------------------------------------------------

    modernization_report = run_modernization_plan()

    # ------------------------------------------------------------------------
    # 7. Code Generation
    # ------------------------------------------------------------------------

    generation_report = run_code_generation(
        repository
    )

    # ------------------------------------------------------------------------
    # 8. Validation
    # ------------------------------------------------------------------------

    validation_report = run_validation()

    log("")
    log("=" * 80)
    log("COMPLETE MODERNIZATION PIPELINE FINISHED")
    log("=" * 80)

    log("")
    log("Artifacts:")
    log(f"  Discovery       : {DISCOVERY_REPORT}")
    log(f"  Architecture    : {ARCHITECTURE_REPORT}")
    log(f"  Code Analysis   : {CODE_CACHE}")
    log(f"  Dependencies    : {DEPENDENCY_MAPPING}")
    log(f"  WCF Analysis    : {WCF_ANALYSIS}")
    log(f"  Modernization   : {MODERNIZATION_PLAN}")
    log(f"  Code Generation : {GENERATION_REPORT}")
    log(f"  Validation      : {VALIDATION_REPORT}")
    log(f"  Generated Repo  : {GENERATED_ROOT}")

    return {
        "discovery": discovery_report,
        "architecture": architecture_report,
        "code_understanding": code_cache,
        "dependency": dependency_report,
        "wcf": wcf_report,
        "modernization": modernization_report,
        "generation": generation_report,
        "validation": validation_report,
    }


# ============================================================================
# Repository Input
# ============================================================================

def get_repository_path(cli_repository: str | None = None) -> str:
    """
    Resolve the source repository path.

    Priority:
        1. Repository path supplied on the command line.
        2. Interactive user input.
        3. SOURCE_REPOSITORY_PATH from .env/environment.

    The interactive prompt is the normal mode for a developer running
    the modernization pipeline manually.

    Examples:

        python main.py

        python main.py "D:\\projects\\legacy-wcf-project"
    """

    # ------------------------------------------------------------------------
    # 1. Command-line repository path
    # ------------------------------------------------------------------------

    if cli_repository:
        repository_path = cli_repository.strip()

    else:
        repository_path = ""

    # ------------------------------------------------------------------------
    # 2. Interactive input
    # ------------------------------------------------------------------------

    if not repository_path:

        print("")
        print("=" * 80)
        print("LEGACY .NET / WCF MODERNIZATION")
        print("=" * 80)
        print("")
        print(
            "Enter the path of the legacy .NET/WCF repository "
            "you want to modernize."
        )
        print("")
        print(
            r"Example: D:\projects\legacy-wcf-project"
        )
        print("")

        try:
            repository_path = input(
                "Repository path: "
            ).strip()

        except EOFError:
            repository_path = ""

    # ------------------------------------------------------------------------
    # 3. Environment fallback
    # ------------------------------------------------------------------------

    if not repository_path:

        repository_path = os.getenv(
            "SOURCE_REPOSITORY_PATH",
            ""
        ).strip()

    # ------------------------------------------------------------------------
    # Remove quotes copied from Windows Explorer / terminals
    # ------------------------------------------------------------------------

    repository_path = (
        repository_path
        .strip()
        .strip('"')
        .strip("'")
        .strip()
    )

    if not repository_path:

        raise ValueError(
            "Repository path was not provided."
        )

    return repository_path


# ============================================================================
# CLI
# ============================================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Run the complete legacy .NET/WCF modernization "
            "agentic workflow."
        )
    )

    parser.add_argument(
        "repository",
        nargs="?",
        default=None,
        help=(
            "Optional path to the legacy .NET/WCF repository. "
            "If omitted, the application asks the user for the path."
        ),
    )

    args = parser.parse_args()

    try:

        # --------------------------------------------------------------------
        # Get repository path dynamically
        # --------------------------------------------------------------------

        repository_path = get_repository_path(
            cli_repository=args.repository
        )

        log("")
        log(
            f"Selected repository: {repository_path}"
        )

        # --------------------------------------------------------------------
        # Execute the complete 8-agent pipeline
        # --------------------------------------------------------------------

        execute_pipeline(
            repository_path
        )

    except KeyboardInterrupt:

        log("")
        log(
            "[STOPPED] Pipeline interrupted by user."
        )

        raise SystemExit(130)

    except Exception as exc:

        log("")
        log("=" * 80)
        log("PIPELINE FAILED")
        log("=" * 80)

        log(
            str(exc)
        )

        log("")
        log(
            traceback.format_exc()
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()
