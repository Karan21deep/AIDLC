import os
from pathlib import Path

from dotenv import load_dotenv

from agents.validation_agent import (
    ValidationAgent,
)


load_dotenv()


# ---------------------------------------------------------------------------
# Input reports
# ---------------------------------------------------------------------------

MODERNIZATION_PLAN = (
    "output/modernization_plan.json"
)

CODE_ANALYSIS_CACHE = (
    "output/code_analysis_cache.json"
)

# ---------------------------------------------------------------------------
# Generated repository
# ---------------------------------------------------------------------------

GENERATED_REPOSITORY = (
    "output/generated_code"
)


def validate_file(path: str):
    """
    Validate that an input file exists.
    """

    if not Path(path).exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )


def main():

    print("=" * 70)
    print("VALIDATION AGENT")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Validate inputs
    # ------------------------------------------------------------------

    validate_file(
        MODERNIZATION_PLAN
    )

    validate_file(
        CODE_ANALYSIS_CACHE
    )

    generated_repository = Path(
        GENERATED_REPOSITORY
    )

    if not generated_repository.exists():

        raise FileNotFoundError(
            "Generated repository does not exist: "
            f"{generated_repository}"
        )

    # ------------------------------------------------------------------
    # Create validation agent
    # ------------------------------------------------------------------

    agent = ValidationAgent(
        generated_repository=GENERATED_REPOSITORY,
        output_root="output",
    )

    # ------------------------------------------------------------------
    # Execute validation
    # ------------------------------------------------------------------

    report = agent.validate(
        modernization_plan_path=(
            MODERNIZATION_PLAN
        ),
        code_analysis_cache_path=(
            CODE_ANALYSIS_CACHE
        ),
    )

    # ------------------------------------------------------------------
    # Display summary
    # ------------------------------------------------------------------

    print("\n" + "=" * 70)
    print("VALIDATION COMPLETED")
    print("=" * 70)

    print(
        f"\nValidation status : "
        f"{report.validation_status}"
    )

    print(
        f"Build status      : "
        f"{report.build_status}"
    )

    print(
        f"Test status       : "
        f"{report.test_status}"
    )

    print(
        f"Semantic status   : "
        f"{report.semantic_validation_status}"
    )

    print(
        f"Projects          : "
        f"{report.total_projects}"
    )

    print(
        f"Source files      : "
        f"{report.total_source_files}"
    )

    print(
        f"Build errors      : "
        f"{report.build_errors}"
    )

    print(
        f"Tests total       : "
        f"{report.tests_total}"
    )

    print(
        f"Tests passed      : "
        f"{report.tests_passed}"
    )

    print(
        f"Tests failed      : "
        f"{report.tests_failed}"
    )

    print(
        f"\nReport:"
        f"\noutput/validation_report.json"
    )


if __name__ == "__main__":
    main()