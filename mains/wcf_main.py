import json

from pathlib import Path

from agents.wcf_analysis_agent import (
    WCFAnalysisAgent
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

# Code Understanding cache.
#
# This contains the analysis of every C# file.
CODE_CACHE_PATH = (
    "output/code_analysis_cache.json"
)

# Dependency Mapping output.
DEPENDENCY_MAPPING_PATH = (
    "output/dependency_mapping.json"
)


# =========================================================
# Output File
# =========================================================

WCF_OUTPUT_PATH = (
    "output/wcf_analysis.json"
)


# =========================================================
# Validate Input Files
# =========================================================

def validate_input_files():

    """
    Make sure all previously generated artifacts exist.

    The WCF Analysis Agent depends on the output of the
    previous agents.
    """

    required_files = [

        DISCOVERY_REPORT_PATH,

        ARCHITECTURE_REPORT_PATH,

        CODE_CACHE_PATH,

        DEPENDENCY_MAPPING_PATH
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
        "             WCF ANALYSIS AGENT"
    )

    print("=" * 70)

    # -----------------------------------------------------
    # Validate previous agent outputs.
    # -----------------------------------------------------

    print(
        "\nValidating previous agent outputs..."
    )

    validate_input_files()

    print(
        "All required files found."
    )

    # -----------------------------------------------------
    # Load Code Analysis Cache just to display statistics.
    # -----------------------------------------------------

    with open(
        CODE_CACHE_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        code_cache = json.load(
            file
        )

    successful_files = sum(

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

    failed_files = sum(

        1

        for entry in code_cache.values()

        if isinstance(
            entry,
            dict
        )
        and entry.get(
            "status"
        ) != "success"
    )

    print(
        "\nCode Understanding cache:"
    )

    print(
        f"Total files : "
        f"{len(code_cache)}"
    )

    print(
        f"Successful  : "
        f"{successful_files}"
    )

    print(
        f"Failed      : "
        f"{failed_files}"
    )

    # -----------------------------------------------------
    # Initialize WCF Agent.
    # -----------------------------------------------------

    print(
        "\nInitializing WCF Analysis Agent..."
    )

    agent = WCFAnalysisAgent()

    # -----------------------------------------------------
    # Analyze WCF repository.
    # -----------------------------------------------------

    print(
        "\nAnalyzing WCF architecture..."
    )

    report = agent.analyze_repository(

        discovery_report_path=
            DISCOVERY_REPORT_PATH,

        architecture_report_path=
            ARCHITECTURE_REPORT_PATH,

        code_cache_path=
            CODE_CACHE_PATH,

        dependency_mapping_path=
            DEPENDENCY_MAPPING_PATH
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
    # Save WCF analysis.
    # -----------------------------------------------------

    output_path = Path(
        WCF_OUTPUT_PATH
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
    # Print summary.
    # -----------------------------------------------------

    print("\n")

    print(
        "=" * 70
    )

    print(
        "             WCF ANALYSIS COMPLETED"
    )

    print(
        "=" * 70
    )

    print(
        f"\nWCF detected       : "
        f"{report.wcf_detected}"
    )

    print(
        f"WCF files         : "
        f"{len(report.wcf_files)}"
    )

    print(
        f"Contracts         : "
        f"{len(report.contracts)}"
    )

    print(
        f"Services          : "
        f"{len(report.services)}"
    )

    print(
        f"Endpoints         : "
        f"{len(report.endpoints)}"
    )

    print(
        f"Bindings          : "
        f"{len(report.bindings)}"
    )

    print(
        f"Recommendations   : "
        f"{len(report.migration_recommendations)}"
    )

    print(
        f"Risks             : "
        f"{len(report.risks)}"
    )

    print(
        f"Unresolved items  : "
        f"{len(report.unresolved_items)}"
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