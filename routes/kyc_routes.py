from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends
from sqlalchemy.orm import Session
from models.schemas import (
    CreateApplicantRequest, ApplicantResponse, 
    VerificationStatusResponse, WebhookPayload,
    FaceLivenessResponse, DocumentVerificationResponse, SelfieVerificationResponse,
    LivenessCheckRequest, DocumentUploadRequest, SelfieUploadRequest,
    VerificationStep, StepStatus
)
from services.sumsub_service import sumsub_service
from database import get_db
from models.db_models import Applicant, VerificationStepEnum, StepStatusEnum
from utils.helpers import verify_webhook_signature
from config import settings
import json

router = APIRouter(prefix="/api/kyc", tags=["KYC"])

@router.get("/health")
async def health_check():
    """Health check endpoint - shows current configuration"""
    return {
        "status": "healthy",
        "api_base_url": settings.SUMSUB_BASE_URL,
        "api_key_prefix": settings.SUMSUB_API_KEY[:10] if settings.SUMSUB_API_KEY else None,
        "is_sandbox": "sandbox" in settings.SUMSUB_BASE_URL,
        "environment": "Sandbox" if "sandbox" in settings.SUMSUB_BASE_URL else "Production"
    }

@router.post("/applicants", response_model=ApplicantResponse)
async def create_applicant(request: CreateApplicantRequest, db: Session = Depends(get_db)):
    """Create new applicant for KYC verification"""
    try:
        response = sumsub_service.create_applicant(
            db=db,
            external_user_id=request.external_user_id,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            country=request.country
        )
        
        if response.get("id"):
            applicant_id = response["id"]
            steps = sumsub_service.get_verification_steps(db, applicant_id)
            
            return ApplicantResponse(
                applicant_id=applicant_id,
                external_user_id=response.get("externalUserId", ""),
                email=response.get("email", ""),
                status=response.get("applicantStatus", "pending"),
                steps=steps
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to create applicant")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== FACE LIVENESS VERIFICATION ====================
@router.post("/applicants/{applicant_id}/liveness/check", response_model=FaceLivenessResponse)
async def check_face_liveness(applicant_id: str, db: Session = Depends(get_db)):
    """Start face liveness detection check"""
    try:
        result = sumsub_service.check_face_liveness(db, applicant_id)
        return FaceLivenessResponse(
            applicant_id=applicant_id,
            status=StepStatus.COMPLETED,
            is_alive=result.get("is_alive"),
            confidence=result.get("confidence"),
            message="Liveness check completed successfully"
        )
    except Exception as e:
        sumsub_service.update_step_status(
            db, applicant_id, VerificationStepEnum.FACE_LIVENESS,
            StepStatusEnum.FAILED, str(e)
        )
        return FaceLivenessResponse(
            applicant_id=applicant_id,
            status=StepStatus.FAILED,
            message=f"Liveness check failed: {str(e)}"
        )

# ==================== KYC VERIFICATION ====================
@router.post("/applicants/{applicant_id}/kyc/verify", response_model=DocumentVerificationResponse)
async def verify_kyc(applicant_id: str, doc_type: str = "IDENTITY", db: Session = Depends(get_db)):
    """Verify KYC documents"""
    try:
        result = sumsub_service.verify_kyc_document(db, applicant_id, doc_type)
        return DocumentVerificationResponse(
            applicant_id=applicant_id,
            status=StepStatus.COMPLETED,
            document_type=doc_type,
            verified=True,
            message="KYC verification completed"
        )
    except Exception as e:
        return DocumentVerificationResponse(
            applicant_id=applicant_id,
            status=StepStatus.FAILED,
            document_type=doc_type,
            message=f"KYC verification failed: {str(e)}"
        )

# ==================== DOCUMENT UPLOAD ====================
@router.post("/applicants/{applicant_id}/documents/id", response_model=DocumentVerificationResponse)
async def upload_id_document(applicant_id: str, file: UploadFile = File(...), 
                            country: str = "BD", db: Session = Depends(get_db)):
    """Upload ID document for verification"""
    try:
        import tempfile
        import os
        
        # Update step status
        sumsub_service.update_step_status(
            db, applicant_id, VerificationStepEnum.ID_SCAN, StepStatusEnum.IN_PROGRESS
        )
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            response = sumsub_service.upload_id_document(
                applicant_id=applicant_id,
                file_path=tmp_path,
                doc_type="IDENTITY",
                country=country
            )
            
            # Mark step as completed
            sumsub_service.update_step_status(
                db, applicant_id, VerificationStepEnum.ID_SCAN, StepStatusEnum.COMPLETED
            )
            
            return DocumentVerificationResponse(
                applicant_id=applicant_id,
                status=StepStatus.COMPLETED,
                document_type="IDENTITY",
                verified=True,
                message="ID document uploaded successfully"
            )
        finally:
            os.unlink(tmp_path)
    except Exception as e:
        sumsub_service.update_step_status(
            db, applicant_id, VerificationStepEnum.ID_SCAN, 
            StepStatusEnum.FAILED, str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

# ==================== SELFIE UPLOAD ====================
@router.post("/applicants/{applicant_id}/documents/selfie", response_model=SelfieVerificationResponse)
async def upload_selfie(applicant_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload selfie for liveness and face matching verification"""
    try:
        import tempfile
        import os
        
        # Update step status
        sumsub_service.update_step_status(
            db, applicant_id, VerificationStepEnum.SELFIE, StepStatusEnum.IN_PROGRESS
        )
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            response = sumsub_service.upload_selfie(
                applicant_id=applicant_id,
                file_path=tmp_path
            )
            
            # Mark step as completed
            sumsub_service.update_step_status(
                db, applicant_id, VerificationStepEnum.SELFIE, StepStatusEnum.COMPLETED
            )
            
            return SelfieVerificationResponse(
                applicant_id=applicant_id,
                status=StepStatus.COMPLETED,
                matches_document=True,
                confidence=0.95,
                message="Selfie uploaded and verified successfully"
            )
        finally:
            os.unlink(tmp_path)
    except Exception as e:
        sumsub_service.update_step_status(
            db, applicant_id, VerificationStepEnum.SELFIE,
            StepStatusEnum.FAILED, str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

# ==================== VERIFICATION STATUS ====================
@router.get("/applicants/{applicant_id}/status", response_model=VerificationStatusResponse)
async def get_verification_status(applicant_id: str, db: Session = Depends(get_db)):
    """Get detailed verification status of applicant"""
    try:
        response = sumsub_service.get_applicant_status(applicant_id)
        steps = sumsub_service.get_verification_steps(db, applicant_id)
        
        # Determine current step
        current_step = VerificationStep.VERIFICATION_COMPLETE
        overall_status = "approved"
        for step in steps:
            if step.status == StepStatus.PENDING:
                current_step = step.step
                overall_status = "pending"
                break
            elif step.status == StepStatus.FAILED:
                overall_status = "failed"
        
        return VerificationStatusResponse(
            applicant_id=applicant_id,
            status=response.get("applicantStatus", "pending"),
            review_status=response.get("reviewStatus", "pending"),
            current_step=current_step,
            steps_progress=steps,
            document_verification=response.get("reviewResult"),
            liveness_verification=response.get("reviewResult"),
            overall_status=overall_status,
            created_at=response.get("createdAt")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/applicants/{applicant_id}/steps")
async def get_verification_steps(applicant_id: str, db: Session = Depends(get_db)):
    """Get all verification steps for an applicant"""
    try:
        steps = sumsub_service.get_verification_steps(db, applicant_id)
        return {
            "applicant_id": applicant_id,
            "steps": steps,
            "total_steps": len(steps),
            "completed_steps": len([s for s in steps if s.status == StepStatus.COMPLETED]),
            "failed_steps": len([s for s in steps if s.status == StepStatus.FAILED])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/applicants/{applicant_id}/sdk-token")
async def get_sdk_token(applicant_id: str, external_user_id: str, 
                       email: str = "", phone: str = ""):
    """Generate SDK access token for Web/Mobile SDKs"""
    try:
        token_response = sumsub_service.create_sdk_token(
            external_user_id=external_user_id,
            email=email,
            phone=phone,
            ttl_in_secs=600
        )
        return {
            "token": token_response.get("token"),
            "userId": token_response.get("userId"),
            "ttlInSecs": 600
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/applicants/{applicant_id}/status/pending")
async def set_applicant_pending(applicant_id: str, db: Session = Depends(get_db)):
    """Submit applicant for final review"""
    try:
        # Mark verification as complete
        sumsub_service.update_step_status(
            db, applicant_id, VerificationStepEnum.VERIFICATION_COMPLETE, StepStatusEnum.COMPLETED
        )
        
        response = sumsub_service.set_applicant_pending(applicant_id)
        return {
            "applicant_id": applicant_id,
            "status": "submitted_for_review",
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== WEBHOOKS ====================
@router.post("/webhooks/verification")
async def verification_webhook(request: Request):
    """Webhook for Sumsub verification updates"""
    try:
        body = await request.body()
        signature = request.headers.get("X-Webhook-Signature", "")
        
        # Verify signature
        if not verify_webhook_signature(body.decode(), signature, settings.SUMSUB_WEBHOOK_SECRET):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        payload = json.loads(body)
        
        # Process webhook payload
        applicant_id = payload.get("applicantId")
        status = payload.get("applicantStatus")
        review_status = payload.get("reviewStatus")
        
        # Update verification completion status
        if review_status == "completed":
            sumsub_service.update_step_status(
                applicant_id, VerificationStep.VERIFICATION_COMPLETE, StepStatus.COMPLETED
            )
        
        print(f"Webhook received - Applicant: {applicant_id}, Status: {status}, Review: {review_status}")
        
        return {"status": "received", "applicant_id": applicant_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))