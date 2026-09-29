from typing import List, Optional

from pydantic import BaseModel, Field


# =========================================================
# WCF Operation
# =========================================================
#
# Represents one operation exposed by a WCF service.
#
# Example:
#
#     GetBooking()
#     CreateBooking()
#     CancelBooking()
#
# The operation information is important because later
# the Modernization Agent will need to determine how this
# operation should be exposed in modern .NET.
# =========================================================

class WCFOperation(BaseModel):

    # Name of the WCF operation.
    name: str

    # Return type of the operation.
    return_type: Optional[str] = None

    # Parameters accepted by the operation.
    parameters: List[str] = Field(
        default_factory=list
    )

    # Description of what the operation does.
    purpose: Optional[str] = None

    # Business logic involved in the operation.
    business_logic: List[str] = Field(
        default_factory=list
    )

    # Classes/files used by this operation.
    dependencies: List[str] = Field(
        default_factory=list
    )

    # Whether this operation appears to access a database.
    database_related: bool = False

    # Whether this operation communicates with another
    # external service.
    external_service_related: bool = False


# =========================================================
# WCF Contract Analysis
# =========================================================
#
# Represents a WCF service contract/interface.
#
# Example:
#
#     IBookingService
#
# with:
#
#     GetBooking()
#     CreateBooking()
#     CancelBooking()
# =========================================================

class WCFContractAnalysis(BaseModel):

    # Contract/interface name.
    name: str

    # File containing the contract.
    file_path: Optional[str] = None

    # Namespace.
    namespace: Optional[str] = None

    # WCF operations exposed by the contract.
    operations: List[WCFOperation] = Field(
        default_factory=list
    )

    # Classes implementing this contract.
    implementations: List[str] = Field(
        default_factory=list
    )

    # Whether the contract uses WCF ServiceContract.
    service_contract_detected: bool = False

    # Whether OperationContract attributes were detected.
    operation_contract_detected: bool = False

    # WCF-specific observations.
    observations: List[str] = Field(
        default_factory=list
    )


# =========================================================
# WCF Service Analysis
# =========================================================
#
# Represents a WCF service implementation.
#
# Example:
#
#     BookingService
#          |
#          └── IBookingService
# =========================================================

class WCFServiceAnalysis(BaseModel):

    # Service implementation class.
    name: str

    # Service implementation file.
    file_path: Optional[str] = None

    # Namespace.
    namespace: Optional[str] = None

    # Contracts implemented by the service.
    contracts: List[str] = Field(
        default_factory=list
    )

    # Operations implemented by the service.
    operations: List[WCFOperation] = Field(
        default_factory=list
    )

    # Classes the service depends upon.
    dependencies: List[str] = Field(
        default_factory=list
    )

    # Whether the service is WCF-related.
    wcf_detected: bool = False

    # WCF implementation observations.
    observations: List[str] = Field(
        default_factory=list
    )


# =========================================================
# WCF Endpoint Analysis
# =========================================================
#
# Represents a WCF endpoint.
#
# Example:
#
#     BasicHttpBinding
#     netTcpBinding
#     wsHttpBinding
#
# with an address such as:
#
#     http://server/BookingService
# =========================================================

class WCFEndpointAnalysis(BaseModel):

    # Endpoint name if available.
    name: Optional[str] = None

    # Contract exposed by the endpoint.
    contract: Optional[str] = None

    # Binding used by the endpoint.
    binding: Optional[str] = None

    # Endpoint address.
    address: Optional[str] = None

    # Configuration file where endpoint was found.
    configuration_file: Optional[str] = None

    # Additional endpoint observations.
    observations: List[str] = Field(
        default_factory=list
    )


# =========================================================
# WCF Binding Analysis
# =========================================================
#
# Represents a WCF binding and its configuration.
#
# Example:
#
#     basicHttpBinding
#     wsHttpBinding
#     netTcpBinding
# =========================================================

class WCFBindingAnalysis(BaseModel):

    # Binding name.
    name: str

    # Binding type.
    binding_type: Optional[str] = None

    # Configuration file.
    configuration_file: Optional[str] = None

    # Important binding configuration.
    configuration: List[str] = Field(
        default_factory=list
    )

    # Security configuration.
    security: List[str] = Field(
        default_factory=list
    )

    # Migration considerations.
    migration_considerations: List[str] = Field(
        default_factory=list
    )


# =========================================================
# WCF Migration Recommendation
# =========================================================
#
# This does NOT generate migration code.
#
# It identifies the migration direction that the later
# Modernization Agent can use.
# =========================================================

class WCFMigrationRecommendation(BaseModel):

    # WCF component being considered.
    component: str

    # Current WCF technology.
    current_technology: str

    # Suggested modern .NET technology.
    target_technology: str

    # Reason for the suggested mapping.
    rationale: str

    # Things that need to be checked before migration.
    considerations: List[str] = Field(
        default_factory=list
    )

    # Migration complexity.
    #
    # Example:
    #     Low
    #     Medium
    #     High
    complexity: str = "Unknown"


# =========================================================
# WCF Analysis Report
# =========================================================
#
# Final output of the WCF Analysis Agent.
# =========================================================

class WCFAnalysisReport(BaseModel):

    # Repository name.
    repository_name: Optional[str] = None

    # Whether WCF was detected anywhere in the repository.
    wcf_detected: bool = False

    # Files containing WCF-related code.
    wcf_files: List[str] = Field(
        default_factory=list
    )

    # WCF service contracts.
    contracts: List[WCFContractAnalysis] = Field(
        default_factory=list
    )

    # WCF service implementations.
    services: List[WCFServiceAnalysis] = Field(
        default_factory=list
    )

    # WCF endpoints.
    endpoints: List[WCFEndpointAnalysis] = Field(
        default_factory=list
    )

    # WCF bindings.
    bindings: List[WCFBindingAnalysis] = Field(
        default_factory=list
    )

    # Migration recommendations.
    migration_recommendations: List[
        WCFMigrationRecommendation
    ] = Field(
        default_factory=list
    )

    # General WCF observations.
    observations: List[str] = Field(
        default_factory=list
    )

    # Risks discovered during WCF analysis.
    risks: List[str] = Field(
        default_factory=list
    )

    # Components that need further investigation.
    unresolved_items: List[str] = Field(
        default_factory=list
    )