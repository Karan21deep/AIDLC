from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Individual compiler/build error
# ---------------------------------------------------------------------------

class BuildError(BaseModel):
    """
    Represents a compiler or build error extracted from dotnet build output.
    """

    error_code: Optional[str] = None

    message: str

    file_path: Optional[str] = None

    line: Optional[int] = None

    column: Optional[int] = None

    raw_output: Optional[str] = None


# ---------------------------------------------------------------------------
# Test result
# ---------------------------------------------------------------------------

class TestResult(BaseModel):
    """
    Result of dotnet test.
    """

    command: str

    status: str

    total_tests: Optional[int] = None

    passed: Optional[int] = None

    failed: Optional[int] = None

    skipped: Optional[int] = None

    duration: Optional[str] = None

    output: str = ""


# ---------------------------------------------------------------------------
# Semantic validation result returned by LLM
# ---------------------------------------------------------------------------

class SemanticValidation(BaseModel):
    """
    LLM-based semantic review of generated code.
    """

    status: str

    behavior_preserved: bool

    issues: List[str] = Field(default_factory=list)

    warnings: List[str] = Field(default_factory=list)

    recommendations: List[str] = Field(default_factory=list)

    explanation: str = ""


# ---------------------------------------------------------------------------
# Validation result for one source file
# ---------------------------------------------------------------------------

class FileValidationResult(BaseModel):
    """
    Validation result for one generated source file.
    """

    source_file: str

    generated_file: str

    status: str

    source_hash: Optional[str] = None

    generated_hash: Optional[str] = None

    changed: bool = False

    semantic_validation: Optional[SemanticValidation] = None

    issues: List[str] = Field(default_factory=list)

    warnings: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Complete validation report
# ---------------------------------------------------------------------------

class ValidationReport(BaseModel):
    """
    Complete report produced by the Validation Agent.
    """

    repository_name: Optional[str] = None

    generated_repository: str

    validation_status: str = "UNKNOWN"

    build_status: str = "NOT_RUN"

    test_status: str = "NOT_RUN"

    semantic_validation_status: str = "NOT_RUN"

    total_projects: int = 0

    total_source_files: int = 0

    changed_files: int = 0

    build_errors: int = 0

    tests_total: int = 0

    tests_passed: int = 0

    tests_failed: int = 0

    tests_skipped: int = 0

    build_output: str = ""

    test_output: str = ""

    build_errors_detail: List[BuildError] = Field(
        default_factory=list
    )

    test_result: Optional[TestResult] = None

    file_results: List[FileValidationResult] = Field(
        default_factory=list
    )

    global_issues: List[str] = Field(
        default_factory=list
    )

    warnings: List[str] = Field(
        default_factory=list
    )

    recommendations: List[str] = Field(
        default_factory=list
    )

    human_review_items: List[str] = Field(
        default_factory=list
    )