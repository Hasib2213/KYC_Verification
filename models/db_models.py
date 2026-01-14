"""
SQLAlchemy database models
"""

from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


class VerificationStepEnum(str, enum.Enum):
    """Verification step types"""
    FACE_LIVENESS = "face_liveness"
    KYC_VERIFICATION = "kyc_verification"
    ID_SCAN = "id_scan"
    SELFIE = "selfie"
    VERIFICATION_COMPLETE = "verification_complete"


class StepStatusEnum(str, enum.Enum):
    """Step status types"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ApplicantStatus(str, enum.Enum):
    """Applicant status types"""
    CREATED = "created"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Applicant(Base):
    """Applicant model for storing applicant information"""
    __tablename__ = "applicants"
    
    id = Column(String(255), primary_key=True, index=True)  # Sumsub applicant ID
    external_user_id = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    country = Column(String(10), nullable=True)
    
    # Status fields
    status = Column(
        SQLEnum(ApplicantStatus),
        default=ApplicantStatus.CREATED,
        nullable=False,
        index=True
    )
    review_status = Column(String(50), nullable=True)  # Sumsub review status
    review_result = Column(String(50), nullable=True)  # Sumsub review result
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    sumsub_created_at = Column(DateTime, nullable=True)
    
    # Relationships
    verification_steps = relationship("VerificationStep", back_populates="applicant", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="applicant", cascade="all, delete-orphan")
    webhook_events = relationship("WebhookEvent", back_populates="applicant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Applicant(id={self.id}, email={self.email}, status={self.status})>"


class VerificationStep(Base):
    """Verification step tracking model"""
    __tablename__ = "verification_steps"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    applicant_id = Column(String(255), ForeignKey("applicants.id"), nullable=False, index=True)
    
    step = Column(
        SQLEnum(VerificationStepEnum),
        nullable=False,
        index=True
    )
    status = Column(
        SQLEnum(StepStatusEnum),
        default=StepStatusEnum.PENDING,
        nullable=False,
        index=True
    )
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    applicant = relationship("Applicant", back_populates="verification_steps")
    
    def __repr__(self):
        return f"<VerificationStep(applicant_id={self.applicant_id}, step={self.step}, status={self.status})>"


class Document(Base):
    """Document storage model"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    applicant_id = Column(String(255), ForeignKey("applicants.id"), nullable=False, index=True)
    
    document_type = Column(String(50), nullable=False, index=True)  # IDENTITY, SELFIE, etc.
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    mime_type = Column(String(100), nullable=True)  # image/jpeg, etc.
    
    # Sumsub metadata
    sumsub_document_id = Column(String(255), nullable=True, index=True)
    upload_status = Column(String(50), default="pending", nullable=False)
    
    # Metadata
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Relationships
    applicant = relationship("Applicant", back_populates="documents")
    
    def __repr__(self):
        return f"<Document(applicant_id={self.applicant_id}, type={self.document_type})>"


class WebhookEvent(Base):
    """Webhook event log model"""
    __tablename__ = "webhook_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    applicant_id = Column(String(255), ForeignKey("applicants.id"), nullable=False, index=True)
    
    event_type = Column(String(100), nullable=False, index=True)
    applicant_status = Column(String(50), nullable=True)
    review_status = Column(String(50), nullable=True)
    review_result = Column(String(50), nullable=True)
    
    # Raw payload
    payload = Column(Text, nullable=True)
    
    # Metadata
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    applicant = relationship("Applicant", back_populates="webhook_events")
    
    def __repr__(self):
        return f"<WebhookEvent(applicant_id={self.applicant_id}, type={self.event_type})>"
