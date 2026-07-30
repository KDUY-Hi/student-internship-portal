# AWS Deployment Checklist

This checklist prepares the Student Internship Portal for a simple production deployment on AWS.

## Target Architecture

```text
Browser
  -> CloudFront or S3 Static Website Hosting
  -> React frontend
  -> EC2 FastAPI backend
  -> RDS PostgreSQL
  -> S3 bucket for CV files
  -> CloudWatch Logs
```

## 1. Region

Use one AWS region for the first deployment.

Recommended:

```text
ap-southeast-1
```

## 2. RDS PostgreSQL

Create an Amazon RDS PostgreSQL database.

Suggested values:

```text
Engine: PostgreSQL
DB name: internship_portal
Username: app_user
Public access: No, if EC2 is in the same VPC
Storage: 20 GB for demo
Backup: Enabled
```

Security group rule:

```text
Allow inbound PostgreSQL 5432 from the backend EC2 security group
```

Backend variable:

```env
DATABASE_URL=postgresql+psycopg2://app_user:<password>@<rds-endpoint>:5432/internship_portal
```

After configuring the backend environment, run:

```bash
cd backend
alembic upgrade head
python seed.py
```

In production, FastAPI does not auto-create tables at startup. Alembic migration is the required schema setup path.

## 3. S3 Bucket For CV Files

Create a private S3 bucket for uploaded CVs.

Suggested values:

```text
Bucket purpose: CV uploads
Block public access: On for production
Versioning: Optional
Encryption: SSE-S3 or SSE-KMS
```

Keep the bucket private. The backend stores only the S3 object key in the database and creates short-lived presigned URLs when an authorized student or company needs to open a CV.

Backend variables:

```env
AWS_REGION=ap-southeast-1
S3_BUCKET_NAME=<your-cv-bucket>
S3_PRESIGNED_URL_EXPIRE_SECONDS=300
```

## 4. IAM Permission For Backend

Prefer attaching an IAM Role to the EC2 instance instead of storing AWS access keys in `.env`.

Minimum S3 permissions for the CV bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::<your-cv-bucket>/*"
    }
  ]
}
```

## 5. EC2 Backend

Create an EC2 instance for FastAPI.

Suggested values:

```text
OS: Ubuntu LTS
Instance type: t3.micro or t3.small for demo
Security group inbound:
  22 from your IP
  80 from 0.0.0.0/0
  443 from 0.0.0.0/0
  8000 only temporarily for testing, then close it
```

Install runtime:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx
```

Run backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
alembic upgrade head
python seed.py
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For a longer-running deployment, run the backend with a systemd service.

## 6. Frontend Build And S3 Hosting

Set frontend production API URL:

```env
VITE_API_URL=https://your-api-domain.com
```

Build:

```bash
cd frontend
npm install
npm run build
```

Upload:

```bash
aws s3 sync dist/ s3://<your-frontend-bucket> --delete
```

Recommended production path:

```text
S3 frontend bucket -> CloudFront distribution -> HTTPS domain
```

## 7. CORS

Set backend CORS to the final frontend domain only:

```env
BACKEND_CORS_ORIGINS=https://your-frontend-domain.com
BACKEND_CORS_ORIGIN_REGEX=
REFRESH_COOKIE_SECURE=true
REFRESH_COOKIE_SAMESITE=none
```

Production startup now rejects wildcard CORS origins, non-HTTPS frontend origins, and a non-empty CORS regex. Use `SameSite=none` for deployments where the frontend domain and API domain are different origins.

For local testing, keep:

```env
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
BACKEND_CORS_ORIGIN_REGEX=https?://(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?
REFRESH_COOKIE_SAMESITE=lax
```

## 8. Health Checks

Backend health endpoint:

```text
GET /health
```

Expected response:

```json
{
  "status": "ok",
  "service": "Student Internship Portal"
}
```

## 9. CloudWatch Logs

Minimum:

```text
Send backend stdout/stderr logs from EC2 to CloudWatch Logs
Create alarms for high CPU, disk usage, and repeated 5xx responses
```

## 10. Final Demo Flow

Use this flow after deployment:

```text
1. Open frontend domain
2. Login company
3. Create company profile
4. Create internship post
5. Login admin
6. Approve internship post
7. Login student
8. Update student profile
9. Upload CV to S3
10. Apply to approved internship
11. Login company
12. Update application status
13. Confirm student notification
```
