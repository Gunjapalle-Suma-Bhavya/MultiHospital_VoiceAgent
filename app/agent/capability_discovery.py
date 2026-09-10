"""
Standardized Capability Discovery & External Actions Engine (Section 5.15).

Provides a standardized mechanism for the AI to discover and invoke available capabilities across:
- Internal application services
- Scheduling services
- Communication services
- EHR connectors
- Healthcare-system integration adapters
- Approved external healthcare systems
- Workflow services
- Notification services

Conceptually:
AI Agent -> Capability Registry -> Available Actions -> Authorized Capability -> Execution -> Verification -> Result.

Allows registering external adapters dynamically to support future expansion without modifying core agent code.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agent.capability_registry import CapabilityRegistry, CapabilityExecutionRequest, CapabilityExecutionResult


class CapabilityCategory(str, Enum):
    INTERNAL_SERVICE = "INTERNAL_SERVICE"
    SCHEDULING_SERVICE = "SCHEDULING_SERVICE"
    COMMUNICATION_SERVICE = "COMMUNICATION_SERVICE"
    EHR_CONNECTOR = "EHR_CONNECTOR"
    INTEGRATION_ADAPTER = "INTEGRATION_ADAPTER"
    EXTERNAL_HEALTHCARE_SYSTEM = "EXTERNAL_HEALTHCARE_SYSTEM"
    WORKFLOW_SERVICE = "WORKFLOW_SERVICE"
    NOTIFICATION_SERVICE = "NOTIFICATION_SERVICE"


class CapabilityDescriptor(BaseModel):
    capability_name: str
    category: CapabilityCategory
    description: str
    parameters_schema: Dict[str, Any] = {}
    origin_service: str
    adapter_type: str = "NATIVE_INTERNAL"
    required_roles: List[str] = ["PATIENT_AGENT"]
    is_external: bool = False


class BaseExternalActionAdapter:
    """
    Abstract Base Class for External System Adapters (EHR connectors, External Healthcare APIs, Communication Adapters).
    """

    def __init__(self, adapter_name: str, category: CapabilityCategory):
        self.adapter_name = adapter_name
        self.category = category

    def get_descriptors(self) -> List[CapabilityDescriptor]:
        raise NotImplementedError

    def execute_action(self, capability_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class SampleEHRExternalAdapter(BaseExternalActionAdapter):
    """
    Sample external EHR Integration Adapter (Epic/Cerner FHIR Gateway Connector).
    """

    def __init__(self):
        super().__init__(adapter_name="EpicCernerFHIRGateway", category=CapabilityCategory.EHR_CONNECTOR)

    def get_descriptors(self) -> List[CapabilityDescriptor]:
        return [
            CapabilityDescriptor(
                capability_name="verify_external_appointment",
                category=CapabilityCategory.EHR_CONNECTOR,
                description="Verify external appointment record in hospital EHR FHIR database.",
                parameters_schema={"appointment_id": "string"},
                origin_service="EpicCernerFHIRGateway",
                adapter_type="FHIR_R4_ADAPTER",
                required_roles=["PATIENT_AGENT", "SYSTEM_WORKFLOW"],
                is_external=True
            ),
            CapabilityDescriptor(
                capability_name="synchronize_appointment_state",
                category=CapabilityCategory.EHR_CONNECTOR,
                description="Synchronize platform appointment status with external hospital EHR system.",
                parameters_schema={"appointment_id": "string", "target_status": "string"},
                origin_service="EpicCernerFHIRGateway",
                adapter_type="FHIR_R4_ADAPTER",
                required_roles=["SYSTEM_WORKFLOW", "ADMIN"],
                is_external=True
            )
        ]

    def execute_action(self, capability_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if capability_name == "verify_external_appointment":
            return {
                "verified": True,
                "external_id": f"EHR-EPIC-{arguments.get('appointment_id', 'UNKNOWN')}",
                "sync_status": "SYNCHRONIZED"
            }
        elif capability_name == "synchronize_appointment_state":
            return {
                "synchronized": True,
                "appointment_id": arguments.get("appointment_id"),
                "status": arguments.get("target_status", "CONFIRMED")
            }
        return {"error": "Unsupported capability in external adapter"}


class CapabilityDiscoveryService:
    """
    Centralized Capability Discovery & Standardized Action Invocation Pipeline (Section 5.15).
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.registry = CapabilityRegistry(db_session)
        self.external_adapters: Dict[str, BaseExternalActionAdapter] = {}
        self.descriptors_catalog: Dict[str, CapabilityDescriptor] = {}
        
        self._initialize_native_descriptors()
        self.register_external_adapter(SampleEHRExternalAdapter())

    def _initialize_native_descriptors(self):
        native_caps = [
            ("search_hospitals", CapabilityCategory.INTERNAL_SERVICE, "Search participating hospitals by location or name.", ["PATIENT_AGENT", "ADMIN"]),
            ("search_specialties", CapabilityCategory.INTERNAL_SERVICE, "Search medical departments and clinical specialties.", ["PATIENT_AGENT"]),
            ("search_doctors", CapabilityCategory.SCHEDULING_SERVICE, "Search doctors by specialty, department, or location.", ["PATIENT_AGENT"]),
            ("check_availability", CapabilityCategory.SCHEDULING_SERVICE, "Query centralized availability engine for bookable doctor slots.", ["PATIENT_AGENT"]),
            ("get_doctor_calendar", CapabilityCategory.SCHEDULING_SERVICE, "Fetch doctor aggregated calendar schedule and working hours.", ["PATIENT_AGENT", "HOSPITAL_ADMIN"]),
            ("lookup_patient", CapabilityCategory.INTERNAL_SERVICE, "Lookup patient profile by phone number or ID.", ["PATIENT_AGENT", "ADMIN"]),
            ("create_appointment", CapabilityCategory.SCHEDULING_SERVICE, "Create and request an appointment with database lock and EHR check.", ["PATIENT_AGENT"]),
            ("reschedule_appointment", CapabilityCategory.SCHEDULING_SERVICE, "Request rescheduling of an active appointment.", ["PATIENT_AGENT"]),
            ("cancel_appointment", CapabilityCategory.SCHEDULING_SERVICE, "Cancel an existing appointment.", ["PATIENT_AGENT"]),
            ("get_appointment", CapabilityCategory.SCHEDULING_SERVICE, "Fetch appointment details by ID.", ["PATIENT_AGENT"]),
            ("get_questionnaire", CapabilityCategory.WORKFLOW_SERVICE, "Fetch pre-visit clinical intake questionnaire.", ["PATIENT_AGENT"]),
            ("submit_questionnaire_response", CapabilityCategory.WORKFLOW_SERVICE, "Submit patient answers for pre-visit questionnaire.", ["PATIENT_AGENT"]),
            ("send_notification", CapabilityCategory.NOTIFICATION_SERVICE, "Send SMS or Voice notification to patient.", ["PATIENT_AGENT", "SYSTEM_WORKFLOW"]),
            ("start_workflow", CapabilityCategory.WORKFLOW_SERVICE, "Initiate asynchronous workflow (e.g. Appointment Reminder).", ["PATIENT_AGENT", "SYSTEM_WORKFLOW"]),
            ("get_user_context", CapabilityCategory.INTERNAL_SERVICE, "Fetch patient 4-tier context bundle.", ["PATIENT_AGENT"]),
            ("update_user_preferences", CapabilityCategory.INTERNAL_SERVICE, "Update patient persistent preferences.", ["PATIENT_AGENT"]),
            ("transfer_to_human", CapabilityCategory.COMMUNICATION_SERVICE, "Escalate active conversation to human support representative.", ["PATIENT_AGENT"])
        ]

        for name, category, desc, roles in native_caps:
            self.descriptors_catalog[name] = CapabilityDescriptor(
                capability_name=name,
                category=category,
                description=desc,
                parameters_schema={},
                origin_service="PlatformNativeService",
                adapter_type="NATIVE_INTERNAL",
                required_roles=roles,
                is_external=False
            )

    def register_external_adapter(self, adapter: BaseExternalActionAdapter):
        """
        Dynamically registers an external healthcare system / EHR / communication adapter.
        """
        self.external_adapters[adapter.adapter_name] = adapter
        for desc in adapter.get_descriptors():
            self.descriptors_catalog[desc.capability_name] = desc

    def discover_capabilities(
        self,
        category: Optional[CapabilityCategory] = None,
        caller_role: str = "PATIENT_AGENT"
    ) -> List[CapabilityDescriptor]:
        """
        Standardized Capability Discovery for the AI Agent.
        """
        available = []
        for desc in self.descriptors_catalog.values():
            if caller_role in desc.required_roles or "PATIENT_AGENT" in desc.required_roles:
                if category is None or desc.category == category:
                    available.append(desc)
        return available

    def execute_capability_pipeline(
        self,
        request: CapabilityExecutionRequest
    ) -> CapabilityExecutionResult:
        """
        Standardized Pipeline:
        AI Agent -> Capability Registry -> Available Actions -> Authorized Capability -> Execution -> Verification -> Result
        """
        cap_name = request.capability_name.lower().strip()
        descriptor = self.descriptors_catalog.get(cap_name)

        if not descriptor:
            return CapabilityExecutionResult(
                success=False,
                capability_name=cap_name,
                data={},
                message=f"Capability '{cap_name}' not registered in capability discovery catalog.",
                correlation_id=request.correlation_id
            )

        # Role Authorization Check
        if request.caller_role not in descriptor.required_roles:
            return CapabilityExecutionResult(
                success=False,
                capability_name=cap_name,
                data={},
                message=f"Unauthorized: Role '{request.caller_role}' cannot execute capability '{cap_name}'.",
                correlation_id=request.correlation_id
            )

        # Delegate execution to external adapter if external, otherwise native registry
        if descriptor.is_external and descriptor.origin_service in self.external_adapters:
            adapter = self.external_adapters[descriptor.origin_service]
            try:
                res_data = adapter.execute_action(cap_name, request.arguments)
                return CapabilityExecutionResult(
                    success=True,
                    capability_name=cap_name,
                    data=res_data,
                    message=f"Successfully executed external capability '{cap_name}' via {descriptor.origin_service}.",
                    correlation_id=request.correlation_id
                )
            except Exception as e:
                return CapabilityExecutionResult(
                    success=False,
                    capability_name=cap_name,
                    data={},
                    message=f"External adapter execution failed: {str(e)}",
                    correlation_id=request.correlation_id
                )

        # Native Execution via CapabilityRegistry
        return self.registry.execute(request)
