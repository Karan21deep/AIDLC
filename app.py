import io
import json
import os
import traceback
from contextlib import redirect_stdout
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

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


# ============================================================================
# Import the existing pipeline
# ============================================================================

# main.py remains responsible for all agent logic.
# This Streamlit application only provides the UI/orchestration layer.

try:
    import main as modernization_pipeline
except Exception as exc:
    modernization_pipeline = None
    IMPORT_ERROR = exc


# ============================================================================
# Streamlit Page Configuration
# ============================================================================

st.set_page_config(
    page_title=".NET/WCF Modernization",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================================
# Styling
# ============================================================================

st.markdown(
    """
    <style>
        .main-title {
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        .sub-title {
            color: #6b7280;
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }

        .stage-card {
            padding: 12px 16px;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
            margin-bottom: 8px;
        }

        .success-box {
            padding: 12px 16px;
            border-radius: 8px;
            background-color: #ecfdf5;
            border: 1px solid #a7f3d0;
        }

        .log-box {
            background-color: #111827;
            color: #e5e7eb;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 0.85rem;
            white-space: pre-wrap;
            height: 400px;
            overflow-y: auto;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================================
# Pipeline Stages
# ============================================================================

STAGES = [
    "Repository Discovery",
    "Architecture Analysis",
    "Code Understanding",
    "Dependency Mapping",
    "WCF Analysis",
    "Modernization Plan",
    "Code Generation",
    "Validation",
]


# ============================================================================
# Helpers
# ============================================================================

def get_default_repository() -> str:
    """
    Get the default repository path.

    SOURCE_REPOSITORY_PATH is optional.
    The user can always enter a different path in the UI.
    """

    return os.getenv("SOURCE_REPOSITORY_PATH", "")


def get_report(path: Path):
    """Read a JSON report if it exists."""

    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    except Exception:
        return None


def format_log_text(lines):
    return "\n".join(lines[-250:])


def update_progress(
    progress_bar,
    stage_placeholder,
    stage_number,
    stage_name,
):
    progress_bar.progress(
        min(stage_number / len(STAGES), 1.0)
    )

    stage_placeholder.info(
        f"Running Stage {stage_number}/{len(STAGES)}: {stage_name}"
    )


def validate_repository(repository_path: str):
    path = Path(repository_path).expanduser()

    if not path.exists():
        return False, f"Repository does not exist: {path}"

    if not path.is_dir():
        return False, f"Repository path is not a directory: {path}"

    return True, str(path.resolve())


# ============================================================================
# Run Complete Pipeline
# ============================================================================

def run_pipeline_from_streamlit(
    repository_path: str,
    progress_bar,
    stage_placeholder,
    log_placeholder,
):
    """
    Execute the same agents/functions used by main.py.

    We deliberately call the existing functions from main.py rather than
    duplicating the agent implementation here.
    """

    repository = Path(repository_path).resolve()

    logs = []

    def stream_log(message: str):
        message = str(message)
        logs.append(message)

        log_placeholder.code(
            format_log_text(logs),
            language="text",
        )

    # main.py's log() normally prints to terminal.
    # Replace it temporarily so Streamlit can display pipeline progress.
    original_log = modernization_pipeline.log

    modernization_pipeline.log = stream_log

    try:

        # --------------------------------------------------------------------
        # STEP 1 - Repository Discovery
        # --------------------------------------------------------------------

        update_progress(
            progress_bar,
            stage_placeholder,
            1,
            "Repository Discovery",
        )

        discovery_report = modernization_pipeline.run_discovery(
            repository
        )

        # --------------------------------------------------------------------
        # STEP 2 - Architecture Analysis
        # --------------------------------------------------------------------

        update_progress(
            progress_bar,
            stage_placeholder,
            2,
            "Architecture Analysis",
        )

        architecture_report = modernization_pipeline.run_architecture(
            repository
        )

        # Convert Pydantic reports to dictionaries for Code Understanding.
        if hasattr(discovery_report, "model_dump"):
            discovery_dict = discovery_report.model_dump()
        else:
            discovery_dict = discovery_report

        if hasattr(architecture_report, "model_dump"):
            architecture_dict = architecture_report.model_dump()
        else:
            architecture_dict = architecture_report

        # --------------------------------------------------------------------
        # STEP 3 - Code Understanding
        # --------------------------------------------------------------------

        update_progress(
            progress_bar,
            stage_placeholder,
            3,
            "Code Understanding",
        )

        code_cache = modernization_pipeline.run_code_understanding(
            repository=repository,
            discovery_report=discovery_dict,
            architecture_report=architecture_dict,
        )

        # --------------------------------------------------------------------
        # STEP 4 - Dependency Mapping
        # --------------------------------------------------------------------

        update_progress(
            progress_bar,
            stage_placeholder,
            4,
            "Dependency Mapping",
        )

        dependency_report = modernization_pipeline.run_dependency_mapping(
            repository
        )

        # --------------------------------------------------------------------
        # STEP 5 - WCF Analysis
        # --------------------------------------------------------------------

        update_progress(
            progress_bar,
            stage_placeholder,
            5,
            "WCF Analysis",
        )

        wcf_report = modernization_pipeline.run_wcf_analysis()

        # --------------------------------------------------------------------
        # STEP 6 - Modernization Plan
        # --------------------------------------------------------------------

        update_progress(
            progress_bar,
            stage_placeholder,
            6,
            "Modernization Plan",
        )

        modernization_report = (
            modernization_pipeline.run_modernization_plan()
        )

        # --------------------------------------------------------------------
        # STEP 7 - Code Generation
        # --------------------------------------------------------------------

        update_progress(
            progress_bar,
            stage_placeholder,
            7,
            "Code Generation",
        )

        generation_report = modernization_pipeline.run_code_generation(
            repository
        )

        # --------------------------------------------------------------------
        # STEP 8 - Validation
        # --------------------------------------------------------------------

        update_progress(
            progress_bar,
            stage_placeholder,
            8,
            "Validation",
        )

        validation_report = modernization_pipeline.run_validation()

        progress_bar.progress(1.0)

        stage_placeholder.success(
            "All 8 stages completed."
        )

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

    finally:
        # Always restore the original main.py logger.
        modernization_pipeline.log = original_log


# ============================================================================
# Sidebar
# ============================================================================

with st.sidebar:

    st.header("⚙️ Configuration")

    default_repository = get_default_repository()

    repository_path = st.text_input(
        "Legacy Repository Path",
        value=default_repository,
        placeholder=r"D:\projects\legacy-wcf-project",
        help=(
            "Enter the local path containing the legacy "
            ".NET/WCF repository."
        ),
    )

    st.caption(
        "You can change the repository path for every run."
    )

    st.divider()

    st.subheader("Pipeline")

    for index, stage in enumerate(STAGES, start=1):
        st.write(
            f"**{index}.** {stage}"
        )

    st.divider()

    st.caption(
        "The Streamlit UI uses the existing agents and "
        "functions implemented in main.py."
    )


# ============================================================================
# Main Header
# ============================================================================

st.markdown(
    '<div class="main-title">🔄 Legacy .NET / WCF Modernization</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="sub-title">
        AI-assisted modernization pipeline for legacy .NET/WCF repositories
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================================
# Validate main.py Import
# ============================================================================

if modernization_pipeline is None:

    st.error(
        "Could not import main.py."
    )

    st.code(
        traceback.format_exc(),
        language="text",
    )

    st.stop()


# ============================================================================
# Repository Validation
# ============================================================================

col1, col2 = st.columns([4, 1])

with col1:

    if repository_path:

        valid, result = validate_repository(
            repository_path
        )

        if valid:
            st.success(
                f"Repository found: `{result}`"
            )
        else:
            st.error(result)

    else:
        st.warning(
            "Enter the path of the legacy repository."
        )


with col2:

    if repository_path:

        try:
            file_count = len(
                list(
                    Path(repository_path).rglob("*.cs")
                )
            )

            st.metric(
                "C# Files",
                file_count,
            )

        except Exception:
            st.metric(
                "C# Files",
                "N/A",
            )


# ============================================================================
# Run Button
# ============================================================================

st.divider()

run_button = st.button(
    "🚀 Start Complete Modernization",
    type="primary",
    use_container_width=True,
)


# ============================================================================
# Pipeline Execution
# ============================================================================

if run_button:

    valid, result = validate_repository(
        repository_path
    )

    if not valid:

        st.error(result)
        st.stop()

    repository_path = result

    # Clear previous run results.
    st.session_state["pipeline_completed"] = False
    st.session_state["pipeline_results"] = None

    st.subheader("Pipeline Progress")

    progress_bar = st.progress(
        0.0
    )

    stage_placeholder = st.empty()

    st.subheader("Live Pipeline Logs")

    log_placeholder = st.empty()

    try:

        with st.spinner(
            "Running modernization pipeline..."
        ):

            results = run_pipeline_from_streamlit(
                repository_path=repository_path,
                progress_bar=progress_bar,
                stage_placeholder=stage_placeholder,
                log_placeholder=log_placeholder,
            )

        st.session_state["pipeline_completed"] = True
        st.session_state["pipeline_results"] = results

        st.success(
            "🎉 Complete modernization pipeline finished."
        )

    except Exception as exc:

        st.session_state["pipeline_completed"] = False

        st.error(
            "Pipeline failed."
        )

        st.exception(exc)


# ============================================================================
# Results
# ============================================================================

if st.session_state.get(
    "pipeline_completed",
    False,
):

    st.divider()

    st.header("📊 Modernization Results")

    results = st.session_state.get(
        "pipeline_results",
        {},
    )

    # ------------------------------------------------------------------------
    # Summary Metrics
    # ------------------------------------------------------------------------

    generation_report = get_report(
        GENERATION_REPORT
    )

    validation_report = get_report(
        VALIDATION_REPORT
    )

    modernization_report = get_report(
        MODERNIZATION_PLAN
    )

    col1, col2, col3, col4 = st.columns(4)

    if generation_report:

        with col1:
            st.metric(
                "Source Files",
                generation_report.get(
                    "total_source_files",
                    0,
                ),
            )

        with col2:
            st.metric(
                "Affected Files",
                generation_report.get(
                    "affected_files",
                    0,
                ),
            )

        with col3:
            st.metric(
                "Generated Files",
                generation_report.get(
                    "generated_files",
                    0,
                ),
            )

        with col4:
            st.metric(
                "Copied Unchanged",
                generation_report.get(
                    "copied_files",
                    0,
                ),
            )

    # ------------------------------------------------------------------------
    # Validation Summary
    # ------------------------------------------------------------------------

    st.subheader("Validation")

    if validation_report:

        validation_col1, validation_col2, validation_col3, validation_col4 = (
            st.columns(4)
        )

        with validation_col1:
            st.metric(
                "Overall",
                validation_report.get(
                    "validation_status",
                    "UNKNOWN",
                ),
            )

        with validation_col2:
            st.metric(
                "Build",
                validation_report.get(
                    "build_status",
                    "NOT_RUN",
                ),
            )

        with validation_col3:
            st.metric(
                "Tests Passed",
                validation_report.get(
                    "tests_passed",
                    0,
                ),
            )

        with validation_col4:
            st.metric(
                "Tests Failed",
                validation_report.get(
                    "tests_failed",
                    0,
                ),
            )

    # ------------------------------------------------------------------------
    # Modernization Plan
    # ------------------------------------------------------------------------

    st.subheader("Modernization Plan")

    if modernization_report:

        plan_col1, plan_col2 = st.columns(2)

        with plan_col1:

            st.write(
                "**Migration Strategy**"
            )

            st.info(
                modernization_report.get(
                    "migration_strategy",
                    "Not available",
                )
            )

        with plan_col2:

            st.write(
                "**Target Framework**"
            )

            st.info(
                modernization_report.get(
                    "target_framework",
                    "Not specified",
                )
            )

        with st.expander(
            "View Modernization Plan JSON"
        ):

            st.json(
                modernization_report
            )

    # ------------------------------------------------------------------------
    # Generated Repository
    # ------------------------------------------------------------------------

    st.subheader("Generated Repository")

    if GENERATED_ROOT.exists():

        st.success(
            f"Generated repository: `{GENERATED_ROOT}`"
        )

        generated_files = [
            path
            for path in GENERATED_ROOT.rglob("*")
            if path.is_file()
        ]

        st.write(
            f"Generated repository contains "
            f"**{len(generated_files)} files**."
        )

        with st.expander(
            "View Generated Files"
        ):

            for file_path in generated_files[:500]:

                relative_path = file_path.relative_to(
                    GENERATED_ROOT
                )

                st.write(
                    f"`{relative_path}`"
                )

    else:

        st.warning(
            "Generated repository was not found."
        )

    # ------------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------------

    st.subheader("Pipeline Reports")

    report_files = [
        (
            "Discovery Report",
            DISCOVERY_REPORT,
        ),
        (
            "Architecture Report",
            ARCHITECTURE_REPORT,
        ),
        (
            "Code Analysis Cache",
            CODE_CACHE,
        ),
        (
            "Dependency Mapping",
            DEPENDENCY_MAPPING,
        ),
        (
            "WCF Analysis",
            WCF_ANALYSIS,
        ),
        (
            "Modernization Plan",
            MODERNIZATION_PLAN,
        ),
        (
            "Code Generation Report",
            GENERATION_REPORT,
        ),
        (
            "Validation Report",
            VALIDATION_REPORT,
        ),
    ]

    for report_name, report_path in report_files:

        if not report_path.exists():
            continue

        report_data = get_report(
            report_path
        )

        with st.expander(
            report_name
        ):

            if report_data is not None:

                st.json(
                    report_data
                )

                report_bytes = json.dumps(
                    report_data,
                    indent=2,
                    ensure_ascii=False,
                ).encode(
                    "utf-8"
                )

                st.download_button(
                    label=f"⬇️ Download {report_name}",
                    data=report_bytes,
                    file_name=report_path.name,
                    mime="application/json",
                    key=f"download_{report_path.name}",
                )

    # ------------------------------------------------------------------------
    # Validation Issues
    # ------------------------------------------------------------------------

    if validation_report:

        issues = validation_report.get(
            "global_issues",
            [],
        )

        warnings = validation_report.get(
            "warnings",
            [],
        )

        recommendations = validation_report.get(
            "recommendations",
            [],
        )

        if issues:

            st.subheader("Validation Issues")

            for issue in issues:
                st.error(issue)

        if warnings:

            st.subheader("Warnings")

            for warning in warnings:
                st.warning(warning)

        if recommendations:

            st.subheader("Recommendations")

            for recommendation in recommendations:
                st.info(recommendation)


# ============================================================================
# Footer
# ============================================================================

st.divider()

st.caption(
    "Legacy .NET/WCF Modernization Agent • "
    "Streamlit UI + existing Python agent pipeline"
)
