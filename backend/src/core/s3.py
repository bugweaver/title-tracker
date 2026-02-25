import logging
from uuid import uuid4

import aioboto3
from botocore.config import Config as BotoConfig

from core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_SCREENSHOTS_PER_ENTRY = 10


class S3Service:
    def __init__(self):
        self._session = aioboto3.Session()
        self._config = settings.s3

    def _get_client_kwargs(self):
        return {
            "service_name": "s3",
            "endpoint_url": self._config.endpoint_url,
            "aws_access_key_id": self._config.access_key,
            "aws_secret_access_key": self._config.secret_key,
            "region_name": self._config.region,
            "config": BotoConfig(signature_version="s3v4"),
        }

    def generate_key(self, user_id: int, extension: str) -> str:
        return f"screenshots/{user_id}/{uuid4().hex}.{extension}"

    async def upload_file(
        self,
        file_content: bytes,
        key: str,
        content_type: str,
    ) -> str:
        async with self._session.client(**self._get_client_kwargs()) as s3:
            try:
                await s3.put_object(
                    Bucket=self._config.bucket_name,
                    Key=key,
                    Body=file_content,
                    ContentType=content_type,
                    ACL="public-read",
                )
            except Exception as e:
                logger.exception("S3 upload failed")
                raise RuntimeError(f"Не удалось загрузить файл в S3: {str(e)}")

        url = f"{self._config.endpoint_url}/{self._config.bucket_name}/{key}"
        logger.info("Uploaded %s -> %s", key, url)
        return url

    async def delete_file(self, key: str) -> None:
        async with self._session.client(**self._get_client_kwargs()) as s3:
            await s3.delete_object(
                Bucket=self._config.bucket_name,
                Key=key,
            )
        logger.info("Deleted %s", key)


s3_service = S3Service()
