import requests
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from config import settings
from utils.helpers import prepare_headers, generate_signature
from utils.exceptions import SumsubAPIError, DocumentUploadError, ApplicantNotFoundError
from models.schemas import VerificationStep, StepStatus, StepStatusDetail
from models.db_models import (
    Applicant, VerificationStep as VerificationStepDB, Document, ApplicantStatus,
    VerificationStepEnum, StepStatusEnum
)

class SumsubService:
    def __init__(self):
        self.base_url = settings.SUMSUB_BASE_URL
        self.api_key = settings.SUMSUB_API_KEY
        self.api_secret = settings.SUMSUB_API_SECRET
        self.level_name = settings.SUMSUB_LEVEL_NAME
    
    def create_applicant(self, db: Session, external_user_id: str, email: str = "", 
                        first_name: str = "", last_name: str = "", country: str = "") -> Dict[str, Any]:
        """
        Create a new applicant via official API flow
        POST /resources/applicants?levelName={levelName}
        
        Args:
            external_user_id: Unique user ID
            email: User email (optional)
            first_name: User first name (optional)
            last_name: User last name (optional)
        """
        method = "POST"
        path = f"/resources/applicants?levelName={self.level_name}"
        
        payload = {
            "externalUserId": external_user_id
        }
        
        # Add additional info if provided
        if email or first_name or last_name:
            payload["info"] = {
                "firstName": first_name or "",
                "lastName": last_name or "",
                "email": email or ""
            }
        
        body = json.dumps(payload)
        headers = prepare_headers(method, path, body, self.api_key, self.api_secret)
        
        response = requests.post(
            f"{self.base_url}{path}",
            headers=headers,
            data=body
        )
        
        if response.status_code not in [200, 201]:
            raise SumsubAPIError(
                message=f"Failed to create applicant: {response.status_code}",
                status_code=response.status_code,
                details={"response": response.text}
            )
        
        api_response = response.json()
        applicant_id = api_response.get("id")
        
        # Save to database
        db_applicant = Applicant(
            id=applicant_id,
            external_user_id=external_user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            country=country,
            status=ApplicantStatus.CREATED,
            sumsub_created_at=datetime.utcnow()
        )
        db.add(db_applicant)
        db.commit()
        db.refresh(db_applicant)
        
        # Initialize verification steps
        self.initialize_verification_steps(db, applicant_id)
        
        return api_response
    
    def get_applicant(self, applicant_id: str) -> Dict[str, Any]:
        """
        Get applicant full data via official API
        GET /resources/applicants/{applicantId}
        """
        method = "GET"
        path = f"/resources/applicants/{applicant_id}"
        
        headers = prepare_headers(method, path, "", self.api_key, self.api_secret)
        
        response = requests.get(
            f"{self.base_url}{path}",
            headers=headers
        )
        
        if response.status_code == 404:
            raise ApplicantNotFoundError(applicant_id)
        
        if response.status_code != 200:
            raise SumsubAPIError(
                message=f"Failed to get applicant: {response.status_code}",
                status_code=response.status_code,
                details={"response": response.text}
            )
        
        return response.json()
    
    def get_applicant_status(self, applicant_id: str) -> Dict[str, Any]:
        """
        Get applicant review status
        Wrapper around get_applicant() to extract status fields
        """
        applicant = self.get_applicant(applicant_id)
        
        return {
            "applicantId": applicant.get("id"),
            "applicantStatus": applicant.get("applicantStatus"),
            "reviewStatus": applicant.get("reviewStatus"),
            "reviewResult": applicant.get("review", {}).get("reviewResult") if applicant.get("review") else None,
            "createdAt": applicant.get("createdAt")
        }
    
    def initialize_verification_steps(self, db: Session, applicant_id: str) -> Dict[str, Any]:
        """Initialize verification steps tracking for an applicant in database"""
        steps = [
            VerificationStepEnum.FACE_LIVENESS,
            VerificationStepEnum.KYC_VERIFICATION,
            VerificationStepEnum.ID_SCAN,
            VerificationStepEnum.SELFIE,
            VerificationStepEnum.VERIFICATION_COMPLETE
        ]
        
        for step in steps:
            db_step = VerificationStepDB(
                applicant_id=applicant_id,
                step=step,
                status=StepStatusEnum.PENDING
            )
            db.add(db_step)
        
        db.commit()
        return {"applicant_id": applicant_id, "steps_initialized": len(steps)}
    
    def update_step_status(self, db: Session, applicant_id: str, step: VerificationStepEnum, 
                          status: StepStatusEnum, error_message: str = None) -> Dict[str, Any]:
        """Update the status of a verification step in database"""
        db_step = db.query(VerificationStepDB).filter(
            VerificationStepDB.applicant_id == applicant_id,
            VerificationStepDB.step == step
        ).first()
        
        if not db_step:
            raise ValueError(f"Step {step} not found for applicant {applicant_id}")
        
        db_step.status = status
        db_step.error_message = error_message
        
        if status == StepStatusEnum.IN_PROGRESS:
            db_step.started_at = datetime.utcnow()
        elif status == StepStatusEnum.COMPLETED:
            db_step.completed_at = datetime.utcnow()
        
        db_step.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_step)
        
        return {"step": step, "status": status, "updated_at": db_step.updated_at.isoformat()}
    
    def get_verification_steps(self, db: Session, applicant_id: str) -> list:
        """Get all verification steps for an applicant from database"""
        db_steps = db.query(VerificationStepDB).filter(
            VerificationStepDB.applicant_id == applicant_id
        ).all()
        
        return [
            StepStatusDetail(
                step=VerificationStep(step.step.value),
                status=StepStatus(step.status.value),
                completed_at=step.completed_at.isoformat() if step.completed_at else None,
                error_message=step.error_message
            )
            for step in db_steps
        ]
    
    def check_face_liveness(self, db: Session, applicant_id: str, video_data: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Check face liveness for applicant
        POST /resources/applicants/{applicantId}/info/faceLiveness
        
        Returns:
            Dict with is_alive, confidence, and status
        """
        try:
            # Update step to in-progress
            self.update_step_status(db, applicant_id, VerificationStepEnum.FACE_LIVENESS, StepStatusEnum.IN_PROGRESS)
            
            method = "POST"
            path = f"/resources/applicants/{applicant_id}/info/faceLiveness"
            
            timestamp = int(time.time())
            signature = generate_signature(method, path, "", timestamp, self.api_secret)
            
            headers = {
                "X-App-Token": self.api_key,
                "X-App-Access-Ts": str(timestamp),
                "X-App-Access-Sig": signature
            }
            
            # If video data provided, send as file, otherwise make empty POST
            if video_data:
                files = {'content': ('liveness.mp4', video_data, 'video/mp4')}
                response = requests.post(
                    f"{self.base_url}{path}",
                    headers=headers,
                    files=files
                )
            else:
                response = requests.post(
                    f"{self.base_url}{path}",
                    headers=headers
                )
            
            if response.status_code not in [200, 201]:
                self.update_step_status(
                    db, applicant_id, VerificationStepEnum.FACE_LIVENESS, 
                    StepStatusEnum.FAILED, f"API Error: {response.status_code}"
                )
                raise SumsubAPIError(
                    message=f"Face liveness check failed: {response.status_code}",
                    status_code=response.status_code,
                    details={"response": response.text}
                )
            
            result = response.json()
            
            # Mark step as completed
            self.update_step_status(db, applicant_id, VerificationStepEnum.FACE_LIVENESS, StepStatusEnum.COMPLETED)
            
            return {
                "applicant_id": applicant_id,
                "is_alive": result.get("isAlive", False),
                "confidence": result.get("confidence", 0),
                "status": "completed"
            }
        except Exception as e:
            self.update_step_status(
                db, applicant_id, VerificationStepEnum.FACE_LIVENESS, 
                StepStatusEnum.FAILED, str(e)
            )
            raise
    
    def verify_kyc_document(self, db: Session, applicant_id: str, doc_type: str = "IDENTITY") -> Dict[str, Any]:
        """
        Mark KYC verification step as completed
        """
        try:
            self.update_step_status(db, applicant_id, VerificationStepEnum.KYC_VERIFICATION, StepStatusEnum.IN_PROGRESS)
            
            # Simulate KYC verification - in production, call actual API
            # For now, mark as completed
            self.update_step_status(db, applicant_id, VerificationStepEnum.KYC_VERIFICATION, StepStatusEnum.COMPLETED)
            
            return {
                "applicant_id": applicant_id,
                "document_type": doc_type,
                "status": "verified"
            }
        except Exception as e:
            self.update_step_status(
                db, applicant_id, VerificationStepEnum.KYC_VERIFICATION, 
                StepStatusEnum.FAILED, str(e)
            )
            raise
    
    def upload_id_document(self, applicant_id: str, file_path: str, 
                          doc_type: str = "IDENTITY", country: str = "BD") -> Dict[str, Any]:
        """
        Upload ID document via official API
        POST /resources/applicants/{applicantId}/info/idDoc
        
        Args:
            applicant_id: Applicant ID
            file_path: Path to document file
            doc_type: Document type (IDENTITY, SELFIE, etc.)
            country: Country code
        """
        method = "POST"
        path = f"/resources/applicants/{applicant_id}/info/idDoc"
        
        timestamp = int(time.time())
        # For file uploads, body is empty in signature
        signature = generate_signature(method, path, "", timestamp, self.api_secret)
        
        headers = {
            "X-App-Token": self.api_key,
            "X-App-Access-Ts": str(timestamp),
            "X-App-Access-Sig": signature
        }
        
        metadata = {
            "idDocType": doc_type,
            "country": country
        }
        
        with open(file_path, 'rb') as f:
            files = {
                'metadata': (None, json.dumps(metadata), 'application/json'),
                'content': (f.name, f, 'image/jpeg')
            }
            response = requests.post(
                f"{self.base_url}{path}",
                headers=headers,
                files=files
            )
        
        if response.status_code not in [200, 201]:
            raise DocumentUploadError(
                message=f"Failed to upload ID document: {response.status_code}",
                details={"response": response.text}
            )
        
        return response.json()
    
    def upload_selfie(self, applicant_id: str, file_path: str) -> Dict[str, Any]:
        """
        Upload selfie/face photo via official API
        POST /resources/applicants/{applicantId}/info/idDoc
        """
        return self.upload_id_document(applicant_id, file_path, "SELFIE")
    
    def set_applicant_pending(self, applicant_id: str) -> Dict[str, Any]:
        """
        Move applicant to pending review
        POST /resources/applicants/{applicantId}/status/pending
        
        Call this after uploading all required documents
        """
        method = "POST"
        path = f"/resources/applicants/{applicant_id}/status/pending"
        
        headers = prepare_headers(method, path, "", self.api_key, self.api_secret)
        
        response = requests.post(
            f"{self.base_url}{path}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise SumsubAPIError(
                message=f"Failed to set applicant pending: {response.status_code}",
                status_code=response.status_code,
                details={"response": response.text}
            )
        
        return response.json()
    
    def create_sdk_token(self, external_user_id: str, 
                        email: str = "", phone: str = "", 
                        ttl_in_secs: int = 600) -> Dict[str, Any]:
        """
        Generate SDK access token for Web/Mobile SDKs
        POST /resources/accessTokens/sdk
        
        Args:
            external_user_id: External user ID
            email: User email (optional)
            phone: User phone (optional)
            ttl_in_secs: Token TTL in seconds
        
        Returns:
            Dict with 'token' and 'userId' fields
        """
        method = "POST"
        path = "/resources/accessTokens/sdk"
        
        payload = {
            "applicantIdentifiers": {},
            "ttlInSecs": ttl_in_secs,
            "userId": external_user_id,
            "levelName": self.level_name
        }
        
        # Add available identifiers
        if email:
            payload["applicantIdentifiers"]["email"] = email
        if phone:
            payload["applicantIdentifiers"]["phone"] = phone
        
        body = json.dumps(payload)
        headers = prepare_headers(method, path, body, self.api_key, self.api_secret)
        
        response = requests.post(
            f"{self.base_url}{path}",
            headers=headers,
            data=body
        )
        
        if response.status_code not in [200, 201]:
            raise SumsubAPIError(
                message=f"Failed to create SDK token: {response.status_code}",
                status_code=response.status_code,
                details={"response": response.text}
            )
        
        return response.json()

# Singleton instance
sumsub_service = SumsubService()
