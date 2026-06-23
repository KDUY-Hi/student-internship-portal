from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, UploadFile, status

from app.config import get_settings


settings = get_settings()


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
