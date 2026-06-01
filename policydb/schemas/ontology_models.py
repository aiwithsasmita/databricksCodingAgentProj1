"""
Pydantic models matching Neo4j ontology schema for Policy Extraction System.

These models define the structure for:
- Policy documents
- Denial Rules
- Fraud Tactics
- Medical codes (CPT, HCPCS, Modifiers)
- Attachments (Excel/CSV)
- Relationships between entities
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


# =============================================================================
# Enums
# =============================================================================

class AttachmentDataType(str, Enum):
    """Type of data contained in attachment"""
    CODE_LIST = "code_list"
    MODIFIER_LIST = "modifier_list"
    BUNDLED_CODES = "bundled_codes"
    REFERENCE_TABLE = "reference_table"
    FEE_SCHEDULE = "fee_schedule"
    OTHER = "other"


class RelationshipType(str, Enum):
    """Valid relationship types in the ontology"""
    CONTAINS_RULE = "CONTAINS_RULE"
    CONTAINS_TACTIC = "CONTAINS_TACTIC"
    HAS_ATTACHMENT = "HAS_ATTACHMENT"
    APPLIES_TO_CPT = "APPLIES_TO_CPT"
    APPLIES_TO_HCPCS = "APPLIES_TO_HCPCS"
    APPLIES_TO_CODE = "APPLIES_TO_CODE"
    REQUIRES_MODIFIER = "REQUIRES_MODIFIER"
    REFERENCES = "REFERENCES"
    REFERENCES_ATTACHMENT = "REFERENCES_ATTACHMENT"
    TRIGGERS_TACTIC = "TRIGGERS_TACTIC"
    BUNDLED_WITH = "BUNDLED_WITH"


# =============================================================================
# Attachment Models
# =============================================================================

class ColumnDefinition(BaseModel):
    """Definition of a column in an attachment"""
    name: str = Field(..., description="Column name/header")
    description: str = Field(..., description="What this column contains")
    sample: Optional[str] = Field(None, description="Sample value from this column")


class Attachment(BaseModel):
    """Policy attachment (Excel/CSV) with auto-generated metadata"""
    attachment_id: str = Field(..., description="Unique ID: ATT-{policy_id}-{seq}")
    policy_id: str = Field(..., description="Parent policy ID")
    original_filename: str = Field(..., description="Original file name")
    attachment_name: str = Field(..., description="LLM-generated meaningful name")
    attachment_description: str = Field(..., description="LLM-generated description of contents")
    file_path: str = Field(..., description="Path to file in kg/attachments/")
    data_type: AttachmentDataType = Field(..., description="Type of data in attachment")
    columns: List[ColumnDefinition] = Field(default_factory=list, description="Column definitions")
    row_count: int = Field(..., description="Total number of rows")
    headers_sample: List[str] = Field(default_factory=list, description="Column headers")
    first_3_rows: List[Dict[str, Any]] = Field(default_factory=list, description="Sample data (first 3 rows)")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)


# =============================================================================
# Code Models
# =============================================================================

class CPTCode(BaseModel):
    """Current Procedural Terminology code"""
    code: str = Field(..., description="CPT code (e.g., '99213')")
    description: str = Field(..., description="Full code description")
    relative_value_units: Optional[float] = Field(None, description="RVU value")


class HCPCSCode(BaseModel):
    """Healthcare Common Procedure Coding System code"""
    code: str = Field(..., description="HCPCS code (e.g., 'A0427')")
    description: str = Field(..., description="Full code description")
    level: Optional[int] = Field(None, description="Level 1 or 2")


class Modifier(BaseModel):
    """Procedure modifier"""
    code: str = Field(..., description="Modifier code (e.g., '25', 'RH')")
    description: str = Field(..., description="Modifier description")
    usage_notes: Optional[str] = Field(None, description="Notes on proper usage")


# =============================================================================
# Policy Model
# =============================================================================

class Policy(BaseModel):
    """Insurance policy document"""
    policy_id: str = Field(..., description="Unique policy identifier (e.g., '2026R0123A')")
    policy_name: str = Field(..., description="Policy name/title")
    policy_type: str = Field(..., description="Type (e.g., 'Reimbursement', 'Medical')")
    version: Optional[str] = Field(None, description="Policy version")
    issuer: str = Field(default="UnitedHealthcare", description="Issuing organization")
    effective_date: Optional[str] = Field(None, description="Effective date")
    expiration_date: Optional[str] = Field(None, description="Expiration date")
    extracted_text: Optional[str] = Field(None, description="Full extracted text")
    summary: Optional[str] = Field(None, description="Brief summary")
    source_url: Optional[str] = Field(None, description="Source URL")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)


# =============================================================================
# Denial Rule Model
# =============================================================================

class DenialRule(BaseModel):
    """Denial rule extracted from policy"""
    rule_id: str = Field(..., description="Unique rule ID (e.g., 'AMB-001')")
    rule_name: str = Field(..., description="Rule name")
    rule_description: str = Field(..., description="Detailed description")
    rule_type: str = Field(..., description="Type (e.g., 'Coding', 'Authorization')")
    condition: str = Field(..., description="Trigger condition in structured format")
    detection_logic: str = Field(..., description="Logic for detecting rule violation")
    denial_reason_code: str = Field(..., description="Standard denial code (e.g., 'AMB-PROV')")
    simulated_example: str = Field(..., description="Example claim scenario")
    active: bool = Field(default=True, description="Whether rule is active")
    
    # Related codes (will also be captured in relationships)
    applicable_codes: List[str] = Field(default_factory=list, description="CPT/HCPCS codes this rule applies to")
    applicable_modifiers: List[str] = Field(default_factory=list, description="Modifiers related to this rule")


# =============================================================================
# Tactic Model (Fraud Pattern)
# =============================================================================

class Tactic(BaseModel):
    """Fraud tactic/exploitation pattern"""
    tactic_id: str = Field(..., description="Unique tactic ID (e.g., 'AMB-FT001')")
    tactic_name: str = Field(..., description="Tactic name")
    tactic_description: str = Field(..., description="Detailed description")
    tactic_type: str = Field(default="Fraud", description="Type (e.g., 'Fraud', 'Abuse')")
    condition: str = Field(..., description="Condition when tactic applies")
    detection_logic: str = Field(..., description="Logic for detecting this tactic")
    tactic_reason_code: Optional[str] = Field(None, description="Tactic code")
    simulated_example: str = Field(..., description="Example fraud scenario")
    risk_level: str = Field(default="HIGH", description="Risk level: HIGH, MEDIUM, LOW")
    cost_impact: Optional[float] = Field(None, description="Estimated cost impact")
    action_steps: List[str] = Field(default_factory=list, description="Steps to address")
    active: bool = Field(default=True, description="Whether tactic is active")
    
    # Related codes
    exploited_codes: List[str] = Field(default_factory=list, description="Codes exploited by this tactic")
    misused_modifiers: List[str] = Field(default_factory=list, description="Modifiers misused")


# =============================================================================
# Relationship Model
# =============================================================================

class Relationship(BaseModel):
    """Relationship between two entities"""
    from_id: str = Field(..., description="Source entity ID")
    relationship_type: str = Field(..., description="Type of relationship")
    to_id: str = Field(..., description="Target entity ID")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Relationship properties")


# =============================================================================
# Extraction Output Model
# =============================================================================

class ExtractionOutput(BaseModel):
    """Complete extraction output conforming to ontology"""
    policy: Policy
    denial_rules: List[DenialRule] = Field(default_factory=list)
    tactics: List[Tactic] = Field(default_factory=list)
    cpt_codes: List[CPTCode] = Field(default_factory=list)
    hcpcs_codes: List[HCPCSCode] = Field(default_factory=list)
    modifiers: List[Modifier] = Field(default_factory=list)
    attachments: List[Attachment] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    
    def total_nodes(self) -> int:
        """Count total nodes"""
        return (
            1 +  # policy
            len(self.denial_rules) +
            len(self.tactics) +
            len(self.cpt_codes) +
            len(self.hcpcs_codes) +
            len(self.modifiers) +
            len(self.attachments)
        )


# =============================================================================
# Validation Models
# =============================================================================

class ValidationFix(BaseModel):
    """Record of a field that was fixed during validation"""
    node_type: str
    node_id: str
    field: str
    source: str
    original_value: Optional[str] = None
    fixed_value: str
    action: str = "extracted"


class ValidationReport(BaseModel):
    """Report from validation agent"""
    total_nodes: int
    validated: int
    errors_found: int
    fixed: int
    retry_count: int = 0
    fixes: List[ValidationFix] = Field(default_factory=list)
    remaining_errors: List[str] = Field(default_factory=list)
    attachments_processed: int = 0
    is_valid: bool = False
    timestamp: datetime = Field(default_factory=datetime.now)


# =============================================================================
# Enhanced Neo4j-Ready Models (V2)
# =============================================================================

class SeverityLevel(str, Enum):
    """Severity/Risk levels (lowercase)"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DetectionLogic(BaseModel):
    """
    Structured detection logic for rules - DYNAMIC, extracted from policy.
    
    IMPORTANT: This model contains COMMON fields, but LLM can add ANY new field
    discovered in the policy text. Use 'custom_conditions' and 'extra_fields' 
    for policy-specific conditions not listed here.
    """
    # Core matching conditions
    same_date_of_service: bool = False
    same_provider_tin: bool = False
    same_rendering_provider: bool = False  # Different from billing TIN
    same_member: bool = False
    same_claim: bool = False
    same_specialty: bool = False
    same_taxonomy: bool = False
    same_facility: bool = False
    same_encounter: bool = False
    
    # Time-based conditions
    time_window: Optional[str] = None  # "same day", "within X days", "global period", "X hours"
    global_period_days: Optional[int] = None  # 0, 10, 90 days
    
    # Patient criteria
    age_requirement: Optional[Dict[str, Any]] = None  # {"min": 0, "max": 18, "unit": "years"}
    gender_requirement: Optional[str] = None  # "M", "F", null
    diagnosis_requirement: Optional[str] = None  # Specific diagnosis or category
    
    # Quantity/Frequency limits
    quantity_limit: Optional[Dict[str, Any]] = None  # {"max_units": 4, "per_period": "day"}
    frequency_limit: Optional[Dict[str, Any]] = None  # {"max_times": 1, "per_period": "day"}
    session_limit: Optional[Dict[str, Any]] = None  # {"max_sessions": X, "per_period": "week"}
    
    # Code-related conditions
    code_combination: Optional[str] = None
    primary_code_required: bool = False  # For add-on codes
    bundling_logic: Optional[str] = None  # What codes are bundled together
    modifier_requirements: Optional[str] = None  # When specific modifier required
    
    # Facility/Setting restrictions
    facility_type_restriction: List[str] = Field(default_factory=list)  # ["inpatient", "outpatient", "ASC"]
    place_of_service_exclusions: List[str] = Field(default_factory=list)  # POS codes excluded
    
    # Authorization/Documentation
    authorization_required: bool = False
    medical_necessity: bool = False
    documentation_required: Optional[str] = None  # What documentation needed
    
    # Provider-related conditions
    incident_to_rules: bool = False
    supervision_level: Optional[str] = None  # "direct", "general", "personal"
    assistant_surgeon_rules: Optional[str] = None
    split_care_rules: Optional[str] = None
    
    # Anatomical/Procedure conditions
    anatomical_site: Optional[str] = None  # "same site", "different site", "bilateral"
    multiple_procedure_reduction: bool = False
    
    # Time-based billing
    time_based_billing: Optional[Dict[str, Any]] = None  # {"min_time": 30, "unit": "minutes"}
    
    # All conditions from policy (dynamic - LIST EVERYTHING)
    conditions: List[str] = Field(default_factory=list)
    custom_conditions: List[str] = Field(default_factory=list)  # Policy-specific
    
    # Extra fields for ANY condition not listed above
    extra_fields: Dict[str, Any] = Field(default_factory=dict)  # Catch-all for new conditions
    
    # Statistical thresholds (for fraud detection)
    frequency_threshold: Optional[str] = None  # ">80% of claims"
    comparison_metric: Optional[str] = None  # "vs peer average"
    time_period: Optional[str] = None  # "90 days"
    statistical_test: Optional[str] = None  # "Z-score > 3"
    outlier_detection: bool = False
    pattern_type: Optional[str] = None  # "systematic", "sporadic", "escalating"
    peer_group: Optional[str] = None  # "same specialty", "same geography"
    volume_threshold: Optional[Dict[str, Any]] = None  # {"min_claims": 10, "period": "month"}
    trend_analysis: Optional[str] = None  # "increasing", "sudden spike"
    billing_ratio: Optional[str] = None  # "E/M to injection ratio"
    timing_patterns: Optional[str] = None  # "end of day clustering"


class SimulatedClaimLine(BaseModel):
    """A single line in a simulated claim"""
    line: int
    cpt: str
    modifier: Optional[str] = ""
    pos: Optional[str] = None
    amount: float = 0.0


class SimulatedClaim(BaseModel):
    """Simulated claim example for denial rules"""
    claim_lines: List[SimulatedClaimLine] = Field(default_factory=list)
    denial_reason: str = ""
    paid_lines: List[int] = Field(default_factory=list)
    denied_lines: List[int] = Field(default_factory=list)


class SimulatedAbuse(BaseModel):
    """Simulated abuse example for fraud tactics"""
    abusive_claims: List[Dict[str, Any]] = Field(default_factory=list)
    legitimate_claims: List[Dict[str, Any]] = Field(default_factory=list)
    why_abusive: str = ""
    financial_impact: str = ""


class ValidationMetadata(BaseModel):
    """Validation metadata attached to rules/tactics"""
    source_text_status: str = "unknown"  # verified, fixed, not_found
    action: str = "original"  # original, enhanced, new


class DenialRuleV2(BaseModel):
    """Enhanced Denial Rule matching Neo4j ontology (V2)"""
    # Identity & Versioning
    rule_uid: str = Field(..., description="Unique: rule_key:date")
    rule_key: str = Field(..., description="Stable ID (e.g., DENY_001)")
    rule_name: str = Field(..., description="Clear descriptive name")
    version: str = Field(default="1.0")
    effective_date: str = Field(..., description="YYYY-MM-DD")
    end_date: Optional[str] = None
    status: str = Field(default="active")
    
    # Rule Details
    severity: SeverityLevel = Field(default=SeverityLevel.MEDIUM)
    description: str = Field(..., description="2-3 sentences")
    source_text: str = Field(..., description="EXACT quote from policy")
    policy_reference: str = Field(default="")
    qa_reference: Optional[str] = None
    
    # Required Data
    required_columns: List[str] = Field(default_factory=list)
    
    # Detection
    detection_logic: DetectionLogic = Field(default_factory=DetectionLogic)
    simulated_claim: SimulatedClaim = Field(default_factory=SimulatedClaim)
    detection_sql: str = Field(default="")
    detection_python: str = Field(default="")
    codification_steps: List[str] = Field(default_factory=list)
    
    # Analytics (initialized to 0)
    total_times_fired: int = 0
    total_denials: int = 0
    total_financial_impact: float = 0.0
    total_members_affected: int = 0
    total_providers_affected: int = 0
    
    # Validation metadata
    _validation: Optional[ValidationMetadata] = None


class FraudTacticV2(BaseModel):
    """Enhanced Fraud Tactic matching Neo4j ontology (V2)"""
    # Identity & Versioning
    tactic_uid: str = Field(..., description="Unique: tactic_key:date")
    tactic_key: str = Field(..., description="Stable ID (e.g., FRAUD_001)")
    tactic_name: str = Field(..., description="Clear descriptive name")
    version: str = Field(default="1.0")
    effective_date: str = Field(..., description="YYYY-MM-DD")
    end_date: Optional[str] = None
    status: str = Field(default="active")
    
    # Tactic Details
    risk_level: SeverityLevel = Field(default=SeverityLevel.MEDIUM)
    description: str = Field(..., description="How providers abuse this")
    fraud_pattern: str = Field(..., description="Detailed exploitation method")
    source_text: str = Field(..., description="EXACT quote from policy")
    policy_reference: str = Field(default="")
    
    # Required Data
    required_columns: List[str] = Field(default_factory=list)
    
    # Detection
    detection_logic: DetectionLogic = Field(default_factory=DetectionLogic)
    red_flags: List[str] = Field(default_factory=list)
    simulated_abuse: SimulatedAbuse = Field(default_factory=SimulatedAbuse)
    detection_sql: str = Field(default="")
    detection_python: str = Field(default="")
    codification_steps: List[str] = Field(default_factory=list)
    
    # Financial
    estimated_overpayment_per_claim: float = 0.0
    
    # Analytics (initialized to 0)
    total_times_detected: int = 0
    total_providers_flagged: int = 0
    total_suspicious_claims: int = 0
    total_estimated_fraud_amount: float = 0.0
    
    # Validation metadata
    _validation: Optional[ValidationMetadata] = None


class POSCode(BaseModel):
    """Place of Service code"""
    code: str = Field(..., description="POS code (e.g., '21')")
    description: Optional[str] = None
    category: str = Field(default="", description="facility or non-facility")


class DRGCode(BaseModel):
    """Diagnosis Related Group code"""
    code: str = Field(..., description="DRG code (e.g., '470')")
    description: Optional[str] = None
    mdc: Optional[str] = None  # Major Diagnostic Category
    weight: Optional[float] = None


class ICD10Code(BaseModel):
    """ICD-10 Diagnosis code"""
    code: str = Field(..., description="ICD-10 code (e.g., 'Z23', 'J18.9')")
    description: Optional[str] = None
    category: Optional[str] = None
    chapter: Optional[str] = None
    is_primary_allowed: bool = True


class AddOnCode(BaseModel):
    """Add-on CPT code that requires a primary code"""
    code: str = Field(..., description="Add-on CPT code (e.g., '99417')")
    description: Optional[str] = None
    primary_codes: List[str] = Field(default_factory=list, description="Required primary codes")


class RevenueCode(BaseModel):
    """Revenue code for facility billing"""
    code: str = Field(..., description="Revenue code (e.g., '0450')")
    description: Optional[str] = None
    category: Optional[str] = None
    facility_type: Optional[str] = None


class NDCCode(BaseModel):
    """National Drug Code"""
    code: str = Field(..., description="NDC code (e.g., '00000-0000-00')")
    description: Optional[str] = None
    drug_class: Optional[str] = None
    route: Optional[str] = None


class TaxonomyCode(BaseModel):
    """Provider Taxonomy/Specialty code"""
    code: str = Field(..., description="Taxonomy code (e.g., '207Q00000X')")
    description: Optional[str] = None
    classification: Optional[str] = None
    specialization: Optional[str] = None
    provider_type: Optional[str] = None  # "Individual" or "Organization"


class RequiredCodes(BaseModel):
    """All code types that can be required by a rule/tactic"""
    cpt_codes: List[str] = Field(default_factory=list)
    hcpcs_codes: List[str] = Field(default_factory=list)
    modifiers: List[str] = Field(default_factory=list)
    place_of_service: List[str] = Field(default_factory=list)
    drg_codes: List[str] = Field(default_factory=list)
    icd10_codes: List[str] = Field(default_factory=list)
    addon_codes: List[str] = Field(default_factory=list)
    revenue_codes: List[str] = Field(default_factory=list)
    ndc_codes: List[str] = Field(default_factory=list)
    taxonomy_codes: List[str] = Field(default_factory=list)


class Neo4jRelationship(BaseModel):
    """Relationship definition for Neo4j loading"""
    from_node: str = Field(..., description="Format: Label:id")
    type: str = Field(..., description="Relationship type")
    to_node: str = Field(..., description="Format: Label:id")
    properties: Dict[str, Any] = Field(default_factory=dict)


class Neo4jReadySummary(BaseModel):
    """Summary of validation/enhancement actions"""
    original_rules: int = 0
    enhanced_rules: int = 0
    new_rules_added: int = 0
    total_rules: int = 0
    original_tactics: int = 0
    enhanced_tactics: int = 0
    new_tactics_added: int = 0
    total_tactics: int = 0


class Neo4jReadyNodes(BaseModel):
    """All nodes for Neo4j loading"""
    policy: Dict[str, Any] = Field(default_factory=dict)
    denial_rules: List[Dict[str, Any]] = Field(default_factory=list)
    fraud_tactics: List[Dict[str, Any]] = Field(default_factory=list)
    cpt_codes: List[Dict[str, str]] = Field(default_factory=list)
    hcpcs_codes: List[Dict[str, str]] = Field(default_factory=list)
    modifiers: List[Dict[str, str]] = Field(default_factory=list)
    pos_codes: List[Dict[str, str]] = Field(default_factory=list)
    drg_codes: List[Dict[str, str]] = Field(default_factory=list)
    icd10_codes: List[Dict[str, str]] = Field(default_factory=list)
    addon_codes: List[Dict[str, Any]] = Field(default_factory=list)
    revenue_codes: List[Dict[str, str]] = Field(default_factory=list)
    ndc_codes: List[Dict[str, str]] = Field(default_factory=list)
    taxonomy_codes: List[Dict[str, str]] = Field(default_factory=list)
    attachments: List[Dict[str, Any]] = Field(default_factory=list)


class Neo4jReadyOutput(BaseModel):
    """Complete Neo4j-ready output from LLM validation agent"""
    policy_id: str
    generated_at: str
    summary: Neo4jReadySummary = Field(default_factory=Neo4jReadySummary)
    nodes: Neo4jReadyNodes = Field(default_factory=Neo4jReadyNodes)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
