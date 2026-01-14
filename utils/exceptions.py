"""
Custom exception classes and error handling utilities for KYC Verification
"""

from typing import Dict, Any, Optional


class KYCException(Exception):
    """Base exception class for KYC verification"""
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR", 
                 status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


class SumsubAPIError(KYCException):
    """Exception for Sumsub API errors"""
    def __init__(self, message: str, status_code: int = 400, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="SUMSUB_API_ERROR",
            status_code=status_code,
            details=details
        )


class ApplicantNotFoundError(KYCException):
    """Exception when applicant is not found"""
    def __init__(self, applicant_id: str):
        super().__init__(
            message=f"Applicant with ID {applicant_id} not found",
            error_code="APPLICANT_NOT_FOUND",
            status_code=404,
            details={"applicant_id": applicant_id}
        )


class InvalidDocumentError(KYCException):
    """Exception for invalid document uploads"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="INVALID_DOCUMENT",
            status_code=400,
            details=details
        )


class DocumentUploadError(KYCException):
    """Exception for document upload failures"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DOCUMENT_UPLOAD_FAILED",
            status_code=400,
            details=details
        )


class AuthenticationError(KYCException):
    """Exception for authentication failures"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401
        )


class ValidationError(KYCException):
    """Exception for validation errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=details
        )


class ConfigurationError(KYCException):
    """Exception for configuration errors"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500
        )


def format_error_response(exception: KYCException) -> Dict[str, Any]:
    """Format exception as API response"""
    return {
        "success": False,
        "error": exception.error_code,
        "message": exception.message,
        "details": exception.details
    }


def handle_api_error(response_data: Dict[str, Any]) -> None:
    """Handle API error responses from Sumsub"""
    error_message = response_data.get("description", "Unknown error from Sumsub API")
    error_code = response_data.get("errorCode", "UNKNOWN")
    
    raise SumsubAPIError(
        message=error_message,
        status_code=response_data.get("httpStatusCode", 400),
        details={
            "error_code": error_code,
            "error_details": response_data
        }
    )
