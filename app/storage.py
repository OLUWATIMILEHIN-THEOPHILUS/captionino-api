# Storage logic here (AWS S3).
import uuid
import boto3
from fastapi import UploadFile
from .config import settings

# AWS setup
AWS_ACCESS_KEY = settings.aws_access_key
AWS_SECRET_KEY = settings.aws_secret_key
AWS_REGION = settings.aws_region
BUCKET_NAME = settings.bucket_name

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

async def upload_temp_image(image: UploadFile):
    ext = image.filename.split(".")[-1]
    image_key = f"temp/{uuid.uuid4()}.{ext}"
    s3_client.upload_fileobj(image.file, BUCKET_NAME, image_key, ExtraArgs={'ACL': 'public-read', 'ContentDisposition': 'inline', "ContentType": image.content_type})
    url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{image_key}"
    return url, image_key

async def move_image_permanently(image_key: str, user_id: str):
    new_key = image_key.replace("temp/", f"users/user_{user_id}/", 1)

    response = s3_client.head_object(Bucket=BUCKET_NAME, Key=image_key)
    content_type = response['ContentType']

    s3_client.copy_object(
        Bucket=BUCKET_NAME,
        CopySource={"Bucket": BUCKET_NAME, "Key": image_key},
        Key=new_key,
        ACL='public-read',
        ContentDisposition='inline',
        ContentType=content_type,
        MetadataDirective='REPLACE'
    )
    s3_client.delete_object(Bucket=BUCKET_NAME, Key=image_key)
    new_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{new_key}"
    return new_url

def delete_image(image_key: str):
    s3_client.delete_object(Bucket=BUCKET_NAME, Key=image_key)
    print(f"Deleted {image_key}")