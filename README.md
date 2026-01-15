# KYC Verification API

A comprehensive Know Your Customer (KYC) verification system built with FastAPI and Sumsub integration. This API enables off-site verification through document uploads, liveness checks, and selfie verification.

## Features

✅ **Off-site Verification** - Remote KYC verification without in-person visits  
✅ **Sumsub Integration** - Powered by Sumsub API for reliable verification  
✅ **Multi-step Verification** - Face liveness, document scan, selfie, and KYC verification  
✅ **PostgreSQL Database** - Persistent storage of applicant data and verification history  
✅ **RESTful API** - Clean, documented endpoints for integration  
✅ **Async Support** - Fast, scalable with FastAPI  
✅ **Database Migrations** - Alembic for schema management  

## Project Structure

```
KYC_VERIFICATION/
├── models/
│   ├── db_models.py       # SQLAlchemy database models
│   └── schemas.py         # Pydantic request/response schemas
├── routes/
│   └── kyc_routes.py      # API endpoints
├── services/
│   └── sumsub_service.py  # Sumsub API integration logic
├── utils/
│   ├── exceptions.py      # Custom exceptions
│   ├── helpers.py         # Helper functions (signatures, headers, etc.)
│   └── __init__.py
├── alembic/               # Database migrations
├── main.py                # FastAPI application entry point
├── config.py              # Configuration management
├── database.py            # Database connection and setup
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Sumsub account with API credentials
- pip (Python package manager)

## Installation

### 1. Clone and Setup

```bash
cd KYC_VERIFICATION
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup

Refer to [POSTGRES_SETUP.md](POSTGRES_SETUP.md) for detailed PostgreSQL configuration.

Quick setup:
```bash
# Create database and user
createdb kyc_verification_db
createuser kyc_user
```

### 4. Environment Configuration

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=postgresql://kyc_user:your_password@localhost/kyc_verification_db

# Sumsub API
SUMSUB_BASE_URL=https://api.sumsub.com
SUMSUB_API_KEY=your_api_key
SUMSUB_API_SECRET=your_api_secret
SUMSUB_LEVEL_NAME=your_level_name

# Application
APP_NAME=KYC Verification API
DEBUG=true
VERSION=1.0.0
```

### 5. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Verify database
python verify_db.py
```

## Running the Application

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Access Points

- **API Docs (Swagger)**: http://localhost:8000/docs
- **API ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### 1. Create Applicant

**POST** `/kyc/create-applicant`

Creates a new applicant in the verification system.

**Request:**
```json
{
  "external_user_id": "user123",
  "email": "user@example.com",
  "phone": "+1234567890",
  "first_name": "John",
  "last_name": "Doe",
  "country": "US"
}
```

**Response:**
```json
{
  "applicant_id": "604a2f6f0001f5d6",
  "external_user_id": "user123",
  "status": "created",
  "steps": [
    {
      "step": "face_liveness",
      "status": "pending"
    }
  ]
}
```

### 2. Get Applicant Status

**GET** `/kyc/applicant/{applicant_id}`

Retrieve current verification status and step details.

**Response:**
```json
{
  "applicant_id": "604a2f6f0001f5d6",
  "external_user_id": "user123",
  "status": "in_progress",
  "steps": [
    {
      "step": "face_liveness",
      "status": "completed",
      "completed_at": "2026-01-15T10:30:00"
    },
    {
      "step": "id_scan",
      "status": "in_progress"
    }
  ]
}
```

### 3. Upload Document

**POST** `/kyc/upload-document`

Upload identity document (ID, passport, etc.) for verification.

**Request:**
```json
{
  "applicant_id": "604a2f6f0001f5d6",
  "document_type": "identity",
  "country": "US",
  "document_data": "base64_encoded_document_image"
}
```

### 4. Upload Liveness Video

**POST** `/kyc/upload-liveness`

Submit face liveness verification video.

**Request:**
```json
{
  "applicant_id": "604a2f6f0001f5d6",
  "video_data": "base64_encoded_video"
}
```

### 5. Upload Selfie

**POST** `/kyc/upload-selfie`

Submit selfie image for verification.

**Request:**
```json
{
  "applicant_id": "604a2f6f0001f5d6",
  "image_data": "base64_encoded_selfie_image"
}
```

### 6. Get Verification Result

**GET** `/kyc/result/{applicant_id}`

Get final verification result and decision.

**Response:**
```json
{
  "applicant_id": "604a2f6f0001f5d6",
  "status": "verified",
  "verification_details": {
    "face_liveness": "completed",
    "id_scan": "completed",
    "selfie": "completed"
  },
  "completed_at": "2026-01-15T11:45:00"
}
```

## Verification Flow

```
1. Create Applicant
   ↓
2. Face Liveness Check (upload video)
   ↓
3. ID/Document Scan (upload document)
   ↓
4. Selfie Upload (upload selfie image)
   ↓
5. Verification Complete
   ↓
6. Get Result (Decision: Approved/Rejected/Manual Review)
```

## Database Models

### Applicant
- `id` - Unique Sumsub applicant ID
- `external_user_id` - Your internal user ID
- `email` - User email
- `first_name`, `last_name` - Personal information
- `country` - Country code
- `status` - Current verification status
- `created_at`, `updated_at` - Timestamps

### VerificationStep
- `applicant_id` - Reference to Applicant
- `step` - Step type (face_liveness, id_scan, etc.)
- `status` - Step status (pending, in_progress, completed, failed)
- `completed_at` - When step was completed
- `error_message` - Error details if failed

### Document
- `applicant_id` - Reference to Applicant
- `document_type` - Type of document
- `file_path` - Storage path
- `uploaded_at` - Upload timestamp

## Error Handling

The API returns standard HTTP status codes:

- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error response format:
```json
{
  "detail": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2026-01-15T10:30:00"
}
```

## Configuration

### settings (config.py)

- `SUMSUB_LEVEL_NAME` - Verification level in Sumsub
- `SUMSUB_BASE_URL` - Sumsub API base URL
- `DATABASE_URL` - PostgreSQL connection string
- `DEBUG` - Debug mode flag

## Testing

```bash
# Run verification
python verify_db.py

# Test API endpoints with curl or Postman
curl http://localhost:8000/health
```

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

## Sumsub Integration

This project integrates with Sumsub's REST API for KYC verification. Key features:

- **Create Applicants** - Register users for verification
- **Liveness Checks** - Video-based face verification
- **Document Upload** - Scan and upload identity documents
- **Verification Decisions** - Automated or manual review decisions

For Sumsub documentation: https://sumsub.com/api-reference/

## Security Considerations

⚠️ **Important:**

1. **API Credentials** - Keep Sumsub API keys secure in environment variables
2. **Database** - Use strong passwords for PostgreSQL
3. **CORS** - Currently allows all origins (change in production)
4. **SSL/TLS** - Enable HTTPS in production
5. **Input Validation** - All inputs are validated with Pydantic

## Production Deployment

For production deployment:

1. Set `DEBUG=false` in environment
2. Use a production WSGI server (Gunicorn, etc.)
3. Enable HTTPS/SSL
4. Restrict CORS origins
5. Use environment-specific database credentials
6. Set up logging and monitoring
7. Enable database connection pooling

Example with Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

## Troubleshooting

### Database Connection Error

```
Make sure PostgreSQL is running and credentials are correct in .env
```

Solution: Check `.env` file and PostgreSQL service status.

### Sumsub API Error

```
Failed to create applicant: 401
```

Solution: Verify API key, secret, and level name in `.env`.

### Port Already in Use

```
Address already in use
```

Solution: Change port in `main.py` or kill process using port 8000.

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

This project is proprietary and confidential.

## Support

For issues and questions:
1. Check the documentation
2. Review error logs
3. Contact the development team

## Changelog

### v1.0.0 (2026-01-15)
- Initial release
- Sumsub integration
- Multi-step verification workflow
- PostgreSQL database support
- FastAPI implementation

---

**Last Updated**: January 15, 2026  
**Status**: Active Development
