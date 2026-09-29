from typing import List, Optional

from pydantic import BaseModel, Field


# =========================================================
# Modernization Mapping
# =========================================================
#
# Represents the migration mapping for one legacy component.
#
# Example:
#
#   WCF ServiceContract
#          ↓
#   ASP.NET Core API Contract
#
#   WCF Service
#          ↓
#   ASP.NET Core Controller / Endpoint
#
#   .NET Framework
#          ↓
#   Modern .NET
# =========================================================

class ModernizationMapping(BaseModel):

    # Name of the legacy component.
    component: str

    # Type of legacy component.
    #
    # Examples:
    #
    #   wcf_contract
    #   wcf_service
    #   repository
    #   application_service
    #   domain_service
    #   configuration
    #   dto
    #   test
    component_type: str

    # Legacy technology/framework being used.
    legacy_technology: str

    # Proposed modern technology.
    target_technology: str

    # Reason for the mapping.
    rationale: str

    # Files affected by the migration.
    affected_files: List[str] = Field(
        default_factory=list
    )

    # Dependencies affected by the migration.
    affected_dependencies: List[str] = Field(
        default_factory=list
    )

    # Important migration considerations.
    considerations: List[str] = Field(
        default_factory=list
    )

    # Risks associated with this migration.
    risks: List[str] = Field(
        default_factory=list
    )

    # Complexity:
    #
    #   Low
    #   Medium
    #   High
    #   Unknown
    complexity: str = "Unknown"


# =========================================================
# Project Modernization
# =========================================================
#
# Represents modernization recommendations for an entire
# project.
# =========================================================

class ProjectModernization(BaseModel):

    # Project name.
    project_name: str

    # Existing target framework.
    current_framework: Optional[str] = None

    # Proposed modern framework.
    target_framework: Optional[str] = None

    # Project-level migration strategy.
    strategy: str

    # Important project changes.
    changes: List[str] = Field(
        default_factory=list
    )

    # Project dependencies affected.
    dependencies: List[str] = Field(
        default_factory=list
    )

    # Migration risks.
    risks: List[str] = Field(
        default_factory=list
    )


# =========================================================
# WCF Modernization
# =========================================================
#
# Specialized mapping for WCF.
#
# WCF migration is one of the most important parts of
# this modernization project.
# =========================================================

class WCFModernization(BaseModel):

    # Legacy WCF component.
    component: str

    # WCF component type.
    #
    # Examples:
    #
    #   contract
    #   service
    #   endpoint
    #   binding
    #   behavior
    #   configuration
    component_type: str

    # Existing WCF technology.
    legacy_technology: str

    # Proposed modern technology.
    target_technology: str

    # Migration reasoning.
    rationale: str

    # Operations affected.
    operations: List[str] = Field(
        default_factory=list
    )

    # Security considerations.
    security_considerations: List[str] = Field(
        default_factory=list
    )

    # Configuration considerations.
    configuration_considerations: List[str] = Field(
        default_factory=list
    )

    # Compatibility considerations.
    compatibility_considerations: List[str] = Field(
        default_factory=list
    )

    # Migration risks.
    risks: List[str] = Field(
        default_factory=list
    )

    # Complexity.
    complexity: str = "Unknown"


# =========================================================
# Dependency Modernization
# =========================================================
#
# Describes how a dependency should be handled during
# modernization.
# =========================================================

class DependencyModernization(BaseModel):

    # Legacy dependency.
    dependency: str

    # Type of dependency.
    dependency_type: str

    # Existing usage.
    current_usage: str

    # Modern replacement, if applicable.
    target_dependency: Optional[str] = None

    # Migration action.
    #
    # Examples:
    #
    #   replace
    #   retain
    #   remove
    #   refactor
    #   review
    action: str

    # Reason for the action.
    rationale: str

    # Risks.
    risks: List[str] = Field(
        default_factory=list
    )


# =========================================================
# Migration Phase
# =========================================================
#
# Defines an implementation phase.
#
# Example:
#
#   Phase 1:
#       Project setup
#
#   Phase 2:
#       Domain/Application layer
#
#   Phase 3:
#       WCF migration
#
#   Phase 4:
#       Tests
#
#   Phase 5:
#       Validation
# =========================================================

class MigrationPhase(BaseModel):

    # Phase number.
    phase: int

    # Phase name.
    name: str

    # Objective of the phase.
    objective: str

    # Components involved.
    components: List[str] = Field(
        default_factory=list
    )

    # Dependencies that must be completed first.
    prerequisites: List[str] = Field(
        default_factory=list
    )

    # Expected outputs.
    deliverables: List[str] = Field(
        default_factory=list
    )

    # Important risks.
    risks: List[str] = Field(
        default_factory=list
    )


# =========================================================
# Validation Strategy
# =========================================================
#
# Defines how the modernization should be validated.
# =========================================================

class ValidationStrategy(BaseModel):

    # Type of validation.
    #
    # Examples:
    #
    #   unit_test
    #   integration_test
    #   contract_test
    #   regression_test
    #   api_test
    validation_type: str

    # What should be validated.
    scope: str

    # Important validation steps.
    steps: List[str] = Field(
        default_factory=list
    )

    # Legacy behavior that must remain unchanged.
    expected_behavior: List[str] = Field(
        default_factory=list
    )


# =========================================================
# Modernization Plan
# =========================================================
#
# Final output of the Modernization Agent.
# =========================================================

class ModernizationPlan(BaseModel):

    # Repository name.
    repository_name: Optional[str] = None

    # Current architecture.
    current_architecture: Optional[str] = None

    # Target architecture.
    target_architecture: Optional[str] = None

    # Current framework.
    current_framework: Optional[str] = None

    # Target framework.
    target_framework: Optional[str] = None

    # Overall migration strategy.
    migration_strategy: str

    # Project-level recommendations.
    projects: List[
        ProjectModernization
    ] = Field(
        default_factory=list
    )

    # General component mappings.
    component_mappings: List[
        ModernizationMapping
    ] = Field(
        default_factory=list
    )

    # WCF-specific modernization mappings.
    wcf_modernization: List[
        WCFModernization
    ] = Field(
        default_factory=list
    )

    # Dependency modernization.
    dependency_modernization: List[
        DependencyModernization
    ] = Field(
        default_factory=list
    )

    # Ordered migration phases.
    migration_phases: List[
        MigrationPhase
    ] = Field(
        default_factory=list
    )

    # Validation strategy.
    validation_strategy: List[
        ValidationStrategy
    ] = Field(
        default_factory=list
    )

    # Major migration risks.
    risks: List[str] = Field(
        default_factory=list
    )

    # Assumptions made during planning.
    assumptions: List[str] = Field(
        default_factory=list
    )

    # Items requiring human review.
    human_review_items: List[str] = Field(
        default_factory=list
    )