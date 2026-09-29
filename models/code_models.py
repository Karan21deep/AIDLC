from typing import List, Optional

from pydantic import BaseModel, Field


# =========================================================
# Dependency Information
# =========================================================

class DependencyInfo(BaseModel):

    name: str

    dependency_type: Optional[str] = None

    description: Optional[str] = None


# =========================================================
# Design Pattern Information
# =========================================================

class DesignPatternInfo(BaseModel):

    pattern: str

    evidence: Optional[str] = None

    description: Optional[str] = None


# =========================================================
# Modernization Observation
# =========================================================

class ModernizationObservation(BaseModel):

    area: str

    observation: str

    recommendation: Optional[str] = None


# =========================================================
# Method Analysis
# =========================================================

class MethodAnalysis(BaseModel):

    name: str

    return_type: Optional[str] = None

    parameters: List[str] = Field(
        default_factory=list
    )

    purpose: str

    business_logic: List[str] = Field(
        default_factory=list
    )

    dependencies: List[DependencyInfo] = Field(
        default_factory=list
    )

    methods_called: List[str] = Field(
        default_factory=list
    )

    database_operations: List[str] = Field(
        default_factory=list
    )

    external_services: List[str] = Field(
        default_factory=list
    )

    exceptions_handled: List[str] = Field(
        default_factory=list
    )

    wcf_operations: List[str] = Field(
        default_factory=list
    )

    complexity_observations: List[str] = Field(
        default_factory=list
    )


# =========================================================
# Class Analysis
# =========================================================

class ClassAnalysis(BaseModel):

    name: str

    class_type: str

    namespace: Optional[str] = None

    base_classes: List[str] = Field(
        default_factory=list
    )

    interfaces: List[str] = Field(
        default_factory=list
    )

    responsibilities: List[str] = Field(
        default_factory=list
    )

    dependencies: List[DependencyInfo] = Field(
        default_factory=list
    )

    methods: List[MethodAnalysis] = Field(
        default_factory=list
    )

    design_patterns: List[DesignPatternInfo] = Field(
        default_factory=list
    )

    wcf_related: bool = False


# =========================================================
# File Analysis
# =========================================================

class FileAnalysis(BaseModel):

    file_path: str

    project: Optional[str] = None

    namespace: Optional[str] = None

    file_purpose: str

    usings: List[str] = Field(
        default_factory=list
    )

    classes: List[ClassAnalysis] = Field(
        default_factory=list
    )

    dependencies: List[DependencyInfo] = Field(
        default_factory=list
    )

    database_related: bool = False

    wcf_related: bool = False

    external_integrations: List[str] = Field(
        default_factory=list
    )

    modernization_observations: List[
        ModernizationObservation
    ] = Field(
        default_factory=list
    )


# =========================================================
# Code Unit Analysis
# =========================================================

class CodeUnitAnalysis(BaseModel):

    unit_type: str

    name: str

    purpose: str

    responsibilities: List[str] = Field(
        default_factory=list
    )

    dependencies: List[DependencyInfo] = Field(
        default_factory=list
    )

    methods_called: List[str] = Field(
        default_factory=list
    )

    business_logic: List[str] = Field(
        default_factory=list
    )

    database_operations: List[str] = Field(
        default_factory=list
    )

    external_services: List[str] = Field(
        default_factory=list
    )

    exceptions_handled: List[str] = Field(
        default_factory=list
    )

    wcf_operations: List[str] = Field(
        default_factory=list
    )

    design_patterns: List[
        DesignPatternInfo
    ] = Field(
        default_factory=list
    )

    modernization_observations: List[
        ModernizationObservation
    ] = Field(
        default_factory=list
    )