import json

from pathlib import Path

from agents.modernization_agent import (
    ModernizationAgent
)


# =========================================================
# Input Files
# =========================================================

# Repository Discovery output.
DISCOVERY_REPORT_PATH = (
    "output/discovery_report.json"
)

# Architecture Analysis output.
ARCHITECTURE_REPORT_PATH = (
    "output/architecture_report.json"
)

# Code Understanding output.
CODE_CACHE_PATH = (
    "output/code_analysis_cache.json"
)

# Dependency Mapping output.
DEPENDENCY_MAPPING_PATH = (
    "output/dependency_mapping.json"
)

# WCF Analysis output.
WCF_ANALYSIS_PATH = (
    "output/wcf_analysis.json"
)


# =========================================================
# Output
# =========================================================

OUTPUT_PATH = (
    "output/modernization_plan.json"
)


# =========================================================
# Validate Input Files
# =========================================================

def validate_input_files():

    """
    Verify that all previous agent outputs exist.
    """

    required_files = [

        DISCOVERY_REPORT_PATH,

        ARCHITECTURE_REPORT_PATH,

        CODE_CACHE_PATH,

        DEPENDENCY_MAPPING_PATH,

        WCF_ANALYSIS_PATH
    ]

    for file_path in required_files:

        if not Path(
            file_path
        ).exists():

            raise FileNotFoundError(

                f"Required file not found: "
                f"{file_path}"
            )


# =========================================================
# Main
# =========================================================

def main():

    print("=" * 70)

    print(
        "             MODERNIZATION AGENT"
    )

    print("=" * 70)

    # -----------------------------------------------------
    # Validate previous outputs.
    # -----------------------------------------------------

    print(
        "\nValidating previous agent outputs..."
    )

    validate_input_files()

    print(
        "All required input files found."
    )

    # -----------------------------------------------------
    # Display basic statistics.
    # -----------------------------------------------------

    with open(
        CODE_CACHE_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        code_cache = json.load(
            file
        )

    successful_code_files = sum(

        1

        for entry in code_cache.values()

        if isinstance(
            entry,
            dict
        )
        and entry.get(
            "status"
        ) == "success"
    )

    print(
        "\nCode Understanding:"
    )

    print(
        f"Successfully analyzed files: "
        f"{successful_code_files}"
    )

    # -----------------------------------------------------
    # Load dependency mapping.
    # -----------------------------------------------------

    with open(
        DEPENDENCY_MAPPING_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        dependency_mapping = json.load(
            file
        )

    print(
        "\nDependency Mapping:"
    )

    print(
        f"Files: "
        f"{dependency_mapping.get(
            'total_files',
            0
        )}"
    )

    print(
        f"Classes: "
        f"{dependency_mapping.get(
            'total_classes',
            0
        )}"
    )

    print(
        f"Methods: "
        f"{dependency_mapping.get(
            'total_methods',
            0
        )}"
    )

    print(
        f"Edges: "
        f"{dependency_mapping.get(
            'total_edges',
            0
        )}"
    )

    # -----------------------------------------------------
    # Load WCF analysis.
    # -----------------------------------------------------

    with open(
        WCF_ANALYSIS_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        wcf_analysis = json.load(
            file
        )

    print(
        "\nWCF Analysis:"
    )

    print(
        f"WCF detected: "
        f"{wcf_analysis.get(
            'wcf_detected',
            False
        )}"
    )

    print(
        f"WCF files: "
        f"{len(
            wcf_analysis.get(
                'wcf_files',
                []
            )
        )}"
    )

    print(
        f"Contracts: "
        f"{len(
            wcf_analysis.get(
                'contracts',
                []
            )
        )}"
    )

    print(
        f"Services: "
        f"{len(
            wcf_analysis.get(
                'services',
                []
            )
        )}"
    )

    # -----------------------------------------------------
    # Initialize Modernization Agent.
    # -----------------------------------------------------

    print(
        "\nInitializing Modernization Agent..."
    )

    agent = ModernizationAgent()

    # -----------------------------------------------------
    # Build modernization plan.
    # -----------------------------------------------------

    print(
        "\nGenerating modernization plan..."
    )

    report = agent.build_plan(

        discovery_report_path=
            DISCOVERY_REPORT_PATH,

        architecture_report_path=
            ARCHITECTURE_REPORT_PATH,

        code_cache_path=
            CODE_CACHE_PATH,

        dependency_mapping_path=
            DEPENDENCY_MAPPING_PATH,

        wcf_analysis_path=
            WCF_ANALYSIS_PATH
    )

    # -----------------------------------------------------
    # Create output directory.
    # -----------------------------------------------------

    output_directory = Path(
        "output"
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    # -----------------------------------------------------
    # Save modernization plan.
    # -----------------------------------------------------

    output_path = Path(
        OUTPUT_PATH
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(

            report.model_dump(),

            file,

            indent=2,

            ensure_ascii=False
        )

    # -----------------------------------------------------
    # Final summary.
    # -----------------------------------------------------

    print("\n")

    print(
        "=" * 70
    )

    print(
        "             MODERNIZATION PLAN COMPLETED"
    )

    print(
        "=" * 70
    )

    print(
        f"\nCurrent architecture:"
    )

    print(
        report.current_architecture
    )

    print(
        f"\nTarget architecture:"
    )

    print(
        report.target_architecture
    )

    print(
        f"\nCurrent framework:"
    )

    print(
        report.current_framework
    )

    print(
        f"\nTarget framework:"
    )

    print(
        report.target_framework
    )

    print(
        f"\nComponent mappings:"
        f" {len(report.component_mappings)}"
    )

    print(
        f"WCF mappings:"
        f" {len(report.wcf_modernization)}"
    )

    print(
        f"Dependency mappings:"
        f" {len(report.dependency_modernization)}"
    )

    print(
        f"Migration phases:"
        f" {len(report.migration_phases)}"
    )

    print(
        f"Validation strategies:"
        f" {len(report.validation_strategy)}"
    )

    print(
        f"Risks:"
        f" {len(report.risks)}"
    )

    print(
        f"Human review items:"
        f" {len(report.human_review_items)}"
    )

    print(
        "\nOutput:"
    )

    print(
        output_path
    )


# =========================================================
# Entry Point
# =========================================================

if __name__ == "__main__":

    main()