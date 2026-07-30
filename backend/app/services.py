import re
from pathlib import PurePath
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, UploadFile, status

from app.config import get_settings


settings = get_settings()
MAX_CV_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_CV_TYPES = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


def sanitize_filename(filename: str | None) -> str:
    base_name = PurePath(filename or "cv").name
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", base_name).strip(".-")
    return safe_name[:120] or "cv"


def validate_cv_file(file: UploadFile) -> None:
    expected_extension = ALLOWED_CV_TYPES.get(file.content_type or "")
    safe_name = sanitize_filename(file.filename)
    if not expected_extension or not safe_name.lower().endswith(expected_extension):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CV must be a PDF or Word document")

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_CV_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CV file must be 5MB or smaller")


def upload_cv_to_s3(file: UploadFile, user_id: int) -> str:
    safe_name = sanitize_filename(file.filename)
    key = f"cvs/student-{user_id}/{uuid4()}-{safe_name}"

    if not settings.s3_bucket_name:
        return f"local://{key}"

    client = boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )
    try:
        client.upload_fileobj(
            file.file,
            settings.s3_bucket_name,
            key,
            ExtraArgs={"ContentType": file.content_type or "application/octet-stream"},
        )
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not upload CV to S3") from exc

    return key


def create_presigned_cv_url(cv_reference: str) -> str:
    if cv_reference.startswith(("local://", "http://", "https://")):
        return cv_reference
    if not settings.s3_bucket_name:
        return f"local://{cv_reference}"

    client = boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )
    try:
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket_name, "Key": cv_reference},
            ExpiresIn=settings.s3_presigned_url_expire_seconds,
        )
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not create CV download URL") from exc
