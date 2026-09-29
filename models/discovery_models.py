from typing import List, Optional
from pydantic import BaseModel, Field


class ProjectInfo(BaseModel):
    name: str
    path: str
    project_type: str
    target_framework: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)


class WCFInfo(BaseModel):
    detected: bool = False
    service_files: List[str] = Field(default_factory=list)
    contracts: List[str] = Field(default_factory=list)
    bindings: List[str] = Field(default_factory=list)
    endpoints: List[str] = Field(default_factory=list)
    configuration_files: List[str] = Field(default_factory=list)


class ArchitectureInfo(BaseModel):
    architecture_style: str = ""
    layers: List[str] = Field(default_factory=list)
    patterns: List[str] = Field(default_factory=list)
    important_components: List[str] = Field(default_factory=list)


class RepositoryDiscoveryReport(BaseModel):
    repository_name: str

    summary: str

    solution_files: List[str] = Field(default_factory=list)

    projects: List[ProjectInfo] = Field(default_factory=list)

    total_files: int = 0

    source_file_count: int = 0

    configuration_files: List[str] = Field(default_factory=list)

    test_projects: List[str] = Field(default_factory=list)

    architecture: ArchitectureInfo

    wcf: WCFInfo

    external_dependencies: List[str] = Field(default_factory=list)

    database_indicators: List[str] = Field(default_factory=list)

    risks: List[str] = Field(default_factory=list)

    modernization_observations: List[str] = Field(default_factory=list)