from typing import List
from pydantic import BaseModel, Field


class ArchitectureProject(BaseModel):
    name: str
    path: str
    project_type: str
    target_framework: str | None = None

    responsibilities: List[str] = Field(
        default_factory=list
    )

    dependencies: List[str] = Field(
        default_factory=list
    )

    dependent_projects: List[str] = Field(
        default_factory=list
    )


class ArchitectureLayer(BaseModel):
    name: str

    purpose: str

    projects: List[str] = Field(
        default_factory=list
    )

    responsibilities: List[str] = Field(
        default_factory=list
    )

    depends_on_layers: List[str] = Field(
        default_factory=list
    )


class ArchitectureComponent(BaseModel):
    name: str

    type: str

    project: str

    purpose: str

    dependencies: List[str] = Field(
        default_factory=list
    )


class ArchitecturePattern(BaseModel):
    name: str

    evidence: List[str] = Field(
        default_factory=list
    )

    explanation: str


class ArchitectureRisk(BaseModel):
    title: str

    description: str

    affected_components: List[str] = Field(
        default_factory=list
    )

    severity: str


class ArchitectureAnalysisReport(BaseModel):

    repository_name: str

    architecture_style: str

    architecture_summary: str

    projects: List[ArchitectureProject] = Field(
        default_factory=list
    )

    layers: List[ArchitectureLayer] = Field(
        default_factory=list
    )

    components: List[ArchitectureComponent] = Field(
        default_factory=list
    )

    design_patterns: List[ArchitecturePattern] = Field(
        default_factory=list
    )

    entry_points: List[str] = Field(
        default_factory=list
    )

    communication_patterns: List[str] = Field(
        default_factory=list
    )

    data_access_components: List[str] = Field(
        default_factory=list
    )

    external_integrations: List[str] = Field(
        default_factory=list
    )

    architecture_risks: List[ArchitectureRisk] = Field(
        default_factory=list
    )

    modernization_observations: List[str] = Field(
        default_factory=list
    )