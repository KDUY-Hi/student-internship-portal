from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, UploadFile, status

from app.config import get_settings


settings = get_settings()
MAX_CV_SIZE_BYTES = 5 * 1024 * 1024


def validate_cv_file(file: UploadFile) -> None:
    if file.content_type not in {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CV must be a PDF or Word document")

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_CV_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CV file must be 5MB or smaller")


def upload_cv_to_s3(file: UploadFile, user_id: int) -> str:
    key = f"cvs/student-{user_id}/{uuid4()}-{file.filename}"

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

    base_url = settings.s3_public_base_url or f"https://{settings.s3_bucket_name}.s3.{settings.aws_region}.amazonaws.com"
    return f"{base_url.rstrip('/')}/{key}"
