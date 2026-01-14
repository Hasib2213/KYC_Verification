from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum

# ==================== Enums ====================
class VerificationStep(str, Enum):
    FACE_LIVENESS = "face_liveness"
    KYC_VERIFICATION = "kyc_verification"
    ID_SCAN = "id_scan"
    SELFIE = "selfie"
    VERIFICATION_COMPLETE = "verification_complete"

class StepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

# ==================== Request Models ====================
class CreateApplicantRequest(BaseModel):
    external_user_id: str
    email: EmailStr
    phone: Optional[str] = None
    first_name: str
    last_name: str
    country: str

class LivenessCheckRequest(BaseModel):
    applicant_id: str
    video_data: Optional[str] = None  # base64 encoded video

class DocumentUploadRequest(BaseModel):
    applicant_id: str
    document_type: str  # "identity", "passport", etc.
    country: str

class SelfieUploadRequest(BaseModel):
    applicant_id: str
    image_data: Optional[str] = None  # base64 encoded image

# ==================== Step Status Models ====================
class StepStatusDetail(BaseModel):
    step: VerificationStep
    status: StepStatus
    completed_at: Optional[str] = None
    error_message: Optional[str] = None

class ApplicantResponse(BaseModel):
    applicant_id: str
    external_user_id: str
    email: str
    status: str
    steps: list[StepStatusDetail] = []

# ==================== Detailed Verification Status ====================
class FaceLivenessResponse(BaseModel):
    applicant_id: str
    status: StepStatus
    is_alive: Optional[bool] = None
    confidence: Optional[float] = None
    message: str

class DocumentVerificationResponse(BaseModel):
    applicant_id: str
    status: StepStatus
    document_type: str
    verified: Optional[bool] = None
    message: str

class SelfieVerificationResponse(BaseModel):
    applicant_id: str
    status: StepStatus
    matches_document: Optional[bool] = None
    confidence: Optional[float] = None
    message: str

class VerificationStatusResponse(BaseModel):
    applicant_id: str
    status: str
    review_status: str
    current_step: VerificationStep
    steps_progress: list[StepStatusDetail]
    document_verification: Optional[str] = None
    liveness_verification: Optional[str] = None
    selfie_verification: Optional[str] = None
    overall_status: str
    created_at: Optional[str] = None

class WebhookPayload(BaseModel):
    applicantId: str
    applicantStatus: str
    reviewStatus: str
    data: Optional[dict] = None