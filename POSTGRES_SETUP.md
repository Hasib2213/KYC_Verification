# PostgreSQL Setup Guide - KYC Verification API

## 📋 Prerequisites

- PostgreSQL 12 or higher installed
- Python 3.8+ installed
- pip package manager

## 🚀 Quick Setup

### 1. Install PostgreSQL

**Windows:**
- Download from https://www.postgresql.org/download/windows/
- Run installer and remember the superuser password
- PostgreSQL default port is 5432

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

### 2. Create Database and User

Open PostgreSQL terminal:

```bash
# Windows - Open pgAdmin or use psql
psql -U postgres

# Or via terminal
psql -U postgres -d postgres
```

Run these SQL commands:

```sql
-- Create new user
CREATE USER kyc_user WITH PASSWORD 'secure_password_123';

-- Create database
CREATE DATABASE kyc_verification OWNER kyc_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE kyc_verification TO kyc_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO kyc_user;

-- Exit
\q
```

### 3. Setup Python Environment

```bash
# Navigate to project directory
cd c:\smt_project\test\KYC_VERIFICATION

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Linux/macOS:
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
# Windows
copy .env.example .env

# Linux/macOS
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# PostgreSQL Configuration
DB_USER=kyc_user
DB_PASSWORD=secure_password_123
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kyc_verification

# Sumsub Configuration
SUMSUB_API_KEY=your_key_here
SUMSUB_API_SECRET=your_secret_here
SUMSUB_WEBHOOK_SECRET=your_webhook_secret
```

### 6. Run the Application

```bash
# The database tables will be created automatically on first run
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## ✅ Verify Installation

Once the app is running, check:

```
http://localhost:8000/docs          # Swagger UI
http://localhost:8000/health        # Health check
http://localhost:8000/api/kyc/health # KYC health check
```

## 📊 Database Tables Created

The application auto-creates these tables:

1. **applicants** - User applicant information
2. **verification_steps** - Step tracking for each applicant
3. **documents** - Document uploads
4. **webhook_events** - Webhook event logs

## 🔧 Troubleshooting

### Connection refused (port 5432)
- PostgreSQL is not running
- Check: `sudo service postgresql status` (Linux) or Services (Windows)

### Authentication failed
- Wrong credentials in `.env`
- Wrong password for PostgreSQL user
- User doesn't exist

### Database does not exist
- Run SQL commands to create database (step 2)
- Verify with: `psql -U kyc_user -d kyc_verification`

### Tables not created
- Check PostgreSQL is running
- Check database connection string is correct
- Check database user has privileges
- See console output for error messages

## 🔐 Production Setup

For production:

1. Use strong passwords
2. Restrict database access (not 0.0.0.0)
3. Use SSL for database connections
4. Enable connection pooling (PgBouncer)
5. Setup automated backups
6. Monitor database performance

Example production connection string:
```
postgresql://kyc_user:secure_password@prod-db.example.com:5432/kyc_verification
```

## 📝 Common Commands

```bash
# Access database
psql -U kyc_user -d kyc_verification

# View tables
\dt

# View table structure
\d applicants

# Drop everything (development only!)
DROP DATABASE kyc_verification;

# Check database size
SELECT pg_database.datname, pg_size_pretty(pg_database.pg_database_size(pg_database.datname))
FROM pg_database
WHERE datname = 'kyc_verification';
```

## 🆘 Need Help?

Check logs in application console for detailed error messages.
